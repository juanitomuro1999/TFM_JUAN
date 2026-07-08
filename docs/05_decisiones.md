# Decisiones de diseño

> Registro de decisiones importantes: qué se decidió, por qué, y qué
> alternativas se descartaron. Complementa a `04_diario_desarrollo.md` (que
> es narrativo, para la memoria) con un registro corto y consultable.
> Entrada nueva arriba.

## 2026-06-17 — Migrar detección visual de HOG (OpenCV) a MediaPipe Pose

- **Decisión:** usar MediaPipe Pose (instalado offline en el NUC) como
  detector visual en `visual_detection_node`, en vez de HOG de OpenCV.
- **Motivo:** HOG solo detecta con el cuerpo completo dentro del encuadre,
  lo cual es inútil a la distancia real de seguimiento (~1 m) — el
  problema inicial se diagnosticó como encuadre/distancia, no como umbral
  mal ajustado (`hog_min_weight`). MediaPipe da landmarks corporales, lo que
  además habilita la detección de gestos (objetivo específico 1 del TFM),
  algo que HOG no puede dar.
- **Alternativas descartadas:** seguir bajando `hog_min_weight` (ya se
  probó, 0.40→0.25, y no resolvía el problema real de encuadre).

## 2026-06-04 — Reescalar parámetros de tracking para eliminar oscilación angular

- **Decisión:** reducir la saturación de velocidad angular (±1.8 → ±1.0
  rad/s), añadir zona muerta angular de ±8°, acoplar `wz` a `vx` (menos giro
  cuanto más rápido avanza el robot), y suavizar el filtro Kalman de
  posición (`kalman_q` 0.02→0.01, `kalman_r` 0.04→0.15).
- **Motivo:** el robot avanzaba "a trompicones" con oscilación angular
  constante y el FSM oscilaba IDLE↔TRACKING; se identificó que pequeñas
  variaciones de posición se traducían en giros bruscos sin filtrado
  suficiente.
- **Alternativas descartadas:** ninguna registrada — ajuste directo de
  parámetros tras diagnóstico.

---

*Sesiones posteriores a 2026-06-17 con cambios de parámetros o arquitectura
deberían añadir su entrada aquí, no solo en `PROGRESO.md`.*
