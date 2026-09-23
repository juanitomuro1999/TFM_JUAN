#!/usr/bin/env python3
# Copyright 2026 Juan Muñoz Rovira
# SPDX-License-Identifier: Apache-2.0
#
# verify_lost_search.py — Verificación del giro de búsqueda (lost_search_*,
# 2026-09-23) con el TrackingNode REAL: se activa el seguimiento por su
# servicio, se le da una última observación de la persona a un lado y se
# dejan de mandar observaciones; se le pasan /scan vacíos por su
# _on_scan y se registra el Twist que publica en /tracking/velocity_cmd.
#
# Uso (ROS 2 Jazzy): python3 validation/verify_lost_search.py
# o sin ROS: bash validation/run_lost_search_docker.sh

import math
import os
import sys
import time

import rclpy
from geometry_msgs.msg import Point
from sensor_msgs.msg import LaserScan
from std_srvs.srv import SetBool

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from person_follower.tracking_node.tracking_node import TrackingNode  # noqa: E402

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      '..', 'person_follower', 'config', 'config.yaml')


def empty_scan():
    m = LaserScan()
    m.angle_min, m.angle_max = -math.pi, math.pi
    m.angle_increment = 2 * math.pi / 720
    m.range_min, m.range_max = 0.15, 12.0
    m.ranges = [float('inf')] * 720
    return m


def run_case(node, angle_deg, dist=1.5, duration=3.5):
    """Observa a la persona a `angle_deg` (convenio /person_position: +x
    delante, ángulo + = izquierda) durante 0.5 s y luego la pierde."""
    node._on_enable(SetBool.Request(data=False), SetBool.Response())
    node._on_enable(SetBool.Request(data=True), SetBool.Response())
    out = []
    node.vel_pub.publish = lambda m: out.append((time.monotonic(), m.linear.x, m.angular.z))
    a = math.radians(angle_deg)
    t_end = time.monotonic() + 0.5
    while time.monotonic() < t_end:
        node._on_position(Point(x=dist * math.cos(a), y=dist * math.sin(a)))
        node._on_scan(empty_scan())
        time.sleep(0.1)
    t_lost = time.monotonic()
    out.clear()
    while time.monotonic() - t_lost < duration:
        node._on_scan(empty_scan())
        time.sleep(0.1)
    return [(t - t_lost, vx, wz) for t, vx, wz in out]


def window(cmds, t0, t1):
    return [c for c in cmds if t0 <= c[0] <= t1]


def main():
    rclpy.init(args=['--ros-args', '--params-file', CONFIG, '-r', '__node:=tracking_node'])
    node = TrackingNode()
    node.get_logger().set_level(40)
    checks = []

    right = run_case(node, -40)
    left = run_case(node, +40)
    front = run_case(node, +5)

    def fmt(cmds):
        return " ".join(f"{t:.1f}s:wz={wz:+.2f}" for t, _, wz in cmds[::5])

    print("persona perdida a -40° (derecha):", fmt(right))
    print("persona perdida a +40° (izquierda):", fmt(left))
    print("persona perdida a +5° (de frente):", fmt(front))

    srch_r = window(right, 1.0, 2.5)
    srch_l = window(left, 1.0, 2.5)
    checks += [
        ("derecha: gira a la derecha (wz<0) sin avanzar entre 1.0 y 2.5 s",
         srch_r and all(wz < -0.2 and vx == 0.0 for _, vx, wz in srch_r)),
        ("izquierda: gira a la izquierda (wz>0) sin avanzar entre 1.0 y 2.5 s",
         srch_l and all(wz > 0.2 and vx == 0.0 for _, vx, wz in srch_l)),
        ("velocidad de búsqueda acotada a lost_search_wz (0.5 rad/s)",
         all(abs(wz) <= 0.5 + 1e-6 for _, _, wz in window(right + left, 0.7, 9))),
        ("tras extrapolation_limit_s + lost_search_s (2.6 s) se para",
         all(vx == 0.0 and wz == 0.0 for _, vx, wz in window(right + left, 2.8, 9))),
        ("perdida de frente (+5°): no gira, se para como antes",
         all(wz == 0.0 for _, _, wz in window(front, 0.8, 9))),
    ]
    print()
    for name, ok in checks:
        print(f"[{'OK ' if ok else 'FALLO'}] {name}")
    ok = sum(bool(c) for _, c in checks)
    print(f"\n{ok}/{len(checks)} comprobaciones correctas")
    node.destroy_node()
    rclpy.shutdown()
    sys.exit(0 if ok == len(checks) else 1)


if __name__ == '__main__':
    main()
