#!/usr/bin/env python3
# Copyright 2026 Juan Muñoz Rovira
# SPDX-License-Identifier: Apache-2.0
#
# verify_home_gesture.py — Verificación sintética, sin ROS ni cámara, del
# gesto "casa" (go_home, tejado) y de que los tres gestos son mutuamente
# excluyentes.
#
# A diferencia de verify_fusion_confirm.py, aquí NO hay réplica de la
# lógica: se importa directamente person_follower/visual_detection_node/
# gestures.py, que es el mismo código que ejecuta visual_detection_node
# (el módulo no depende de rclpy). Los parámetros son los de config.yaml.
#
# Uso:
#   python3 validation/verify_home_gesture.py

import os
import sys
from types import SimpleNamespace as P

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from person_follower.visual_detection_node.gestures import (  # noqa: E402
    GestureDebouncer, classify_gesture)

# config.yaml (visual_detection_node)
MIN_VIS, MARGIN_RATIO, ROOF_SEP = 0.5, 0.15, 0.6
CONFIRM, COOLDOWN, DT = 3, 2.0, 0.4          # detection_interval=0.4 → 2.5 Hz


def pose(r_wrist, l_wrist, nose_vis=0.99, wrist_vis=0.9, mirror=False):
    """Persona de frente a 320x240 normalizado. Torso hombro→cadera = 0.30.
    mirror=True simula verla de espaldas (MediaPipe intercambia izq/der)."""
    lm = [P(x=0.5, y=0.5, visibility=0.0) for _ in range(33)]
    lm[0] = P(x=0.50, y=0.20, visibility=nose_vis)            # nariz
    lm[11] = P(x=0.58, y=0.35, visibility=0.95)               # hombro izq
    lm[12] = P(x=0.42, y=0.35, visibility=0.95)               # hombro der
    lm[23] = P(x=0.55, y=0.65, visibility=0.9)                # cadera izq
    lm[24] = P(x=0.45, y=0.65, visibility=0.9)                # cadera der
    lm[16] = P(x=r_wrist[0], y=r_wrist[1], visibility=wrist_vis)
    lm[15] = P(x=l_wrist[0], y=l_wrist[1], visibility=wrist_vis)
    if mirror:
        for a, b in ((11, 12), (15, 16), (23, 24)):
            lm[a], lm[b] = lm[b], lm[a]
    return lm


DOWN_R, DOWN_L = (0.40, 0.62), (0.60, 0.62)      # brazos caídos
UP_R, UP_L = (0.38, 0.22), (0.62, 0.22)          # mano sobre el hombro
ROOF_R, ROOF_L = (0.48, 0.08), (0.52, 0.08)      # muñecas juntas sobre cabeza


def run(frames):
    """Pasa una secuencia de poses por clasificador+debouncer; devuelve los
    comandos emitidos."""
    deb = GestureDebouncer(CONFIRM, COOLDOWN)
    out = []
    for i, lm in enumerate(frames):
        g, _ = classify_gesture(lm, MIN_VIS, MARGIN_RATIO, ROOF_SEP)
        cmd = deb.update(g, i * DT)
        if cmd:
            out.append(cmd)
    return out


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def raise_to(r_target, l_target, steps, hold, r_delay=0, l_delay=0):
    """Subida gradual de cada brazo (con retardo opcional) y mantenimiento."""
    frames = []
    for i in range(steps + max(r_delay, l_delay) + hold):
        tr = min(1.0, max(0.0, (i - r_delay) / steps))
        tl = min(1.0, max(0.0, (i - l_delay) / steps))
        frames.append(pose(lerp(DOWN_R, r_target, tr), lerp(DOWN_L, l_target, tl)))
    return frames


CASES = [
    ("reposo (brazos caídos)", [pose(DOWN_R, DOWN_L)] * 10, []),
    ("mano derecha arriba", [pose(UP_R, DOWN_L)] * 4, ['start_tracking']),
    ("mano izquierda arriba", [pose(DOWN_R, UP_L)] * 4, ['stop_tracking']),
    ("tejado mantenido 1.2 s", [pose(ROOF_R, ROOF_L)] * 3, ['go_home']),
    ("tejado mantenido 4 s → 2 emisiones (cooldown 2 s; "
     "control_node ignora go_home ya en HOMING)",
     [pose(ROOF_R, ROOF_L)] * 10, ['go_home', 'go_home']),
    ("tejado solo 2 frames (0.8 s) → nada", [pose(ROOF_R, ROOF_L)] * 2, []),
    ("subida simultánea hasta tejado", raise_to(ROOF_R, ROOF_L, 4, 4), ['go_home']),
    ("subida con derecha 1 frame adelantada",
     raise_to(ROOF_R, ROOF_L, 4, 4, l_delay=1), ['go_home']),
    ("subida con derecha 2 frames adelantada (0.8 s)",
     raise_to(ROOF_R, ROOF_L, 4, 4, l_delay=2), ['go_home']),
    # Limitación conocida: si un brazo se adelanta >= confirm_frames (1.2 s),
    # sale antes start_tracking. Inocuo: go_home llega igual y control_node
    # termina en HOMING (desde IDLE o desde TRACKING).
    ("subida con derecha 3 frames adelantada (1.2 s)",
     raise_to(ROOF_R, ROOF_L, 4, 4, l_delay=3), ['start_tracking', 'go_home']),
    ("tejado visto de espaldas (izq/der intercambiados)",
     [pose(ROOF_R, ROOF_L, mirror=True)] * 3, ['go_home']),
    ("tejado sin nariz visible (fallback a hombros)",
     [pose(ROOF_R, ROOF_L, nose_vis=0.1)] * 3, ['go_home']),
    ("ambas manos arriba separadas (V) → nada",
     [pose((0.30, 0.10), (0.70, 0.10))] * 6, []),
    ("ambas manos sobre hombro pero bajo la nariz → nada",
     [pose((0.47, 0.25), (0.53, 0.25))] * 6, []),
    ("muñecas con visibilidad baja → nada",
     [pose(ROOF_R, ROOF_L, wrist_vis=0.3)] * 6, []),
    ("tejado y después mano derecha (tras cooldown)",
     [pose(ROOF_R, ROOF_L)] * 3 + [pose(DOWN_R, DOWN_L)] * 3 + [pose(UP_R, DOWN_L)] * 4,
     ['go_home', 'start_tracking']),
]


def main():
    fails = 0
    for name, frames, expected in CASES:
        got = run(frames)
        ok = got == expected
        fails += not ok
        print(f"[{'OK ' if ok else 'FALLO'}] {name}: {got}"
              + ("" if ok else f"  (esperado {expected})"))
    print(f"\n{len(CASES) - fails}/{len(CASES)} casos correctos")
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
