# Copyright 2026 omixxxer
# Author: omixxxer
# SPDX-License-Identifier: Apache-2.0

import rclpy
import numpy as np
import math
from rclpy.node import Node
from geometry_msgs.msg import Twist, Point
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String
from std_srvs.srv import SetBool

class TrackingNode(Node):
    def __init__(self):
        super().__init__('tracking_node')

        # Verificar si el nodo está habilitado
        self.declare_parameter('enabled', True)
        self.enabled = self.get_parameter('enabled').value

        if not self.enabled:
            self.get_logger().info("Nodo de Seguimiento desactivado.")
            self.publish_status("Nodo desactivado.")
            return

        # Estado del nodo de seguimiento
        self.tracking_enabled = False

        # Inicializar shutdown
        self.initialize_shutdown_listener()

        # Parámetros de evasión y velocidad
        self.declare_parameter('obstacle_avoidance_enabled', True)
        self.declare_parameter('max_speed', 0.4)
        self.declare_parameter('target_distance', 0.4)
        self.declare_parameter('acc_limit', 0.05)
        self.declare_parameter('angular_gain', 2.0)
        self.obstacle_avoidance_enabled = self.get_parameter('obstacle_avoidance_enabled').value
        self.max_speed       = self.get_parameter('max_speed').value
        self.target_distance = self.get_parameter('target_distance').value
        self.acc_limit       = self.get_parameter('acc_limit').value
        self.angular_gain    = self.get_parameter('angular_gain').value

        # Filtro de Kalman para posición de persona
        self.kalman_state = np.zeros(4)  # [x, y, vx, vy]
        self.kalman_covariance = np.eye(4) * 0.1
        self.kalman_F = np.eye(4)
        self.kalman_H = np.array([[1, 0, 0, 0], [0, 1, 0, 0]])
        self.kalman_R = np.eye(2) * 0.05
        self.kalman_Q = np.eye(4) * 0.01

        # Servicio para habilitar/deshabilitar seguimiento
        self.create_service(SetBool, 'enable_tracking', self.enable_tracking_callback)

        # Publicadores y suscripciones
        self.person_position_subscription = self.create_subscription(
            Point, '/person_position', self.person_position_callback, 10)
        self.person_detected_subscription = self.create_subscription(
            Bool, '/person_detected', self.detection_callback, 10)
        self.scan_subscription = self.create_subscription(
            LaserScan, '/scan', self.listener_callback, 10)

        self.velocity_publisher = self.create_publisher(Twist, '/tracking/velocity_cmd', 10)
        self.position_publisher = self.create_publisher(Point, '/expected_person_position', 10)
        self.status_publisher = self.create_publisher(String, '/tracking/status', 10)

        # Variables de control
        self.person_detected = False
        self.person_position = None
        self.last_person_update_time = None
        self.timeout_duration = 2.0  # segundos
        self.previous_vx = 0.0

        self.get_logger().info("Nodo de Seguimiento iniciado")
        self.publish_status("Nodo OK.")

    def enable_tracking_callback(self, request, response):
        self.tracking_enabled = request.data
        response.success = True
        response.message = f"{'Enabled' if self.tracking_enabled else 'Disabled'}"
        self.get_logger().info(response.message)
        self.publish_status(response.message) 
        return response

    def detection_callback(self, msg):
        self.person_detected = msg.data

    def person_position_callback(self, msg):
        # Observación de la persona
        z = np.array([msg.x, msg.y])
        # Predicción Kalman
        self.kalman_F[:2, 2:] = np.eye(2) * 0.1
        pred_state = self.kalman_F @ self.kalman_state
        pred_cov = self.kalman_F @ self.kalman_covariance @ self.kalman_F.T + self.kalman_Q
        # Actualización con observación
        y = z - (self.kalman_H @ pred_state)
        S = self.kalman_H @ pred_cov @ self.kalman_H.T + self.kalman_R
        K = pred_cov @ self.kalman_H.T @ np.linalg.inv(S)
        self.kalman_state = pred_state + K @ y
        self.kalman_covariance = (np.eye(4) - K @ self.kalman_H) @ pred_cov

        # Publicar posición estimada
        self.person_position = Point(x=self.kalman_state[0], y=self.kalman_state[1])
        self.last_person_update_time = self.get_clock().now()
        self.position_publisher.publish(self.person_position)
        self.get_logger().info(
            f"Kalman -> x={self.person_position.x:.2f}, y={self.person_position.y:.2f}")

    def avoid_obstacles(self, scan_msg):
        """
        Evasión avanzada: reconoce múltiples obstáculos en ±45°
        y calcula un vector de repulsión (ajuste angular) y un
        factor de reducción lineal.
        """
        if not self.obstacle_avoidance_enabled:
            return 0.0, 1.0

        repulsive_force = 0.0
        count = 0
        # Analizar sólo ángulo frontal ±45°
        for i, distance in enumerate(scan_msg.ranges):
            angle = scan_msg.angle_min + i * scan_msg.angle_increment
            if abs(angle) <= math.radians(45) and scan_msg.range_min < distance < 0.6:
                # Peso mayor cuanto más cerca y centrado
                weight = (0.6 - distance) * math.cos(angle)
                repulsive_force += weight * -angle
                count += 1

        if count == 0:
            return 0.0, 1.0

        # Ajuste angular promedio, limitado
        adjustment = repulsive_force / count
        adjustment = max(-1.5, min(1.5, adjustment))
        # Reducción lineal proporcional al nivel de amenaza
        threat_ratio = min(1.0, count / (len(scan_msg.ranges) * 0.25))
        linear_factor = 1.0 - 0.5 * threat_ratio

        self.get_logger().warn(
            f"Evasión -> angle_adj={adjustment:.2f}, lin_factor={linear_factor:.2f}")
        return adjustment, linear_factor

    def listener_callback(self, scan_msg):
        if not self.tracking_enabled or not self.person_position:
            self.stop_robot()
            return
        # El Kalman predice la posición mientras haya actualizaciones recientes.
        # Sólo parar si el timeout de posición se agota (persona realmente perdida).
        elapsed = (self.get_clock().now() - self.last_person_update_time).nanoseconds * 1e-9
        if elapsed > self.timeout_duration:
            self.get_logger().warn("Timeout de posición -> Detener robot")
            self.stop_robot()
            return

        # Cálculo objetivo sobre estado Kalman
        dx, dy = self.person_position.x, self.person_position.y
        distance = math.hypot(dx, dy)
        angle_to_person = math.atan2(dy, dx)

        # Evasión avanzada
        angle_adj, lin_factor = self.avoid_obstacles(scan_msg)

        # Velocidad lineal: rampa suave con acc_limit configurable
        # Zona muerta = target_distance; velocidad máxima a target_distance + 1m
        d_eff = max(0.0, distance - self.target_distance)
        target_vx = min(self.max_speed, self.max_speed * d_eff)
        vx = self.previous_vx + min(self.acc_limit, max(-self.acc_limit, target_vx - self.previous_vx))
        self.previous_vx = vx
        vx *= lin_factor

        # Velocidad angular proporcional
        angle_diff = -angle_to_person
        wz = self.angular_gain * angle_diff + angle_adj
        wz = max(-1.6, min(1.6, wz))

        # Publicar comando
        cmd = Twist()
        cmd.linear.x = vx
        cmd.angular.z = wz
        self.velocity_publisher.publish(cmd)

    def stop_robot(self):
        # Detiene el robot publicando velocidades cero
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.angular.z = 0.0
        self.velocity_publisher.publish(cmd)

    def publish_status(self, message):
        self.status_publisher.publish(String(data=message))

    # --- Shutdown handling ---
    def initialize_shutdown_listener(self):
            self.create_subscription(Bool, '/system_shutdown', self.shutdown_callback, 10)
            self.shutdown_confirmation_publisher = self.create_publisher(Bool, '/shutdown_confirmation', 10)

    def shutdown_callback(self, msg):
        if msg.data:
            self.get_logger().info("Shutdown detectado -> confirmando")
            try:
                # Se asume existencia de este publisher
                self.shutdown_confirmation_publisher.publish(Bool(data=True))
            except Exception as e:
                self.get_logger().error(f"Error conf shutdown: {e}")
            finally:
                self.destroy_node()


def main(args=None):
    rclpy.init()
    node = TrackingNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("TrackingNode detenido con Ctrl-C.")
    finally:
        node.destroy_node()


if __name__ == '__main__':
    main()
