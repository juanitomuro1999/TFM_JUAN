#!/usr/bin/env python3
# Copyright 2026 Juan Muñoz Rovira
# SPDX-License-Identifier: Apache-2.0
#
# Imprime la pose actual de AMCL como las líneas home_x/home_y/home_yaw_deg
# de config.yaml (control_node), para fijar la pose "casa" del gesto go_home.
#
# Uso (en el NUC, con AMCL localizado y el robot aparcado en casa):
#   python3 scripts/print_home_pose.py
#
# Espera hasta 15 s: /amcl_pose es transient_local, pero el descubrimiento
# DDS de un proceso nuevo por SSH tarda varios segundos (Sesión 7).

import math
import sys

import rclpy
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy
from geometry_msgs.msg import PoseWithCovarianceStamped


def main():
    rclpy.init()
    node = rclpy.create_node('print_home_pose')
    qos = QoSProfile(depth=1,
                     durability=DurabilityPolicy.TRANSIENT_LOCAL,
                     reliability=ReliabilityPolicy.RELIABLE)
    got = []
    node.create_subscription(PoseWithCovarianceStamped, '/amcl_pose',
                             lambda m: got.append(m), qos)

    deadline = node.get_clock().now().nanoseconds + 15e9
    while not got and node.get_clock().now().nanoseconds < deadline:
        rclpy.spin_once(node, timeout_sec=0.5)

    if not got:
        print("Sin /amcl_pose en 15 s — ¿AMCL activo y con pose inicial?")
        sys.exit(1)

    p = got[0].pose.pose
    yaw = math.atan2(2.0 * (p.orientation.w * p.orientation.z
                            + p.orientation.x * p.orientation.y),
                     1.0 - 2.0 * (p.orientation.y ** 2 + p.orientation.z ** 2))
    cov = got[0].pose.covariance
    print(f"# frame={got[0].header.frame_id}  "
          f"sigma_xy≈{math.sqrt(max(cov[0], cov[7])):.2f} m")
    print(f"    home_x: {p.position.x:.3f}")
    print(f"    home_y: {p.position.y:.3f}")
    print(f"    home_yaw_deg: {math.degrees(yaw):.1f}")
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
