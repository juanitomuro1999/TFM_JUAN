#!/usr/bin/env python3
# Copyright 2026 Juan Muñoz Rovira
# SPDX-License-Identifier: Apache-2.0
#
# verify_reacquire_sector.py — Verificación del (re)enganche solo por el
# frente (reacquire_sector_deg, 2026-09-23) con el DetectionNode REAL: se le
# pasan LaserScan sintéticos por su propio lidar_callback (filtro de mediana,
# interpolación, DBSCAN y gating incluidos) y se registran las posiciones que
# publica en /person_position.
#
# Escena: persona (dos piernas) DELANTE del robot a 1.2 m y un "mueble" con
# dos patas separadas 0.30 m (par de piernas falso) DETRÁS a 0.9 m — más cerca que la persona,
# que es justo lo que ganaba antes la selección por proximidad sin ancla.
#
# Uso (ROS 2 Jazzy + scipy): python3 validation/verify_reacquire_sector.py
# o sin ROS: bash validation/run_reacquire_docker.sh

import math
import os
import sys
import time

import rclpy
from sensor_msgs.msg import LaserScan

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from person_follower.detection_node.detection_node import DetectionNode  # noqa: E402

N_BEAMS = 1600                     # RPLIDAR A2M8 ~1600 muestras/vuelta a 10 Hz
LEG_R = 0.05


def leg_pair(x, y, sep=0.30):
    """Centros de dos 'piernas' separadas `sep` en perpendicular al rayo."""
    ang = math.atan2(y, x) + math.pi / 2
    dx, dy = math.cos(ang) * sep / 2, math.sin(ang) * sep / 2
    return [(x + dx, y + dy), (x - dx, y - dy)]


def scan(circles):
    """LaserScan del frame bruto del láser (delante del robot = ángulo π)."""
    m = LaserScan()
    m.header.frame_id = 'laser'
    m.angle_min, m.angle_max = -math.pi, math.pi
    m.angle_increment = 2 * math.pi / N_BEAMS
    m.range_min, m.range_max = 0.15, 12.0
    ranges = []
    for i in range(N_BEAMS):
        a = m.angle_min + i * m.angle_increment
        ux, uy = math.cos(a), math.sin(a)
        best = float('inf')
        for cx, cy in circles:
            b = ux * cx + uy * cy
            c = cx * cx + cy * cy - LEG_R ** 2
            disc = b * b - c
            if disc >= 0 and b - math.sqrt(disc) > 0:
                best = min(best, b - math.sqrt(disc))
        ranges.append(best)
    m.ranges = ranges
    return m


# Frame bruto del láser: delante ≈ (-x), detrás ≈ (+x)
PERSON_FRONT = leg_pair(-1.2, 0.0)
FURNITURE_BEHIND = leg_pair(0.9, 0.0, sep=0.30)
# Frente = ángulo π del láser; a 70° de él (lateral) y a 130° (detrás en diagonal)
PERSON_SIDE = leg_pair(1.2 * math.cos(math.radians(180 - 70)), 1.2 * math.sin(math.radians(180 - 70)))
PERSON_BACK_SIDE = leg_pair(1.2 * math.cos(math.radians(180 - 130)), 1.2 * math.sin(math.radians(180 - 130)))


def make_node(sector_deg):
    params = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          '..', 'person_follower', 'config', 'config.yaml')
    ctx_args = ['--ros-args', '--params-file', params,
                '-p', f'reacquire_sector_deg:={sector_deg}',
                '-p', f'reacquire_after_s:={0.0 if sector_deg >= 180 else 0.5}',
                '-r', '__node:=detection_node']
    rclpy.init(args=ctx_args)
    node = DetectionNode()
    published = []
    orig = node.person_position_publisher.publish

    def rec(pt):
        # /person_position: delante = +x. Ángulo respecto al frente del robot.
        published.append((time.monotonic(), math.hypot(pt.x, pt.y),
                          math.degrees(math.atan2(pt.y, pt.x))))
        orig(pt)
    node.person_position_publisher.publish = rec
    node.log_info = lambda *a, **k: None
    return node, published


def feed(node, circles, n):
    for _ in range(n):
        node.lidar_callback(scan(circles))
        time.sleep(0.1)


def phase(node, published, circles, n):
    k = len(published)
    feed(node, circles, n)
    return published[k:]


def summary(pubs):
    if not pubs:
        return "sin publicaciones"
    angs = [a for _, _, a in pubs]
    ds = [d for _, d, _ in pubs]
    return (f"{len(pubs)} pubs, dist {min(ds):.2f}-{max(ds):.2f} m, "
            f"ángulo {min(angs):+.0f}..{max(angs):+.0f}° (0 = delante)")


def main():
    results = []
    for sector in (180.0, 90.0):
        node, pub = make_node(sector)
        print(f"\n=== reacquire_sector_deg = {sector:.0f} "
              f"({'antes' if sector >= 180 else 'nuevo'}) ===")
        p1 = phase(node, pub, PERSON_FRONT + FURNITURE_BEHIND, 15)
        print(f" 1. arranque persona delante + mueble detrás: {summary(p1)}")
        p2 = phase(node, pub, FURNITURE_BEHIND, 20)
        print(f" 2. persona desaparece (2 s), solo mueble:    {summary(p2)}")
        p3 = phase(node, pub, PERSON_FRONT + FURNITURE_BEHIND, 15)
        print(f" 3. persona reaparece delante:               {summary(p3)}")
        phase(node, pub, FURNITURE_BEHIND, 20)
        p5 = phase(node, pub, PERSON_SIDE + FURNITURE_BEHIND, 15)
        print(f" 4. tras otra pérdida, persona a 70° al lado: {summary(p5)}")
        phase(node, pub, FURNITURE_BEHIND, 20)
        p7 = phase(node, pub, PERSON_BACK_SIDE + FURNITURE_BEHIND, 15)
        print(f" 4b. tras otra pérdida, algo a 130° (detrás): {summary(p7)}")
        # 5. Seguimiento normal con ancla: re-enganche delante y la persona
        #    camina de forma continua (0.06 m/scan ≈ 0.6 m/s) hasta 80° al lado.
        phase(node, pub, FURNITURE_BEHIND, 20)
        phase(node, pub, PERSON_FRONT + FURNITURE_BEHIND, 10)
        k = len(pub)
        for step in range(40):
            ang = math.radians(180 - 2 * step)          # 180° → 100° (láser)
            feed(node, leg_pair(1.2 * math.cos(ang), 1.2 * math.sin(ang)) + FURNITURE_BEHIND, 1)
        p6 = pub[k:]
        print(f" 5. con ancla, camina de frente a 80° al lado: {summary(p6)}")
        results.append((sector, p1, p2, p3, p5, p6, p7))
        node.destroy_node()
        rclpy.shutdown()

    def behind(pubs):
        return [p for p in pubs if abs(p[2]) > 90]

    def front(pubs):
        return [p for p in pubs if abs(p[2]) < 30]

    old, new = results
    checks = [
        ("antes: sin ancla se enganchaba al mueble de detrás (reproduce el bug)",
         bool(behind(old[1]) or behind(old[2]))),
        ("nuevo: arranque engancha a la persona de delante, nunca al mueble",
         bool(front(new[1])) and not behind(new[1])),
        ("nuevo: con la persona perdida no publica el mueble de detrás",
         not behind(new[2])),
        ("nuevo: re-engancha a la persona al reaparecer delante",
         bool(front(new[3])) and not behind(new[3])),
        ("nuevo: re-engancha a la persona a 70° al lado (sector ±90°)",
         bool(new[4]) and all(60 <= abs(p[2]) <= 80 for p in new[4])),
        ("nuevo: no re-engancha a 130° (detrás en diagonal)",
         not new[6]),
        ("nuevo: con ancla sigue a la persona de forma continua hasta 80° al lado",
         len(new[5]) >= 36 and max(abs(p[2]) for p in new[5]) >= 75
         and not behind(new[5])),
    ]
    print()
    for name, ok in checks:
        print(f"[{'OK ' if ok else 'FALLO'}] {name}")
    ok = sum(c for _, c in checks)
    print(f"\n{ok}/{len(checks)} comprobaciones correctas")
    sys.exit(0 if ok == len(checks) else 1)


if __name__ == '__main__':
    main()
