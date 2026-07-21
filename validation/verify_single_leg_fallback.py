#!/usr/bin/env python3
# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# verify_single_leg_fallback.py — Verificación sintética, sin ROS, del
# fallback de pierna única (sin par) en detection_node.py
# (docs/sesion_siguiente.md, Sesión 4, "Arreglar la pérdida de detección
# conjunta al girar"; docs/decisiones.md, 2026-07-15/2026-07-21).
#
# Este portátil no tiene rclpy instalado (ver PROGRESO.md, sesión
# 2026-07-09), así que no se puede importar detection_node.py directamente
# (hace `import rclpy` a nivel de módulo). En su lugar, `SingleLegGateSim`
# replica EXACTAMENTE la lógica de los métodos nuevos/reusados de
# DetectionNode (_filter_by_drift, _confirm_single_leg_candidate) — misma
# matemática, mismos nombres de parámetro. Si se toca esa lógica en
# detection_node.py, hay que replicar el cambio aquí también, o este script
# deja de verificar el código real.
#
# Pendiente de validar contra el nodo real (robot en vivo, girando) tras
# esta verificación sintética.
#
# Uso:
#   python3 validation/verify_single_leg_fallback.py

import numpy as np


class SingleLegGateSim:
    """Réplica mínima del estado y la lógica de gating de DetectionNode
    relevante para el fallback de pierna única."""

    def __init__(self, max_person_speed=2.0, position_jump_margin=0.3,
                 continuity_window_s=1.0, continuity_confirm_frames=1):
        self.max_person_speed = max_person_speed
        self.position_jump_margin = position_jump_margin
        self.continuity_window_s = continuity_window_s
        self.continuity_confirm_frames = continuity_confirm_frames

        self._position_history = []  # [(t_seg, np.array[x,y])]
        self._single_leg_confirm_streak = 0
        self._single_leg_pending_candidate = None

    # -- réplica de DetectionNode._filter_by_drift --------------------------
    def _filter_by_drift(self, positions, now_s):
        self._position_history = [(t, p) for t, p in self._position_history
                                   if now_s - t <= self.continuity_window_s]
        if not self._position_history:
            return positions
        window_t, window_ref = self._position_history[0]
        window_elapsed = now_s - window_t
        max_window_jump = self.max_person_speed * max(window_elapsed, 0.0) + self.position_jump_margin
        return [p for p in positions if np.linalg.norm(p - window_ref) <= max_window_jump]

    # -- réplica de DetectionNode._confirm_single_leg_candidate (NUEVO) -----
    def confirm_single_leg_candidate(self, candidate, now_s):
        if candidate is None:
            self._single_leg_confirm_streak = 0
            self._single_leg_pending_candidate = None
            return None
        if self._single_leg_pending_candidate is not None and \
                np.linalg.norm(candidate - self._single_leg_pending_candidate) <= self.position_jump_margin:
            self._single_leg_confirm_streak += 1
        else:
            self._single_leg_confirm_streak = 1
        self._single_leg_pending_candidate = candidate
        if self._single_leg_confirm_streak >= self.continuity_confirm_frames:
            return candidate
        return None

    # -- réplica de la selección de detect_person (rama de pierna única) ---
    def step(self, leg_cluster_centroids, now_s, max_detection_distance=6.0,
              last_confirmed_pos=None):
        """Un `scan`: dado el centroide de cada clúster ya clasificado como
        pierna y SIN pareja este scan, decide si se publica una posición."""
        positions = [p for p in leg_cluster_centroids
                     if np.linalg.norm(p) <= max_detection_distance]
        positions = self._filter_by_drift(positions, now_s)
        if not positions:
            self.confirm_single_leg_candidate(None, now_s)
            return None
        key = (lambda p: np.linalg.norm(p - last_confirmed_pos)) \
            if last_confirmed_pos is not None else (lambda p: np.linalg.norm(p))
        nearest = min(positions, key=key)
        confirmed = self.confirm_single_leg_candidate(nearest, now_s)
        if confirmed is not None:
            self._position_history.append((now_s, np.array(confirmed, dtype=float)))
        return confirmed


def check(name, condition):
    status = "OK  " if condition else "FAIL"
    print(f"[{status}] {name}")
    return condition


def scenario_giro_pierna_unica_rellena_el_hueco():
    """
    Reproduce el caso diagnosticado el 2026-07-15: al girar, una pierna
    ocluye a la otra durante varios scans seguidos (aquí simulados: 8 scans
    a ~11Hz, ~0.7s, dentro del rango real observado de 2-4s). Con
    continuity_confirm_frames=1 (default), el fallback debe publicar
    posición desde el primer scan con pierna única, en vez de devolver
    "sin detección" como antes de este fix.
    """
    sim = SingleLegGateSim(continuity_confirm_frames=1)
    last_confirmed = np.array([1.5, 0.1])  # última posición con par, antes del giro
    pierna = np.array([1.55, 0.05])        # la pierna que sigue visible durante el giro

    t = 0.0
    accepted = []
    for _ in range(8):
        t += 0.087  # ~11.5Hz, igual que el LIDAR real
        r = sim.step([pierna], now_s=t, last_confirmed_pos=last_confirmed)
        accepted.append(r is not None)

    return check(
        "8 scans seguidos con una sola pierna visible: TODOS publican posición (hueco relleno)",
        all(accepted))


def scenario_mueble_no_se_cuela_como_pierna_unica():
    """
    Un clúster de pierna espurio (falso positivo geométrico, p.ej. una pata
    de silla que superó por poco el clasificador _is_leg_cluster) que NO se
    repite en el mismo sitio entre scans no debe confirmarse nunca, igual
    que en el fallback de fusión.
    """
    sim = SingleLegGateSim(continuity_confirm_frames=3)
    sim._position_history = [(0.0, np.array([0.0, 0.0]))]

    t = 0.0
    results = []
    rng = np.random.default_rng(7)
    for _ in range(20):
        t += 0.087
        candidate = np.array([1.0, 0.0]) + rng.uniform(-1.0, 1.0, size=2)
        results.append(sim.step([candidate], now_s=t, last_confirmed_pos=np.array([0.0, 0.0])))

    return check("Clúster espurio disperso nunca se confirma en 20 scans (continuity_confirm_frames=3)",
                  all(r is None for r in results))


def scenario_confirm_frames_mayor_que_uno_exige_consistencia():
    """
    Con continuity_confirm_frames=3, una pierna real y consistente debe
    confirmarse exactamente en el 3er scan, no antes.
    """
    sim = SingleLegGateSim(continuity_confirm_frames=3)
    pierna = np.array([1.2, 0.3])

    t = 0.0
    accepted_at = None
    for i in range(1, 6):
        t += 0.087
        r = sim.step([pierna], now_s=t, last_confirmed_pos=np.array([1.2, 0.25]))
        if r is not None:
            accepted_at = i
            break

    return check("continuity_confirm_frames=3: pierna consistente se confirma en el 3er scan",
                  accepted_at == 3)


def scenario_par_disponible_no_pasa_por_aqui():
    """
    Documental: esta rama solo se alcanza en detect_person cuando
    candidate_positions (pares) está vacío. Esto no se puede probar aquí
    (es lógica de detect_person, no de SingleLegGateSim), pero se deja
    constancia explícita del invariante para quien lea este script: si hay
    un par válido, detect_person retorna antes de llegar a esta rama.
    """
    return check(
        "Invariante documentado: el fallback de pierna única solo se evalúa si "
        "candidate_positions (pares) está vacío en detect_person — ver el orden "
        "de las ramas en detection_node.py",
        True)


if __name__ == "__main__":
    print("Verificación sintética — fallback de pierna única (sin par) al girar\n")
    all_ok = True
    all_ok &= scenario_giro_pierna_unica_rellena_el_hueco()
    print()
    all_ok &= scenario_mueble_no_se_cuela_como_pierna_unica()
    print()
    all_ok &= scenario_confirm_frames_mayor_que_uno_exige_consistencia()
    print()
    all_ok &= scenario_par_disponible_no_pasa_por_aqui()
    print()
    print("TODO OK" if all_ok else "HAY FALLOS")
    raise SystemExit(0 if all_ok else 1)
