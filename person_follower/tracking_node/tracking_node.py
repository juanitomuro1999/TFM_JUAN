# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# tracking_node.py — v2: Kalman dt real + PD angular + velocidad adaptativa + telemetría

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


class TrackingNode(Node):
    def __init__(self):
        super().__init__('tracking_node')

        # ── Parámetros ────────────────────────────────────────────────────
        self.declare_parameter('enabled', True)
        self.declare_parameter('obstacle_avoidance_enabled', True)
        self.declare_parameter('max_speed',        0.4)
        self.declare_parameter('target_distance',  0.4)
        self.declare_parameter('acc_limit',        0.05)
        self.declare_parameter('angular_gain',     2.0)
        self.declare_parameter('angular_d_gain',   0.3)   # NUEVO: derivada angular
        self.declare_parameter('vel_ramp_exp',     1.5)   # NUEVO: exponente rampa (1=lineal, >1=suave)
        self.declare_parameter('kalman_q',         0.02)  # NUEVO: ruido proceso Kalman
        self.declare_parameter('kalman_r',         0.04)  # NUEVO: ruido medida Kalman

        self.enabled = self.get_parameter('enabled').value
        if not self.enabled:
            self.get_logger().info("TrackingNode desactivado.")
            self._pub_status = self.create_publisher(String, '/tracking/status', 10)
            self._pub_status.publish(String(data="Nodo desactivado."))
            return

        self.obstacle_avoidance_enabled = self.get_parameter('obstacle_avoidance_enabled').value
        self.max_speed       = self.get_parameter('max_speed').value
        self.target_distance = self.get_parameter('target_distance').value
        self.acc_limit       = self.get_parameter('acc_limit').value
        self.ang_kp          = self.get_parameter('angular_gain').value
        self.ang_kd          = self.get_parameter('angular_d_gain').value
        self.vel_ramp_exp    = self.get_parameter('vel_ramp_exp').value
        kq                   = self.get_parameter('kalman_q').value
        kr                   = self.get_parameter('kalman_r').value

        # ── Kalman (estado: [x, y, vx, vy]) ──────────────────────────────
        self.kf_x   = np.zeros(4)
        self.kf_P   = np.eye(4) * 0.5
        self.kf_H   = np.array([[1, 0, 0, 0],
                                 [0, 1, 0, 0]], dtype=float)
        self.kf_R   = np.eye(2) * kr
        self.kf_Q   = np.eye(4) * kq
        self._last_kf_time: float | None = None   # timestamp float (s)

        # ── Estado de control ─────────────────────────────────────────────
        self.tracking_enabled      = False
        self.person_detected       = False
        self.person_position: Point | None = None
        self.last_person_update_t: float | None = None
        self.timeout_duration      = 2.0   # s sin observación → parar

        self.prev_vx     = 0.0
        self.prev_angle  = 0.0            # para derivada angular

        # ── Publicadores ─────────────────────────────────────────────────
        self.vel_pub      = self.create_publisher(Twist,  '/tracking/velocity_cmd', 10)
        self.pos_pub      = self.create_publisher(Point,  '/expected_person_position', 10)
        self.status_pub   = self.create_publisher(String, '/tracking/status', 10)
        self.telem_pub    = self.create_publisher(String, '/follower/telemetry', 10)

        # ── Suscripciones ─────────────────────────────────────────────────
        self.create_subscription(Point,     '/person_position', self._on_position, 10)
        self.create_subscription(Bool,      '/person_detected', self._on_detected,  10)
        self.create_subscription(LaserScan, '/scan',            self._on_scan,      10)

        # ── Servicio enable/disable ───────────────────────────────────────
        self.create_service(SetBool, 'enable_tracking', self._on_enable)

        # ── Shutdown ──────────────────────────────────────────────────────
        self.create_subscription(Bool, '/system_shutdown', self._on_shutdown, 10)
        self._shutdown_pub = self.create_publisher(Bool, '/shutdown_confirmation', 10)

        self._pub_status("Nodo OK (v2 PD+Kalman-dt)")
        self.get_logger().info("TrackingNode v2 iniciado — PD angular, Kalman dt real, telemetría")

    # ─────────────────────────────────────────────────────────────────────
    # Callbacks de suscripción
    # ─────────────────────────────────────────────────────────────────────

    def _on_detected(self, msg: Bool):
        self.person_detected = msg.data

    def _on_position(self, msg: Point):
        """Actualiza el filtro de Kalman con nueva observación."""
        now = time.monotonic()
        dt = (now - self._last_kf_time) if self._last_kf_time is not None else 0.1
        dt = max(0.01, min(dt, 0.5))   # saturar entre 10ms y 500ms
        self._last_kf_time = now

        # Matriz de transición con dt real
        F = np.eye(4)
        F[0, 2] = dt
        F[1, 3] = dt

        # Predicción
        x_pred = F @ self.kf_x
        P_pred = F @ self.kf_P @ F.T + self.kf_Q

        # Corrección (innovación)
        z   = np.array([msg.x, msg.y])
        inn = z - self.kf_H @ x_pred
        S   = self.kf_H @ P_pred @ self.kf_H.T + self.kf_R
        K   = P_pred @ self.kf_H.T @ np.linalg.inv(S)
        self.kf_x = x_pred + K @ inn
        self.kf_P = (np.eye(4) - K @ self.kf_H) @ P_pred

        self.person_position = Point(x=float(self.kf_x[0]), y=float(self.kf_x[1]))
        self.last_person_update_t = now
        self.pos_pub.publish(self.person_position)

    def _on_scan(self, scan: LaserScan):
        """Bucle principal de control: se ejecuta a ~10-12 Hz con cada scan."""
        if not self.tracking_enabled or self.person_position is None:
            self._stop()
            return

        # Comprobar timeout de observación
        elapsed = time.monotonic() - self.last_person_update_t
        if elapsed > self.timeout_duration:
            self.get_logger().warn(f"Timeout posición ({elapsed:.1f}s) → parar")
            self._stop()
            return

        dx, dy   = self.person_position.x, self.person_position.y
        distance = math.hypot(dx, dy)
        angle_to = math.atan2(dy, dx)

        # ── Velocidad lineal: rampa adaptativa ───────────────────────────
        d_eff     = max(0.0, distance - self.target_distance)
        # Rampa con exponente configurable: más suave al acercarse, más rápida lejos
        norm      = min(1.0, d_eff / 1.0)          # 1.0 m de referencia
        target_vx = self.max_speed * (norm ** self.vel_ramp_exp)
        # Rampas de aceleración/frenada
        delta     = target_vx - self.prev_vx
        delta     = max(-self.acc_limit, min(self.acc_limit, delta))
        vx        = self.prev_vx + delta
        self.prev_vx = vx

        # ── Velocidad angular: PD ────────────────────────────────────────
        angle_err  = -angle_to                      # error (negativo: izq)
        d_angle    = angle_err - self.prev_angle    # derivada (aproximada a 10Hz)
        wz         = self.ang_kp * angle_err + self.ang_kd * d_angle
        wz         = max(-1.8, min(1.8, wz))
        self.prev_angle = angle_err

        # ── Evasión de obstáculos ────────────────────────────────────────
        ang_adj, lin_factor = self._obstacle_avoidance(scan)
        vx  *= lin_factor
        wz  += ang_adj

        # ── Publicar ─────────────────────────────────────────────────────
        cmd = Twist()
        cmd.linear.x  = float(vx)
        cmd.angular.z = float(wz)
        self.vel_pub.publish(cmd)

        # ── Telemetría (JSON, ~10Hz) ──────────────────────────────────────
        self._publish_telemetry(distance, angle_to, vx, wz, lin_factor, elapsed)

    # ─────────────────────────────────────────────────────────────────────
    # Evasión de obstáculos mejorada
    # ─────────────────────────────────────────────────────────────────────

    def _obstacle_avoidance(self, scan: LaserScan):
        if not self.obstacle_avoidance_enabled:
            return 0.0, 1.0

        repulsion = 0.0
        threat    = 0.0
        n_front   = 0

        for i, r in enumerate(scan.ranges):
            ang = scan.angle_min + i * scan.angle_increment
            if abs(ang) > math.radians(50):
                continue
            if not (scan.range_min < r < 0.65):
                continue
            w = (0.65 - r) * math.cos(ang)          # peso: más cerca y más central
            repulsion += w * (-ang)                  # empujar en dirección contraria
            threat    += w
            n_front   += 1

        if n_front == 0:
            return 0.0, 1.0

        adj        = max(-1.5, min(1.5, repulsion / n_front))
        lin_factor = max(0.3, 1.0 - 0.6 * min(1.0, threat / 0.5))

        self.get_logger().warn(
            f"Obstáculo frontal: adj={adj:.2f} lin_factor={lin_factor:.2f}")
        return adj, lin_factor

    # ─────────────────────────────────────────────────────────────────────
    # Telemetría
    # ─────────────────────────────────────────────────────────────────────

    def _publish_telemetry(self, dist, angle, vlin, vang, lin_factor, elapsed_obs):
        """Publica JSON en /follower/telemetry para grabación en tiempo real."""
        payload = {
            "t":          round(time.time(), 3),
            "dist":       round(dist, 3),
            "angle_deg":  round(math.degrees(angle), 1),
            "vlin":       round(vlin, 3),
            "vang":       round(vang, 3),
            "lin_factor": round(lin_factor, 2),
            "obs_age":    round(elapsed_obs, 3),
            "kf_vx":      round(float(self.kf_x[2]), 3),
            "kf_vy":      round(float(self.kf_x[3]), 3),
        }
        self.telem_pub.publish(String(data=json.dumps(payload)))

    # ─────────────────────────────────────────────────────────────────────
    # Utilidades
    # ─────────────────────────────────────────────────────────────────────

    def _stop(self):
        self.prev_vx = 0.0
        self.vel_pub.publish(Twist())

    def _pub_status(self, msg: str):
        self.status_pub.publish(String(data=msg))

    def _on_enable(self, req, resp):
        self.tracking_enabled = req.data
        resp.success = True
        resp.message = "enabled" if req.data else "disabled"
        self.get_logger().info(f"Tracking {'habilitado' if req.data else 'deshabilitado'}")
        self._pub_status(resp.message)
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
