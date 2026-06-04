# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# tracking_node.py — v3
#   • Kalman 9-estados: [x, y, vx, vy, ax, ay] + yaw + ω + dist
#     → mejor predicción en oclusiones (inspirado en LiDAR_Human_Tracker_ROS2)
#   • Controlador PD angular (Kp + Kd)
#   • Rampa de velocidad adaptativa con exponente configurable
#   • Validación de innovación por distancia de Mahalanobis (rechaza outliers)
#   • Telemetría JSON completa en /follower/telemetry

import math
import time
import json

import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Point
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String
from std_srvs.srv import SetBool

# ── Constante: chi² 95% para 2 DOF (gate de Mahalanobis) ─────────────────────
MAHAL_GATE = 5.991


class KalmanTracker:
    """
    Filtro de Kalman de 6 estados para seguimiento 2D:
      estado x = [px, py, vx, vy, ax, ay]

    Inspirado en la implementación de 9 estados de LiDAR_Human_Tracker_ROS2.
    Aquí simplificamos a 6 estados (sin yaw/omega) porque RPLIDAR 2D no
    proporciona orientación directa del objetivo.

    La matriz de transición F(dt) incorpora aceleración constante (CA model):
      px_k+1 = px_k + vx·dt + ½·ax·dt²
      vx_k+1 = vx_k + ax·dt
      ax_k+1 = ax_k    (aceleración aproximadamente constante)
    """
    DIM = 6   # estados: px, py, vx, vy, ax, ay
    OBS = 2   # observaciones: px, py

    def __init__(self, q: float = 0.02, r: float = 0.04):
        self.x = np.zeros(self.DIM)
        self.P = np.eye(self.DIM) * 0.5

        # Modelo de observación H: solo posición
        self.H = np.zeros((self.OBS, self.DIM))
        self.H[0, 0] = 1.0   # px
        self.H[1, 1] = 1.0   # py

        self.R = np.eye(self.OBS) * r
        self._q = q
        self._last_t: float | None = None
        self.initialized = False

    def _build_F_Q(self, dt: float):
        """Matrices F y Q para modelo de aceleración constante."""
        dt2 = 0.5 * dt * dt
        dt3 = dt2 * dt / 3.0

        F = np.eye(self.DIM)
        # px
        F[0, 2] = dt;  F[0, 4] = dt2
        # py
        F[1, 3] = dt;  F[1, 5] = dt2
        # vx
        F[2, 4] = dt
        # vy
        F[3, 5] = dt

        # Ruido de proceso: bloques correlacionados por dt
        q = self._q
        Q = np.zeros((self.DIM, self.DIM))
        # Posición-posición
        Q[0, 0] = q * dt3;  Q[1, 1] = q * dt3
        # Posición-velocidad (covarianza cruzada)
        Q[0, 2] = q * dt2;  Q[2, 0] = q * dt2
        Q[1, 3] = q * dt2;  Q[3, 1] = q * dt2
        # Velocidad-velocidad
        Q[2, 2] = q * dt;   Q[3, 3] = q * dt
        # Aceleración (menor ruido: más suave)
        Q[4, 4] = q * 0.2 * dt
        Q[5, 5] = q * 0.2 * dt

        return F, Q

    def init(self, px: float, py: float):
        self.x[:] = 0.0
        self.x[0] = px
        self.x[1] = py
        self.P = np.eye(self.DIM) * 0.5
        self._last_t = time.monotonic()
        self.initialized = True

    def update(self, px: float, py: float) -> tuple[float, float]:
        """
        Actualiza con nueva observación.
        Retorna la posición filtrada (x, y).
        Aplica gate de Mahalanobis para rechazar outliers.
        """
        now = time.monotonic()
        dt  = (now - self._last_t) if self._last_t is not None else 0.1
        dt  = max(0.01, min(dt, 0.5))
        self._last_t = now

        if not self.initialized:
            self.init(px, py)
            return px, py

        F, Q = self._build_F_Q(dt)

        # — Predicción —
        x_pred = F @ self.x
        P_pred = F @ self.P @ F.T + Q

        # — Innovación y gate de Mahalanobis —
        z   = np.array([px, py])
        inn = z - self.H @ x_pred
        S   = self.H @ P_pred @ self.H.T + self.R
        S_inv = np.linalg.inv(S)

        mah2 = float(inn @ S_inv @ inn)
        if mah2 > MAHAL_GATE * 4:
            # Observación muy alejada: re-inicializar suavemente
            self.init(px, py)
            return px, py

        # — Corrección (forma de Joseph para estabilidad numérica) —
        K = P_pred @ self.H.T @ S_inv
        self.x = x_pred + K @ inn
        I_KH  = np.eye(self.DIM) - K @ self.H
        self.P = I_KH @ P_pred @ I_KH.T + K @ self.R @ K.T

        return float(self.x[0]), float(self.x[1])

    def predict_position(self, dt: float = 0.1) -> tuple[float, float]:
        """Predicción de posición a dt segundos en el futuro."""
        F, _ = self._build_F_Q(dt)
        x_p  = F @ self.x
        return float(x_p[0]), float(x_p[1])

    @property
    def velocity(self) -> tuple[float, float]:
        return float(self.x[2]), float(self.x[3])

    @property
    def acceleration(self) -> tuple[float, float]:
        return float(self.x[4]), float(self.x[5])


class TrackingNode(Node):
    def __init__(self):
        super().__init__('tracking_node')

        # ── Parámetros ────────────────────────────────────────────────────
        self.declare_parameter('enabled',                   True)
        self.declare_parameter('obstacle_avoidance_enabled', True)
        self.declare_parameter('max_speed',                 0.4)
        self.declare_parameter('target_distance',           0.4)
        self.declare_parameter('acc_limit',                 0.05)
        self.declare_parameter('angular_gain',              2.0)
        self.declare_parameter('angular_d_gain',            0.3)
        self.declare_parameter('vel_ramp_exp',              1.5)
        self.declare_parameter('kalman_q',                  0.02)
        self.declare_parameter('kalman_r',                  0.04)
        self.declare_parameter('obstacle_threshold',         0.55)

        self.enabled = self.get_parameter('enabled').value
        if not self.enabled:
            self.get_logger().info("TrackingNode desactivado.")
            self.status_pub = self.create_publisher(String, '/tracking/status', 10)
            self.status_pub.publish(String(data="Nodo desactivado."))
            return

        self.obs_avoidance = self.get_parameter('obstacle_avoidance_enabled').value
        self.max_speed      = self.get_parameter('max_speed').value
        self.target_dist    = self.get_parameter('target_distance').value
        self.acc_limit      = self.get_parameter('acc_limit').value
        self.ang_kp         = self.get_parameter('angular_gain').value
        self.ang_kd         = self.get_parameter('angular_d_gain').value
        self.vel_ramp_exp   = self.get_parameter('vel_ramp_exp').value
        kq                  = self.get_parameter('kalman_q').value
        kr                  = self.get_parameter('kalman_r').value
        self.obs_threshold  = self.get_parameter('obstacle_threshold').value

        # ── Kalman 6 estados ──────────────────────────────────────────────
        self.kf = KalmanTracker(q=kq, r=kr)

        # ── Estado ───────────────────────────────────────────────────────
        self.tracking_enabled      = False
        self.person_detected       = False
        self.person_pos: Point | None = None
        self.last_obs_t: float | None = None
        self.timeout_s             = 2.0

        self.prev_vx    = 0.0
        self.prev_angle = 0.0

        # ── Publishers ───────────────────────────────────────────────────
        self.vel_pub    = self.create_publisher(Twist,  '/tracking/velocity_cmd',    10)
        self.pos_pub    = self.create_publisher(Point,  '/expected_person_position', 10)
        self.status_pub = self.create_publisher(String, '/tracking/status',          10)
        self.telem_pub  = self.create_publisher(String, '/follower/telemetry',       10)

        # ── Subscribers ──────────────────────────────────────────────────
        self.create_subscription(Point,     '/person_position', self._on_position, 10)
        self.create_subscription(Bool,      '/person_detected', self._on_detected,  10)
        self.create_subscription(LaserScan, '/scan',            self._on_scan,      10)
        self.create_subscription(Bool,      '/system_shutdown', self._on_shutdown,  10)

        # ── Service ──────────────────────────────────────────────────────
        self.create_service(SetBool, 'enable_tracking', self._on_enable)
        self._shutdown_pub = self.create_publisher(Bool, '/shutdown_confirmation', 10)

        self.status_pub.publish(String(data="Nodo OK (v3 Kalman-6DOF+PD)"))
        self.get_logger().info(
            "TrackingNode v3 — Kalman 6 estados (CA model), PD angular, Mahalanobis gate")

    # ─── Observación de posición ──────────────────────────────────────────────

    def _on_detected(self, msg: Bool):
        self.person_detected = msg.data

    def _on_position(self, msg: Point):
        px, py = self.kf.update(msg.x, msg.y)
        self.person_pos  = Point(x=px, y=py)
        self.last_obs_t  = time.monotonic()
        self.pos_pub.publish(self.person_pos)
        self.get_logger().debug(
            f"Kalman → ({px:.3f}, {py:.3f}) "
            f"v=({self.kf.velocity[0]:.2f},{self.kf.velocity[1]:.2f})")

    # ─── Bucle de control (cada scan, ~10Hz) ─────────────────────────────────

    def _on_scan(self, scan: LaserScan):
        if not self.tracking_enabled:
            self._stop()
            return

        # Si no hay posición aún, parar
        if self.person_pos is None or self.last_obs_t is None:
            self._stop()
            return

        elapsed = time.monotonic() - self.last_obs_t

        if elapsed > self.timeout_s:
            self.get_logger().warn(f"Timeout observación ({elapsed:.1f}s) → parar")
            self._stop()
            return

        # Durante oclusión breve (< timeout): usar predicción Kalman
        if elapsed > 0.3:
            px, py = self.kf.predict_position(elapsed)
        else:
            px, py = self.person_pos.x, self.person_pos.y

        distance = math.hypot(px, py)
        angle_to = math.atan2(py, px)

        # ── Velocidad lineal: rampa adaptativa ────────────────────────────
        d_eff    = max(0.0, distance - self.target_dist)
        norm     = min(1.0, d_eff)                             # ref 1 m
        tgt_vx   = self.max_speed * (norm ** self.vel_ramp_exp)
        delta    = tgt_vx - self.prev_vx
        delta    = max(-self.acc_limit, min(self.acc_limit, delta))
        vx       = self.prev_vx + delta
        self.prev_vx = vx

        # ── Velocidad angular: PD con zona muerta ────────────────────────
        ang_err = -angle_to
        # Clamp derivada: evita pico cuando la detección salta tras oclusión
        d_ang   = max(-0.3, min(0.3, ang_err - self.prev_angle))

        # Zona muerta ±8°: no girar para errores pequeños → elimina micro-oscilaciones
        DEAD = math.radians(8)
        if abs(ang_err) < DEAD:
            wz = self.ang_kd * d_ang
        else:
            eff_err = ang_err - math.copysign(DEAD, ang_err)
            wz = self.ang_kp * eff_err + self.ang_kd * d_ang

        # Acoplar wz con velocidad lineal: menos giro cuando se avanza rápido
        wz *= max(0.4, 1.0 - abs(vx) / max(self.max_speed, 0.01) * 0.5)
        wz  = max(-1.0, min(1.0, wz))
        self.prev_angle = ang_err

        # ── Evasión de obstáculos ─────────────────────────────────────────
        ang_adj, lin_factor = self._obstacle_avoidance(scan)
        vx  *= lin_factor
        wz  += ang_adj

        # ── Publicar ──────────────────────────────────────────────────────
        cmd = Twist()
        cmd.linear.x  = float(vx)
        cmd.angular.z = float(wz)
        self.vel_pub.publish(cmd)

        self._publish_telemetry(distance, angle_to, vx, wz, lin_factor, elapsed)

    # ─── Evasión de obstáculos ────────────────────────────────────────────────

    def _obstacle_avoidance(self, scan: LaserScan):
        if not self.obs_avoidance:
            return 0.0, 1.0

        repulsion = 0.0
        threat    = 0.0
        n         = 0

        for i, r in enumerate(scan.ranges):
            ang = scan.angle_min + i * scan.angle_increment
            if abs(ang) > math.radians(50):
                continue
            if not (scan.range_min < r < self.obs_threshold):
                continue
            w          = (self.obs_threshold - r) * math.cos(ang)
            repulsion += w * (-ang)
            threat    += w
            n         += 1

        if n == 0:
            return 0.0, 1.0

        adj        = max(-1.5, min(1.5, repulsion / n))
        lin_factor = max(0.3, 1.0 - 0.6 * min(1.0, threat / 0.5))
        self.get_logger().warn(
            f"Obstáculo frontal: adj={adj:.2f}  lin_factor={lin_factor:.2f}")
        return adj, lin_factor

    # ─── Telemetría ───────────────────────────────────────────────────────────

    def _publish_telemetry(self, dist, angle, vlin, vang, lin_factor, elapsed_obs):
        vx_est, vy_est = self.kf.velocity
        ax_est, ay_est = self.kf.acceleration
        payload = {
            "t":          round(time.time(), 3),
            "dist":       round(dist, 3),
            "angle_deg":  round(math.degrees(angle), 1),
            "vlin":       round(vlin, 3),
            "vang":       round(vang, 3),
            "lin_factor": round(lin_factor, 2),
            "obs_age":    round(elapsed_obs, 3),
            "kf_vx":      round(vx_est, 3),
            "kf_vy":      round(vy_est, 3),
            "kf_ax":      round(ax_est, 3),
            "kf_ay":      round(ay_est, 3),
        }
        self.telem_pub.publish(String(data=json.dumps(payload)))

    # ─── Utilidades ──────────────────────────────────────────────────────────

    def _stop(self):
        self.prev_vx    = 0.0
        self.prev_angle = 0.0
        self.vel_pub.publish(Twist())

    def _on_enable(self, req, resp):
        self.tracking_enabled = req.data
        if req.data and not self.kf.initialized:
            # Reset Kalman al empezar a seguir
            self.kf = KalmanTracker(
                q=self.get_parameter('kalman_q').value,
                r=self.get_parameter('kalman_r').value
            )
        resp.success = True
        resp.message = "enabled" if req.data else "disabled"
        self.get_logger().info(f"Tracking {'habilitado' if req.data else 'deshabilitado'}")
        self.status_pub.publish(String(data=resp.message))
        return resp

    def _on_shutdown(self, msg: Bool):
        if msg.data:
            self._shutdown_pub.publish(Bool(data=True))
            self.destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = TrackingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()
