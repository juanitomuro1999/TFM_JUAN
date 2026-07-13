# Copyright 2026 omixxxer
# Author: omixxxer
# SPDX-License-Identifier: Apache-2.0

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, Float32, Float32MultiArray, String
from geometry_msgs.msg import Point
import numpy as np
from scipy.spatial import cKDTree
from scipy import ndimage
import math
import time


def dbscan_labels(points, eps, min_samples):
    """DBSCAN auto-contenido (sin sklearn) sobre puntos 2D.

    Devuelve un array de etiquetas de clúster (-1 = ruido), con la misma
    semántica que sklearn.cluster.DBSCAN: un punto es 'core' si tiene
    >= min_samples vecinos dentro de eps (incluyéndose a sí mismo).

    Se usa scipy.spatial.cKDTree para la consulta de vecindad (el NUC no
    tiene una build válida de scikit-learn para Python 3.12; numpy y scipy
    sí funcionan). Para los ~cientos de puntos de un scan filtrado el coste
    es despreciable.
    """
    n = len(points)
    labels = np.full(n, -1, dtype=int)
    if n == 0:
        return labels
    tree = cKDTree(points)
    neighbors = tree.query_ball_point(points, r=eps)  # incluye el propio punto
    visited = np.zeros(n, dtype=bool)
    cluster_id = -1
    for i in range(n):
        if visited[i]:
            continue
        visited[i] = True
        if len(neighbors[i]) < min_samples:
            continue  # de momento ruido (puede pasar a borde más adelante)
        cluster_id += 1
        labels[i] = cluster_id
        seeds = list(neighbors[i])
        k = 0
        while k < len(seeds):
            j = seeds[k]
            k += 1
            if not visited[j]:
                visited[j] = True
                if len(neighbors[j]) >= min_samples:
                    seeds.extend(neighbors[j])
            if labels[j] == -1:
                labels[j] = cluster_id
    return labels

class DetectionNode(Node):
    def __init__(self):
        super().__init__('detection_node')
        
        # Parámetros configurables
        self.declare_parameter('enabled', True)
        self.declare_parameter('camera_timeout', 1.0)               # segundos antes de invalidar detección visual
        self.declare_parameter('camera_debounce_count', 2)         # detecciones visuales consecutivas mínimas
        # Parámetros LIDAR y clustering
        self.declare_parameter('max_detection_distance', 6.0)
        self.declare_parameter('min_detection_distance', 0.1)
        self.declare_parameter('dbscan_eps', 0.1)
        self.declare_parameter('dbscan_min_samples', 4)
        self.declare_parameter('min_leg_cluster_size', 4)
        self.declare_parameter('max_leg_cluster_size', 200)
        self.declare_parameter('min_leg_radius', 0.01)
        self.declare_parameter('max_leg_radius', 0.15)
        self.declare_parameter('min_leg_distance', 0.04)
        self.declare_parameter('max_leg_distance', 0.35)
        self.declare_parameter('median_filter_window', 7)
        # ── Fusión cámara+LIDAR (fallback cuando no hay par de piernas) ──────
        self.declare_parameter('fusion_enabled', True)
        self.declare_parameter('fusion_angle_tol_deg', 25.0)   # tolerancia angular cluster vs rumbo cámara
        self.declare_parameter('fusion_max_distance', 4.0)     # alcance máx. para el fallback (m)
        self.declare_parameter('bearing_sign', -1.0)           # signo cámara→láser (calibrar en vivo)
        self.declare_parameter('bearing_timeout', 1.5)         # validez del último rumbo (s)
        # ── Filtro de continuidad (anti-salto) ───────────────────────────────
        self.declare_parameter('max_person_speed', 2.0)        # m/s — cota física de velocidad humana
        self.declare_parameter('position_jump_margin', 0.3)    # m — margen extra sobre max_person_speed*dt
        self.declare_parameter('continuity_confirm_frames', 1)  # scans seguidos de salto implausible antes de aceptarlo (1 = sin espera, comportamiento anterior)
        self.declare_parameter('continuity_window_s', 1.0)      # ventana (s) para limitar la deriva acumulada, no solo el salto frame a frame

        # Carga de parámetros
        self.enabled = self.get_parameter('enabled').value
        self.camera_timeout = self.get_parameter('camera_timeout').value
        self.camera_debounce_count = int(self.get_parameter('camera_debounce_count').value)
        self.max_detection_distance = self.get_parameter('max_detection_distance').value
        self.min_detection_distance = self.get_parameter('min_detection_distance').value
        self.dbscan_eps = self.get_parameter('dbscan_eps').value
        self.dbscan_min_samples = self.get_parameter('dbscan_min_samples').value
        self.min_leg_cluster_size = self.get_parameter('min_leg_cluster_size').value
        self.max_leg_cluster_size = self.get_parameter('max_leg_cluster_size').value
        self.min_leg_radius = self.get_parameter('min_leg_radius').value
        self.max_leg_radius = self.get_parameter('max_leg_radius').value
        self.min_leg_distance = self.get_parameter('min_leg_distance').value
        self.max_leg_distance = self.get_parameter('max_leg_distance').value
        self.median_filter_window = self.get_parameter('median_filter_window').value
        self.fusion_enabled = self.get_parameter('fusion_enabled').value
        self.fusion_angle_tol = math.radians(self.get_parameter('fusion_angle_tol_deg').value)
        self.fusion_max_distance = self.get_parameter('fusion_max_distance').value
        self.bearing_sign = self.get_parameter('bearing_sign').value
        self.bearing_timeout = self.get_parameter('bearing_timeout').value
        self.max_person_speed = self.get_parameter('max_person_speed').value
        self.position_jump_margin = self.get_parameter('position_jump_margin').value
        self.continuity_confirm_frames = int(self.get_parameter('continuity_confirm_frames').value)
        self.continuity_window_s = float(self.get_parameter('continuity_window_s').value)

        if not self.enabled:
            self.get_logger().info("Nodo de Detección desactivado.")
            self.publish_status("Nodo desactivado.")
            return

        # Publicadores y suscriptores
        self.status_publisher = self.create_publisher(String, '/detection/status', 10)
        self.detection_publisher = self.create_publisher(Bool, '/person_detected', 10)
        self.scan_subscription = self.create_subscription(LaserScan, '/scan', self.lidar_callback, 10)
        self.create_subscription(Bool, '/person_detected_visual', self.visual_detected_callback, 10)
        self.create_subscription(Float32, '/person_bearing', self.bearing_callback, 10)
        self.cluster_publisher = self.create_publisher(Float32MultiArray, '/detection/clusters', 10)
        self.general_cluster_publisher = self.create_publisher(Float32MultiArray, '/clusters/general', 10)
        self.leg_cluster_publisher = self.create_publisher(Float32MultiArray, '/clusters/legs', 10)
        self.person_position_publisher = self.create_publisher(Point, '/person_position', 10)

        # Estado de detección visual
        self.visual_detected = False
        self.visual_count = 0
        self.last_visual_time = self.get_clock().now()

        # Estado del rumbo de cámara (para fusión)
        self._bearing = None                       # rad, frame cámara
        self._bearing_time = self.get_clock().now()

        # ── Filtro de persistencia temporal ──────────────────────────────
        # Un objeto debe detectarse N scans consecutivos para ser considerado persona.
        # Evita falsos positivos por objetos estáticos (sillas, patas de mesa).
        self.declare_parameter('detection_confirm_frames', 3)   # scans consecutivos requeridos
        self.declare_parameter('detection_loss_frames',    4)   # scans fallidos para perder
        self._confirm_frames = self.get_parameter('detection_confirm_frames').value
        self._loss_frames    = self.get_parameter('detection_loss_frames').value
        self._detect_streak  = 0   # scans consecutivos con detección
        self._loss_streak    = 0   # scans consecutivos sin detección
        self._confirmed      = False   # persona "confirmada" (supera umbral)
        self._last_confirmed_pos: tuple | None = None  # última posición publicada (gating de continuidad)
        self._last_position_time = None
        self._continuity_reject_streak = 0  # scans consecutivos de salto implausible sin confirmar
        self._pending_reanchor: np.ndarray | None = None  # candidato implausible en seguimiento de consistencia
        self._position_history: list = []  # [(t_seg, np.array[x,y])] confirmadas, últimos continuity_window_s

        self.publish_status("Nodo OK.")
        self.initialize_shutdown_listener()

    def publish_status(self, message):
        self.status_publisher.publish(String(data=message))

    def log_info(self, message, data=None):
        if data is not None:
            self.get_logger().info(f"{message} | {data}")
        else:
            self.get_logger().debug(message)

    def lidar_callback(self, msg):
        # Filtro de mediana
        ranges_filtered = self.apply_median_filter(msg.ranges, self.median_filter_window)

        # Interpolación para mayor resolución
        interpolated_ranges, interpolated_angles = self.interpolate_lidar_points(
            ranges_filtered, msg.angle_min, msg.angle_max, msg.angle_increment, factor=2
        )

        # Detección con LIDAR
        person_detected = self.detect_person(
            interpolated_ranges,
            interpolated_angles[0],
            interpolated_angles[1] - interpolated_angles[0]
        )

        # ── Fusión LIDAR + cámara ─────────────────────────────────────────
        elapsed = (self.get_clock().now() - self.last_visual_time).nanoseconds * 1e-9
        visual_valid = (elapsed < self.camera_timeout) and (self.visual_count >= self.camera_debounce_count)
        raw_detection = person_detected or visual_valid

        # ── Filtro de persistencia temporal ──────────────────────────────
        # Requiere N detecciones consecutivas para "confirmar" y
        # M pérdidas consecutivas para "perder" → elimina falsas sillas/patas.
        if raw_detection:
            self._detect_streak += 1
            self._loss_streak    = 0
            if self._detect_streak >= self._confirm_frames:
                self._confirmed = True
        else:
            self._loss_streak   += 1
            self._detect_streak  = 0
            if self._loss_streak >= self._loss_frames:
                self._confirmed = False
                self._last_confirmed_pos = None  # pérdida larga: ya no ancla el gating de continuidad
                self._continuity_reject_streak = 0  # streak obsoleto tras perder el anclaje
                self._pending_reanchor = None
                self._position_history = []  # ventana de deriva obsoleta tras perder el anclaje

        final_detection = self._confirmed

        self.detection_publisher.publish(Bool(data=final_detection))
        if final_detection:
            self.log_info("Persona detectada (fusion LIDAR+cam)",
                          {'lidar': person_detected, 'cam': visual_valid,
                           'streak': self._detect_streak})

    def initialize_shutdown_listener(self):
        self.create_subscription(Bool, '/system_shutdown', self.shutdown_callback, 10)
        self.shutdown_confirmation_publisher = self.create_publisher(Bool, '/shutdown_confirmation', 10)

    def shutdown_callback(self, msg):
        if msg.data:
            self.get_logger().info("Cierre del sistema detectado. Enviando confirmación.")
            try:
                self.shutdown_confirmation_publisher.publish(Bool(data=True))
            except Exception as e:
                self.get_logger().error(f"Error al publicar confirmación de apagado: {e}")
            self.destroy_node()

    def visual_detected_callback(self, msg):
        # Debounce: contar detecciones consecutivas
        if msg.data:
            self.visual_count += 1
        else:
            self.visual_count = 0
        if msg.data:
            self.last_visual_time = self.get_clock().now()

    def bearing_callback(self, msg):
        self._bearing = float(msg.data)
        self._bearing_time = self.get_clock().now()

    def apply_median_filter(self, data, window_size):
        # Filtro de mediana vectorizado con scipy (antes: bucle Python con
        # una llamada a np.median por punto, ~56ms/scan en el NUC — 70% del
        # presupuesto de tiempo disponible entre scans a 11Hz, ver
        # docs/decisiones.md 2026-07-13). scipy.ndimage usa mode='nearest'
        # (replica el valor extremo) en los bordes, distinto de la ventana
        # recortada del original — se recalculan esos puntos exactamente
        # igual que antes para no cambiar el comportamiento.
        data = np.asarray(data, dtype=float)
        n = len(data)
        half = window_size // 2
        filtered = ndimage.median_filter(data, size=2 * half + 1, mode='nearest')
        edge_idx = set(range(min(half, n))) | set(range(max(n - half, 0), n))
        for i in edge_idx:
            start = max(0, i - half)
            end = min(n, i + half + 1)
            filtered[i] = np.median(data[start:end])
        return filtered

    def interpolate_lidar_points(self, ranges, angle_min, angle_max, angle_increment, factor=2):
        n_orig = len(ranges)
        original_angles = np.linspace(angle_min, angle_min + angle_increment * n_orig, n_orig, endpoint=False)
        interpolated_angles = np.linspace(angle_min, angle_max, n_orig * factor)
        interpolated_ranges = np.interp(interpolated_angles, original_angles, ranges)
        return interpolated_ranges, interpolated_angles

    def _gate_by_continuity(self, positions, now):
        """
        Filtra `positions` (lista de np.array [x,y]) descartando las que
        impliquen una velocidad mayor que max_person_speed respecto a la
        última posición publicada. Sin filtro, un cluster espurio (p.ej.
        patas de silla) más cercano al robot que la persona real puede ganar
        la selección por proximidad y producir saltos de varios metros entre
        frames consecutivos.

        Devuelve `positions` sin filtrar si no hay ancla reciente (arranque o
        tras una pérdida larga) — así no se bloquea la reasignación cuando la
        persona reaparece en otro punto.

        Si hay ancla pero ningún candidato es plausible, exige
        `continuity_confirm_frames` scans consecutivos con un candidato
        *consistente* (repitiéndose en aprox. el mismo punto, tolerancia
        `position_jump_margin`) antes de aceptar el reanclaje. No basta con
        que haya "algo implausible" N veces seguidas: un cluster espurio
        (ruido, pata de silla) no suele repetirse en el mismo sitio de un
        scan al siguiente, mientras que una reaparición real de la persona
        sí. Si el candidato más cercano cambia de sitio entre scans, la
        cuenta se reinicia. Mientras no se confirma, devuelve `[]` (ningún
        candidato válido este scan) en vez de reanclar de inmediato. Con
        `continuity_confirm_frames=1` (valor por defecto) el comportamiento
        es idéntico al anterior: acepta el salto en el primer scan.

        Además del salto respecto al frame inmediatamente anterior, se limita
        la deriva acumulada respecto a la posición confirmada más antigua
        dentro de `continuity_window_s` segundos. Sin esto, una cadena de
        clústeres espurios (p.ej. las patas de una silla cercana) separados
        poco más que `position_jump_margin` entre sí puede "caminar" de uno a
        otro frame a frame — cada salto individual parece plausible, pero la
        suma en 1-2s traza un barrido de varios metros alrededor del robot
        (visto en vivo el 2026-07-09, sesión de gesto real: PROGRESO.md).
        """
        if self._last_confirmed_pos is None or self._last_position_time is None:
            return positions

        # Deriva acumulada: filtro previo, duro, independiente del mecanismo
        # de confirmación por consistencia de abajo (ese mecanismo no sirve
        # aquí — una cadena de clústeres espurios consecutivos es, por
        # definición, "consistente" frame a frame, así que confirmarla no la
        # distingue de una reaparición real). Si ningún candidato respeta la
        # deriva máxima desde la posición confirmada más antigua dentro de
        # `continuity_window_s`, se descartan todos sin más antes de mirar el
        # salto frame a frame.
        now_s = now.nanoseconds * 1e-9
        self._position_history = [(t, p) for t, p in self._position_history
                                   if now_s - t <= self.continuity_window_s]
        if self._position_history:
            window_t, window_ref = self._position_history[0]
            window_elapsed = now_s - window_t
            max_window_jump = self.max_person_speed * max(window_elapsed, 0.0) + self.position_jump_margin
            positions = [p for p in positions
                         if np.linalg.norm(p - window_ref) <= max_window_jump]
            if not positions:
                return []

        elapsed = (now - self._last_position_time).nanoseconds * 1e-9
        max_jump = self.max_person_speed * max(elapsed, 0.0) + self.position_jump_margin
        last = np.array(self._last_confirmed_pos)
        plausible = [p for p in positions if np.linalg.norm(p - last) <= max_jump]
        if plausible:
            self._continuity_reject_streak = 0
            self._pending_reanchor = None
            return plausible
        if not positions:
            return []

        nearest = min(positions, key=lambda p: np.linalg.norm(p - last))
        if self._pending_reanchor is not None and \
                np.linalg.norm(nearest - self._pending_reanchor) <= self.position_jump_margin:
            self._continuity_reject_streak += 1
        else:
            self._continuity_reject_streak = 1
        self._pending_reanchor = nearest

        if self._continuity_reject_streak >= self.continuity_confirm_frames:
            self._continuity_reject_streak = 0
            self._pending_reanchor = None
            return positions
        return []

    def _publish_person_position(self, xy, now, log_msg, log_data):
        # Convenio de salida de /person_position: "delante del robot" = +x
        # (convenio estandar que asume tracking_node). Internamente (gating,
        # _position_history, fallback de fusion) se sigue trabajando en el
        # frame bruto del laser de este robot, donde delante es approx pi
        # (ver comentario en el fallback de fusion, mas abajo) -- confirmado
        # en vivo 2026-07-13: persona delante a 1m publicaba x=-1.18. Antes
        # de este fix tracking_node.angle_to=atan2(py,px) trataba x positivo
        # como "delante" sin aplicar ese desfase, dejando el error angular
        # pegado a +-180 grados sin converger nunca (ver docs/decisiones.md).
        # Se invierte el signo solo aqui, en la frontera de publicacion --
        # el resto de este fichero sigue usando xy tal cual (frame bruto).
        pt = Point(x=float(-xy[0]), y=float(-xy[1]), z=0.0)
        self.person_position_publisher.publish(pt)
        self.log_info(log_msg, log_data)
        self._last_confirmed_pos = (float(xy[0]), float(xy[1]))
        self._last_position_time = now
        self._position_history.append((now.nanoseconds * 1e-9, np.array(xy, dtype=float)))

    def detect_person(self, ranges, angle_min, angle_increment):
        # Alcance efectivo: para el fallback de fusión necesitamos clústeres
        # más allá de max_detection_distance, así que ampliamos el filtro de
        # puntos. El emparejamiento de piernas sigue acotado a max_detection_distance.
        effective_max = max(self.max_detection_distance, self.fusion_max_distance) \
            if self.fusion_enabled else self.max_detection_distance
        points = [
            (r * np.cos(angle_min + i * angle_increment),
             r * np.sin(angle_min + i * angle_increment))
            for i, r in enumerate(ranges)
            if self.min_detection_distance < r < effective_max
        ]
        if not points:
            self.log_info("No se detectaron puntos")
            return False

        points = np.array(points)
        labels = dbscan_labels(points, self.dbscan_eps, self.dbscan_min_samples)
        clusters = [points[labels == lbl] for lbl in set(labels) if lbl != -1]

        _, leg_clusters = self.detect_leg_clusters(clusters)
        self.publish_general_clusters(points, labels)
        if leg_clusters:
            all_leg_points = np.concatenate(leg_clusters)
            self.publish_leg_clusters(all_leg_points)

        candidate_positions = []
        used = set()
        for i, ci in enumerate(leg_clusters):
            if i in used: continue
            ci_center = np.mean(ci, axis=0)
            closest, min_dist = None, float('inf')
            for j, cj in enumerate(leg_clusters):
                if i == j or j in used: continue
                cj_center = np.mean(cj, axis=0)
                d = np.linalg.norm(ci_center - cj_center)
                if self.min_leg_distance < d < self.max_leg_distance and d < min_dist:
                    closest, min_dist = j, d
            if closest is not None:
                used.update({i, closest})
                combo = np.vstack((ci, leg_clusters[closest]))
                candidate_positions.append(np.mean(combo, axis=0))

        candidate_positions = [p for p in candidate_positions
                               if np.linalg.norm(p) <= self.max_detection_distance]
        if candidate_positions:
            now = self.get_clock().now()
            gated = self._gate_by_continuity(candidate_positions, now)
            if not gated:
                # Todos los candidatos de piernas implican un salto implausible
                # respecto al último anclaje y aún no está confirmado (ver
                # _gate_by_continuity) — se trata este scan como "sin detección"
                # en vez de reanclar de inmediato a un cluster posiblemente espurio.
                self.log_info("Candidatos de piernas descartados por el gate de continuidad (sin confirmar)")
                return False
            last = np.array(self._last_confirmed_pos) if self._last_confirmed_pos is not None else None
            key = (lambda p: np.linalg.norm(p - last)) if last is not None else (lambda p: np.linalg.norm(p))
            selected = min(gated, key=key)
            self._publish_person_position(
                selected, now, "Posición de persona publicada",
                {"x_laser": selected[0], "y_laser": selected[1]})
            return True

        # ── Fallback de fusión cámara+LIDAR ──────────────────────────────────
        # Si el LIDAR no encontró un par de piernas válido (persona quieta,
        # piernas juntas, lejos…) pero la cámara da un rumbo reciente, elegimos
        # el clúster general cuyo ángulo coincide mejor con ese rumbo y
        # publicamos su centroide como /person_position. Da posición aunque no
        # se distingan dos piernas.
        if self.fusion_enabled and self._bearing is not None:
            age = (self.get_clock().now() - self._bearing_time).nanoseconds * 1e-9
            if age <= self.bearing_timeout and len(clusters) > 0:
                # Rumbo cámara → ángulo esperado en el frame del láser.
                # Persona de frente ≈ π en el láser (TF base→laser con yaw=π).
                theta_target = math.atan2(
                    math.sin(math.pi + self.bearing_sign * self._bearing),
                    math.cos(math.pi + self.bearing_sign * self._bearing),
                )
                now = self.get_clock().now()
                centroids = [np.mean(cl, axis=0) for cl in clusters]
                in_range = [c for c in centroids
                            if self.min_detection_distance
                               < float(np.linalg.norm(c))
                               <= self.fusion_max_distance]
                gated = self._gate_by_continuity(in_range, now)

                best, best_dev = None, float('inf')
                for c in gated:
                    theta_c = math.atan2(c[1], c[0])
                    dev = abs(math.atan2(math.sin(theta_c - theta_target),
                                         math.cos(theta_c - theta_target)))
                    if dev < best_dev:
                        best, best_dev = c, dev
                if best is not None and best_dev <= self.fusion_angle_tol:
                    self._publish_person_position(
                        best, now, "Posición de persona publicada (FUSION cam+LIDAR)",
                        {"x_laser": round(float(best[0]), 3), "y_laser": round(float(best[1]), 3),
                         "beta_deg": round(math.degrees(self._bearing), 1),
                         "theta_tgt_deg": round(math.degrees(theta_target), 1),
                         "dev_deg": round(math.degrees(best_dev), 1),
                         "dist": round(float(np.linalg.norm(best)), 2)})
                    return True

        self.log_info("No se encontraron pares de piernas válidos")
        return False

    def _cluster_features(self, cl: np.ndarray) -> dict:
        """
        Extrae features geométricas de un clúster.
        Inspirado en ros2_leg_detector (mowito) y leg_detector (ROS 1 Spencer).

        Features:
          size        — número de puntos
          radius      — radio medio (dist. al centroide)
          width       — ancho de la bounding box
          height      — alto  de la bounding box
          aspect      — ratio ancho/alto (1.0 = cuadrado)
          circularity — 4π·área / perímetro² (1.0 = círculo perfecto)
          compactness — perímetro² / área
          scatter     — desviación estándar de radios (uniformidad)
        """
        centroid = np.mean(cl, axis=0)
        radii    = np.linalg.norm(cl - centroid, axis=1)
        xmin, ymin = cl.min(axis=0)
        xmax, ymax = cl.max(axis=0)
        w = xmax - xmin
        h = ymax - ymin

        # Área y perímetro aproximados por bounding box
        area      = max(w * h, 1e-6)
        perimeter = 2 * (w + h) if (w + h) > 0 else 1e-6
        circularity = (4 * np.pi * area) / (perimeter ** 2)

        return {
            "size":        len(cl),
            "radius":      float(radii.mean()),
            "scatter":     float(radii.std()),
            "width":       float(w),
            "height":      float(h),
            "aspect":      float(w / h) if h > 1e-4 else 99.0,
            "circularity": float(circularity),
            "compactness": float(perimeter ** 2 / area),
        }

    def _is_leg_cluster(self, cl: np.ndarray) -> bool:
        """
        Clasificador geométrico multi-feature para detectar clústeres de pierna.
        Combina los filtros del código original con features adicionales de
        ros2_leg_detector para reducir falsos positivos/negativos.
        """
        f = self._cluster_features(cl)

        # 1. Tamaño del clúster
        if not (self.min_leg_cluster_size <= f["size"] <= self.max_leg_cluster_size):
            return False

        # 2. Radio medio (ajustado con max_leg_radius ampliado en config)
        if not (self.min_leg_radius <= f["radius"] <= self.max_leg_radius):
            return False

        # 3. Forma no demasiado elongada (pierna ≈ circular en planta)
        if f["aspect"] > 4.5 or f["aspect"] < 0.22:
            return False

        # 4. No demasiado grande en ninguna dimensión
        #    (pierna: diámetro ~0.08–0.15m → width/height < 0.25m)
        if f["width"] > 0.30 or f["height"] > 0.30:
            return False

        # 5. Circularity: una pierna debería ser razonablemente compacta
        #    (pared/esquina tiene circularity muy baja)
        if f["circularity"] < 0.15:
            return False

        # 6. Scatter bajo → puntos concentrados (no ruido disperso)
        if f["scatter"] > self.max_leg_radius * 0.8:
            return False

        return True

    def detect_leg_clusters(self, clusters):
        leg_clusters, all_clusters = [], []
        for cl in clusters:
            all_clusters.append(cl)
            if self._is_leg_cluster(cl):
                leg_clusters.append(cl)
        return all_clusters, leg_clusters

    def publish_general_clusters(self, points, labels):
        msg = Float32MultiArray()
        for lbl in set(labels):
            if lbl == -1: continue
            for x, y in points[labels == lbl]: msg.data.extend([x, y])
        self.general_cluster_publisher.publish(msg)

    def publish_leg_clusters(self, points):
        msg = Float32MultiArray()
        for x, y in points: msg.data.extend([x, y])
        self.leg_cluster_publisher.publish(msg)


def main(args=None):
    rclpy.init()
    node = DetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("DetectionNode detenido con Ctrl-C.")
    finally:
        node.destroy_node()

