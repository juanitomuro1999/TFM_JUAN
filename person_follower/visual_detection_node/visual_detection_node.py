# Copyright 2026 omixxxer
# Author: omixxxer
# SPDX-License-Identifier: Apache-2.0
#
# Detección visual de persona usando HOG de OpenCV (sin MediaPipe ni cv_bridge).
# Captura directamente desde /dev/video0 en un hilo, publica:
#   /person_detected_visual  → Bool  (fusión con LIDAR en detection_node)
#   /gesture_command         → String ("start_tracking" / "stop_tracking")
#   /camera/status           → String (info de estado)
#
# Fallback automático: si MediaPipe está disponible lo usa; si no, usa HOG.

import threading
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, String

# ── Dependencias opcionales ──────────────────────────────────────────────────
try:
    import cv2
    _CV2_OK = True
except ImportError:
    _CV2_OK = False

try:
    import mediapipe as mp
    _MP_OK = True
except ImportError:
    _MP_OK = False


class VisualDetectionNode(Node):
    """
    Nodo de detección visual.

    Modo HOG  (por defecto): usa el descriptor HOG de OpenCV con el SVM
    preentrenado para personas.  No requiere dependencias externas más allá
    de python3-opencv (ya instalado).

    Modo Pose (si mediapipe está instalado): usa MediaPipe Pose para mayor
    precisión.  Se activa automáticamente si 'use_mediapipe' es True y el
    paquete está disponible.
    """

    def __init__(self):
        super().__init__('visual_detection_node')

        # ── Parámetros ───────────────────────────────────────────────────────
        self.declare_parameter('enabled', True)
        self.declare_parameter('camera_device', 0)          # índice de /dev/videoN
        self.declare_parameter('frame_width',  320)
        self.declare_parameter('frame_height', 240)
        self.declare_parameter('detection_interval', 0.4)   # s entre capturas
        self.declare_parameter('use_mediapipe', True)       # preferir MP si disponible
        # HOG
        self.declare_parameter('hog_win_stride', 8)
        self.declare_parameter('hog_scale',      1.05)
        self.declare_parameter('hog_padding',    8)
        self.declare_parameter('hog_min_weight', 0.35)      # umbral de confianza HOG
        self.declare_parameter('hog_center_crop_ratio', 0.7) # % central del frame a analizar
        # MediaPipe Pose
        self.declare_parameter('pose_model_complexity', 0)  # 0=Lite, 1=Full, 2=Heavy
        self.declare_parameter('pose_min_detection_confidence', 0.5)
        self.declare_parameter('pose_min_tracking_confidence', 0.5)
        self.declare_parameter('pose_min_landmarks', 3)     # mínimo landmarks visibles

        # Carga
        self.enabled           = self.get_parameter('enabled').value
        self.camera_device     = self.get_parameter('camera_device').value
        self.frame_width       = self.get_parameter('frame_width').value
        self.frame_height      = self.get_parameter('frame_height').value
        self.det_interval      = self.get_parameter('detection_interval').value
        self.use_mediapipe     = self.get_parameter('use_mediapipe').value
        self.hog_win_stride    = self.get_parameter('hog_win_stride').value
        self.hog_scale         = self.get_parameter('hog_scale').value
        self.hog_padding       = self.get_parameter('hog_padding').value
        self.hog_min_weight    = self.get_parameter('hog_min_weight').value
        self.hog_crop_ratio    = self.get_parameter('hog_center_crop_ratio').value
        self.pose_complexity   = self.get_parameter('pose_model_complexity').value
        self.pose_min_det      = self.get_parameter('pose_min_detection_confidence').value
        self.pose_min_track    = self.get_parameter('pose_min_tracking_confidence').value
        self.pose_min_lm       = self.get_parameter('pose_min_landmarks').value

        # ── Publicadores comunes (siempre se crean) ──────────────────────────
        self.status_pub = self.create_publisher(String, '/camera/status', 10)
        self.visual_pub = self.create_publisher(Bool,   '/person_detected_visual', 10)
        self.gesture_pub = self.create_publisher(String, '/gesture_command', 10)
        self.shutdown_confirmation_pub = self.create_publisher(Bool, '/shutdown_confirmation', 10)
        self.create_subscription(Bool, '/system_shutdown', self._shutdown_cb, 10)

        if not self.enabled:
            self.get_logger().info("VisualDetectionNode desactivado por parámetro.")
            self._pub_status("Nodo desactivado.")
            return

        if not _CV2_OK:
            self.get_logger().error("python3-opencv no disponible. Nodo desactivado.")
            self._pub_status("Error: sin OpenCV.")
            return

        # ── Seleccionar detector ─────────────────────────────────────────────
        self._use_mp = self.use_mediapipe and _MP_OK
        self._detector_name = "MediaPipe" if self._use_mp else "HOG"
        self.get_logger().info(f"Detector seleccionado: {self._detector_name}")

        if self._use_mp:
            self._init_mediapipe()
        else:
            self._init_hog()

        # ── Hilo de captura ──────────────────────────────────────────────────
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

        self.get_logger().info(
            f"VisualDetectionNode iniciado [{self._detector_name}] "
            f"— /dev/video{self.camera_device} @ {self.frame_width}×{self.frame_height}"
        )
        self._pub_status(f"OK ({self._detector_name})")

    # ── Inicialización de detectores ─────────────────────────────────────────

    def _init_hog(self):
        self._hog = cv2.HOGDescriptor()
        self._hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
        self.get_logger().info(
            f"HOG detector listo (min_weight={self.hog_min_weight}, "
            f"crop={int(self.hog_crop_ratio*100)}% central)"
        )

    def _init_mediapipe(self):
        self._mp_pose = mp.solutions.pose
        self._pose = self._mp_pose.Pose(
            static_image_mode=False,
            model_complexity=self.pose_complexity,
            enable_segmentation=False,
            min_detection_confidence=self.pose_min_det,
            min_tracking_confidence=self.pose_min_track,
        )
        self.get_logger().info(
            f"MediaPipe Pose listo (complexity={self.pose_complexity}, "
            f"min_lm={self.pose_min_lm})"
        )

    # ── Hilo de captura ──────────────────────────────────────────────────────

    def _capture_loop(self):
        cap = cv2.VideoCapture(self.camera_device)
        if not cap.isOpened():
            self.get_logger().error(
                f"No se puede abrir /dev/video{self.camera_device}"
            )
            self._pub_status("Error: cámara inaccesible.")
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # buffer mínimo → frame más reciente

        self.get_logger().info("Captura de cámara iniciada.")

        while not self._stop.is_set() and rclpy.ok():
            t0 = time.time()
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            if self._use_mp:
                detected = self._detect_mp(frame)
            else:
                detected = self._detect_hog(frame)

            self.visual_pub.publish(Bool(data=detected))

            # Throttle
            elapsed = time.time() - t0
            sleep_t = max(0.0, self.det_interval - elapsed)
            time.sleep(sleep_t)

        cap.release()
        self.get_logger().info("Captura de cámara detenida.")

    # ── Detección HOG ────────────────────────────────────────────────────────

    def _detect_hog(self, frame) -> bool:
        """
        Detecta personas en el frame usando HOG.
        Solo analiza la franja central (hog_center_crop_ratio) para
        concentrarse en la dirección de marcha del robot.
        """
        h, w = frame.shape[:2]
        # Crop central
        cx  = int(w * (1.0 - self.hog_crop_ratio) / 2)
        cy  = int(h * (1.0 - self.hog_crop_ratio) / 2)
        cw  = int(w * self.hog_crop_ratio)
        ch  = int(h * self.hog_crop_ratio)
        roi = frame[cy:cy+ch, cx:cx+cw]

        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        rects, weights = self._hog.detectMultiScale(
            gray,
            winStride=(self.hog_win_stride, self.hog_win_stride),
            padding=(self.hog_padding, self.hog_padding),
            scale=self.hog_scale,
        )

        if len(rects) == 0 or len(weights) == 0:
            return False

        max_w = float(weights.flatten().max())
        detected = max_w >= self.hog_min_weight

        if detected:
            self.get_logger().info(
                f"[CAM-HOG] Persona detectada — confianza={max_w:.2f}, "
                f"boxes={len(rects)}"
            )
        return detected

    # ── Detección MediaPipe ──────────────────────────────────────────────────

    def _detect_mp(self, frame) -> bool:
        """
        Detecta persona mediante MediaPipe Pose.
        Retorna True si hay ≥ pose_min_landmarks landmarks visibles.
        """
        import cv2 as _cv2
        rgb = _cv2.cvtColor(frame, _cv2.COLOR_BGR2RGB)
        results = self._pose.process(rgb)
        if not results.pose_landmarks:
            return False

        visible = sum(
            1 for lm in results.pose_landmarks.landmark
            if lm.visibility > 0.5
        )
        detected = visible >= self.pose_min_lm

        if detected:
            self.get_logger().info(
                f"[CAM-MP] Persona detectada — landmarks_visibles={visible}"
            )
        return detected

    # ── Utilidades ───────────────────────────────────────────────────────────

    def _pub_status(self, msg: str):
        self.status_pub.publish(String(data=msg))

    def _shutdown_cb(self, msg):
        if msg.data:
            self.get_logger().info("Shutdown recibido. Cerrando VisualDetectionNode.")
            self._stop.set()
            self.shutdown_confirmation_pub.publish(Bool(data=True))
            self.destroy_node()


# ── Punto de entrada ─────────────────────────────────────────────────────────

def main(args=None):
    rclpy.init(args=args)
    node = VisualDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("VisualDetectionNode detenido manualmente.")
    finally:
        if hasattr(node, '_stop'):
            node._stop.set()
        node.destroy_node()


if __name__ == '__main__':
    main()
