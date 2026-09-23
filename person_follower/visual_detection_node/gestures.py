# Copyright 2026 Juan Muñoz Rovira
# SPDX-License-Identifier: Apache-2.0
#
# Clasificación geométrica de gestos sobre landmarks de MediaPipe Pose, sin
# dependencias de ROS: así se puede verificar con landmarks sintéticos
# (validation/verify_home_gesture.py) antes de tocar el robot real.
#
# Gestos (mutuamente excluyentes, como mucho uno por frame):
#   start_tracking → mano DERECHA levantada por encima del hombro (sola)
#   stop_tracking  → mano IZQUIERDA levantada por encima del hombro (sola)
#   go_home        → "tejado": ambas muñecas por encima de la cabeza y juntas
#
# Coordenadas normalizadas de MediaPipe: y crece hacia ABAJO, así que "por
# encima de" = y menor.

# Índices MediaPipe Pose
NOSE = 0
L_SHOULDER, R_SHOULDER = 11, 12
L_WRIST, R_WRIST = 15, 16
L_HIP, R_HIP = 23, 24


def classify_gesture(landmarks, min_visibility, margin_ratio,
                     roof_max_sep_ratio):
    """
    Devuelve (gesto, margin) con gesto en {'start_tracking', 'stop_tracking',
    'go_home', None}.

    landmarks: secuencia indexable de objetos con .x, .y, .visibility.
    roof_max_sep_ratio: separación horizontal máxima entre muñecas para el
    tejado, relativa a la altura del torso (hombro→cadera).
    """
    def lm(idx):
        p = landmarks[idx]
        return p if p.visibility >= min_visibility else None

    nose = lm(NOSE)
    l_shoulder, r_shoulder = lm(L_SHOULDER), lm(R_SHOULDER)
    l_wrist, r_wrist = lm(L_WRIST), lm(R_WRIST)
    l_hip, r_hip = lm(L_HIP), lm(R_HIP)

    scale = None
    if l_shoulder and l_hip:
        scale = abs(l_hip.y - l_shoulder.y)
    elif r_shoulder and r_hip:
        scale = abs(r_hip.y - r_shoulder.y)
    margin = scale * margin_ratio if scale else 0.05

    r_up = bool(r_wrist and r_shoulder and r_wrist.y < r_shoulder.y - margin)
    l_up = bool(l_wrist and l_shoulder and l_wrist.y < l_shoulder.y - margin)

    if r_up and l_up:
        # Ambas manos arriba: solo cuenta como tejado si las muñecas están
        # por encima de la cabeza y juntas. Nunca como start/stop, para que
        # el tejado no dispare también los gestos de una sola mano.
        head_y = nose.y if nose else min(l_shoulder.y, r_shoulder.y) - 2 * margin
        above_head = r_wrist.y < head_y and l_wrist.y < head_y
        max_sep = (scale if scale else 0.3) * roof_max_sep_ratio
        together = abs(r_wrist.x - l_wrist.x) < max_sep
        return ('go_home' if above_head and together else None), margin
    if r_up:
        return 'start_tracking', margin
    if l_up:
        return 'stop_tracking', margin
    return None, margin


class GestureDebouncer:
    """
    Exige confirm_frames frames consecutivos del MISMO gesto y un cooldown
    entre comandos emitidos. Cualquier frame con otro gesto (o ninguno)
    reinicia la racha.
    """

    def __init__(self, confirm_frames, cooldown_s):
        self.confirm_frames = confirm_frames
        self.cooldown_s = cooldown_s
        self.current = None
        self.streak = 0
        self._last_pub_t = None

    def update(self, gesture, now):
        """Devuelve el gesto a publicar en este frame, o None."""
        if gesture is not None and gesture == self.current:
            self.streak += 1
        else:
            self.current = gesture
            self.streak = 1 if gesture is not None else 0

        if gesture is None or self.streak < self.confirm_frames:
            return None
        if self._last_pub_t is not None and now - self._last_pub_t < self.cooldown_s:
            return None
        self._last_pub_t = now
        self.streak = 0
        return gesture
