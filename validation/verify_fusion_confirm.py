#!/usr/bin/env python3
# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# verify_fusion_confirm.py — Verificación sintética, sin ROS, del fix de
# confirmación obligatoria para candidatos del fallback de fusión
# cámara+LIDAR (docs/sesion_siguiente.md, Sesión 4, "Arreglar confirmación
# en el fallback de fusión"; docs/decisiones.md, 2026-07-13/2026-07-16).
#
# Este portátil no tiene rclpy instalado (ver PROGRESO.md, sesión
# 2026-07-09), así que no se puede importar detection_node.py directamente
# (hace `import rclpy` a nivel de módulo). En su lugar, `FusionGateSim`
# replica EXACTAMENTE la lógica de los métodos nuevos/modificados de
# DetectionNode (_filter_by_drift, _confirm_fusion_candidate,
# _gate_by_continuity) — misma matemática, mismos nombres de parámetro.
# Si se toca esa lógica en detection_node.py, hay que replicar el cambio
# aquí también, o este script deja de verificar el código real.
#
# Pendiente de validar contra el nodo real (rosbag o robot en vivo) en la
# Sesión 4 de laboratorio — esto es solo lógica aislada.
#
# Uso:
#   python3 validation/verify_fusion_confirm.py

import numpy as np


class FusionGateSim:
    """Réplica mínima del estado y la lógica de gating de DetectionNode."""

    def __init__(self, max_person_speed=2.0, position_jump_margin=0.3,
                 continuity_window_s=1.0, continuity_confirm_frames=1):
        self.max_person_speed = max_person_speed
        self.position_jump_margin = position_jump_margin
        self.continuity_window_s = continuity_window_s
        self.continuity_confirm_frames = continuity_confirm_frames

        self._last_confirmed_pos = None
        self._last_position_time = None
        self._position_history = []  # [(t_seg, np.array[x,y])]
        self._continuity_reject_streak = 0
        self._pending_reanchor = None
        self._fusion_confirm_streak = 0
        self._fusion_pending_candidate = None

    # -- réplica de DetectionNode._filter_by_drift -------------------------
    def _filter_by_drift(self, positions, now_s):
        self._position_history = [(t, p) for t, p in self._position_history
                                   if now_s - t <= self.continuity_window_s]
        if not self._position_history:
            return positions
        window_t, window_ref = self._position_history[0]
        window_elapsed = now_s - window_t
        max_window_jump = self.max_person_speed * max(window_elapsed, 0.0) + self.position_jump_margin
        return [p for p in positions if np.linalg.norm(p - window_ref) <= max_window_jump]

    # -- réplica de DetectionNode._confirm_fusion_candidate (NUEVO) --------
    def confirm_fusion_candidate(self, candidate, now_s):
        if candidate is None:
            self._fusion_confirm_streak = 0
            self._fusion_pending_candidate = None
            return None
        if self._fusion_pending_candidate is not None and \
                np.linalg.norm(candidate - self._fusion_pending_candidate) <= self.position_jump_margin:
            self._fusion_confirm_streak += 1
        else:
            self._fusion_confirm_streak = 1
        self._fusion_pending_candidate = candidate
        if self._fusion_confirm_streak >= self.continuity_confirm_frames:
            return candidate
        return None

    # -- réplica de DetectionNode._gate_by_continuity (SIN CAMBIOS) --------
    def gate_by_continuity(self, positions, now_s):
        positions = self._filter_by_drift(positions, now_s)
        if not positions:
            return []
        if self._last_confirmed_pos is None or self._last_position_time is None:
            return positions
        elapsed = now_s - self._last_position_time
        max_jump = self.max_person_speed * max(elapsed, 0.0) + self.position_jump_margin
        last = self._last_confirmed_pos
        plausible = [p for p in positions if np.linalg.norm(p - last) <= max_jump]
        if plausible:
            self._continuity_reject_streak = 0
            self._pending_reanchor = None
            return plausible
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

    def confirm(self, xy, now_s):
        self._last_confirmed_pos = np.array(xy, dtype=float)
        self._last_position_time = now_s
        self._position_history.append((now_s, np.array(xy, dtype=float)))


def check(name, condition):
    status = "OK  " if condition else "FAIL"
    print(f"[{status}] {name}")
    return condition


def scenario_mueble_cuela_con_gate_by_continuity():
    """
    Reproduce el hallazgo de 2026-07-13 (docs/decisiones.md): con
    _gate_by_continuity (comportamiento ANTERIOR del camino de fusión), un
    mueble a 1.34m del último punto confirmado, tras 0.92s de hueco, cae
    dentro del radio "plausible" (2.0*0.92+0.3=2.14m) y se acepta en el
    primer scan, incluso con continuity_confirm_frames=3.
    """
    sim = FusionGateSim(continuity_confirm_frames=3)
    sim.confirm(np.array([0.0, 0.0]), now_s=0.0)
    mueble = np.array([1.34, 0.0])
    gated = sim.gate_by_continuity([mueble], now_s=0.92)
    return check(
        "Bug reproducido: _gate_by_continuity acepta el mueble en el primer scan (comportamiento anterior, ya no usado por fusión)",
        len(gated) == 1 and np.allclose(gated[0], mueble))


def scenario_mueble_no_cuela_con_confirm_fusion():
    """
    Mismo escenario (mueble a 1.34m tras 0.92s), pero con el mecanismo
    NUEVO (_confirm_fusion_candidate, continuity_confirm_frames=3): el
    mueble no debe aceptarse hasta el 3er scan consecutivo en el mismo
    sitio, ni siquiera aunque esté dentro del radio "plausible".
    """
    sim = FusionGateSim(continuity_confirm_frames=3)
    sim.confirm(np.array([0.0, 0.0]), now_s=0.0)
    mueble = np.array([1.34, 0.0])

    r1 = sim.confirm_fusion_candidate(mueble, now_s=0.92)
    r2 = sim.confirm_fusion_candidate(mueble, now_s=1.02)
    r3 = sim.confirm_fusion_candidate(mueble, now_s=1.12)

    ok = check("Scan 1 (0.92s): NO se acepta el mueble (streak 1/3)", r1 is None)
    ok &= check("Scan 2 (1.02s): NO se acepta el mueble (streak 2/3)", r2 is None)
    ok &= check("Scan 3 (1.12s): SÍ se acepta (streak 3/3, ya confirmado)",
                r3 is not None and np.allclose(r3, mueble))
    return ok


def scenario_ruido_no_se_repite():
    """
    Un cluster espurio de ruido que NO se repite en el mismo sitio entre
    scans (a diferencia de un mueble estático) nunca debe acumular racha,
    sin importar cuántos scans pasen.
    """
    sim = FusionGateSim(continuity_confirm_frames=3)
    sim.confirm(np.array([0.0, 0.0]), now_s=0.0)

    results = []
    t = 0.0
    rng = np.random.default_rng(42)
    for _ in range(20):
        t += 0.1
        candidate = np.array([1.0, 0.0]) + rng.uniform(-1.0, 1.0, size=2)
        results.append(sim.confirm_fusion_candidate(candidate, now_s=t))

    return check("Ruido disperso (posiciones aleatorias) nunca se confirma en 20 scans",
                all(r is None for r in results))


def scenario_persona_real_confirma_rapido():
    """
    Una persona real, cuya posición se repite de forma consistente entre
    scans (dentro de position_jump_margin), debe confirmarse en exactamente
    continuity_confirm_frames scans — sin retraso adicional ni bloqueo
    permanente.
    """
    sim = FusionGateSim(continuity_confirm_frames=3)
    sim.confirm(np.array([2.0, 0.0]), now_s=0.0)
    persona = np.array([2.05, 0.02])  # pequeño ruido de medida, dentro de margin=0.3

    t = 0.0
    accepted_at = None
    for i in range(1, 6):
        t += 0.1
        r = sim.confirm_fusion_candidate(persona, now_s=t)
        if r is not None:
            accepted_at = i
            break

    return check("Persona real (posición consistente) se confirma en el 3er scan, no antes ni después",
                accepted_at == 3)


def scenario_default_param_sin_cambio_de_comportamiento():
    """
    Con continuity_confirm_frames=1 (valor por defecto en config.yaml), el
    comportamiento debe ser idéntico al anterior: aceptar en el primer scan
    — el fix no debe introducir latencia si nadie sube el parámetro.
    """
    sim = FusionGateSim(continuity_confirm_frames=1)
    sim.confirm(np.array([0.0, 0.0]), now_s=0.0)
    persona = np.array([1.0, 0.0])
    r = sim.confirm_fusion_candidate(persona, now_s=0.5)
    return check("continuity_confirm_frames=1 (default): se acepta en el primer scan, sin retraso",
                r is not None and np.allclose(r, persona))


def scenario_leg_pairs_no_afectados():
    """
    _gate_by_continuity (camino de pares de piernas) no debe cambiar de
    comportamiento: sigue aceptando un salto plausible de inmediato.
    """
    sim = FusionGateSim(continuity_confirm_frames=3)
    sim.confirm(np.array([0.0, 0.0]), now_s=0.0)
    persona = np.array([1.5, 0.0])  # < max_person_speed*1.0 + margin
    gated = sim.gate_by_continuity([persona], now_s=1.0)
    return check("Pares de piernas: _gate_by_continuity sigue aceptando saltos plausibles al instante (sin cambios)",
                len(gated) == 1 and np.allclose(gated[0], persona))


if __name__ == "__main__":
    print("Verificación sintética — fix de confirmación en el fallback de fusión\n")
    all_ok = True
    all_ok &= scenario_mueble_cuela_con_gate_by_continuity()
    print()
    all_ok &= scenario_mueble_no_cuela_con_confirm_fusion()
    print()
    all_ok &= scenario_ruido_no_se_repite()
    print()
    all_ok &= scenario_persona_real_confirma_rapido()
    print()
    all_ok &= scenario_default_param_sin_cambio_de_comportamiento()
    print()
    all_ok &= scenario_leg_pairs_no_afectados()
    print()
    print("TODO OK" if all_ok else "HAY FALLOS")
    raise SystemExit(0 if all_ok else 1)
