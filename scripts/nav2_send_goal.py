#!/usr/bin/env python3
# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# Demo minima de Nav2 (objetivo especifico 3 del TFM): manda UN objetivo de
# navegacion a un punto fijo del mapa con nav2_simple_commander.
#
#   ANDAMIAJE SIN PROBAR (2026-07-09, escrito sin acceso al robot).
#
# Requisitos antes de usarlo:
#   1. person_follower/launch/nav2_localization_demo.launch.py ya lanzado y
#      con AMCL localizando de forma estable (confirmar en RViz).
#   2. paquete nav2_simple_commander instalado (suele venir con
#      nav2-bringup; comprobar con `ros2 pkg list | grep simple_commander`).
#   3. Las coordenadas (x, y) son en el frame `map` del mapa guardado
#      (maps/mapa_laboratorio.yaml, origen [-8.319, -11.352, 0], resolucion
#      0.05 m/px) -- hay que leerlas sobre el mapa real en RViz la primera
#      vez, no se pueden adivinar sin el robot.
#
# Uso (en el NUC, con el workspace sourceado):
#   python3 scripts/nav2_send_goal.py <x> <y> [yaw_deg=0]

import sys
import math

import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator
from geometry_msgs.msg import PoseStamped


def main():
    if len(sys.argv) < 3:
        print("Uso: python3 nav2_send_goal.py <x> <y> [yaw_deg=0]")
        sys.exit(1)

    x = float(sys.argv[1])
    y = float(sys.argv[2])
    yaw_deg = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0

    rclpy.init()
    navigator = BasicNavigator()

    print("Esperando a que Nav2 este activo (lifecycle managers)...")
    navigator.waitUntilNav2Active()

    goal = PoseStamped()
    goal.header.frame_id = 'map'
    goal.header.stamp = navigator.get_clock().now().to_msg()
    goal.pose.position.x = x
    goal.pose.position.y = y
    # Rotacion pura en Z: solo componentes z/w del cuaternion.
    half_rad = math.radians(yaw_deg) / 2.0
    goal.pose.orientation.z = math.sin(half_rad)
    goal.pose.orientation.w = math.cos(half_rad)

    print(f"Enviando objetivo: x={x:.2f} y={y:.2f} yaw={yaw_deg:.1f}deg")
    navigator.goToPose(goal)

    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            print(f"  distancia restante: {feedback.distance_remaining:.2f} m")

    result = navigator.getResult()
    print(f"Resultado final: {result}")

    rclpy.shutdown()


if __name__ == '__main__':
    main()
