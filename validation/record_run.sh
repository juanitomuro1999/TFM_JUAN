#!/bin/bash
# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# record_run.sh — Graba una toma de validación experimental (rosbag2).
#   Ejecutar EN EL NUC (ssh user@10.48.0.1), con el sistema person_follower
#   ya lanzado y siguiendo a la persona. Solo necesita ROS 2 (no internet).
#
# Uso:
#   bash record_run.sh <etiqueta> [duracion_s]
#
#   <etiqueta>     nombre corto de la toma, p.ej. "recta_3m", "curva", "oclusion"
#   [duracion_s]   opcional; si se indica, para sola tras N segundos.
#                  Si se omite, graba hasta Ctrl-C.
#
# Ejemplos:
#   bash record_run.sh recta_3m 60      # 60 s de seguimiento en línea recta
#   bash record_run.sh curva            # graba hasta que pulses Ctrl-C
#
# Los bags se guardan en ~/tfm_bags/<fecha>_<etiqueta>/ (FUERA del repo, para
# no inflar git). Cópialos luego al portátil para analizarlos:
#   scp -r user@10.48.0.1:~/tfm_bags/<carpeta> .

set -e

# ── Entorno ROS (mismas rutas que scripts/launch_robot.bash) ─────────────────
source /opt/ros/jazzy/setup.bash
[ -f "$HOME/kobuki_ws/install/setup.bash" ] && source "$HOME/kobuki_ws/install/setup.bash"
source "$HOME/ros2_ws/install/setup.bash"
export ROS_DOMAIN_ID=24

ETIQUETA="${1:?Falta la etiqueta. Uso: bash record_run.sh <etiqueta> [duracion_s]}"
DURACION="${2:-}"

STAMP="$(date +%Y%m%d_%H%M%S)"
OUTDIR="$HOME/tfm_bags/${STAMP}_${ETIQUETA}"
mkdir -p "$(dirname "$OUTDIR")"

# ── Topics a grabar ──────────────────────────────────────────────────────────
# Curados para el análisis del Capítulo 7. /scan y /tf abultan; se incluyen para
# poder reproducir la toma en RViz y para SLAM/evo con TF. Quita /scan si solo
# quieres telemetría y trayectoria (bags mucho más ligeros).
TOPICS=(
  /follower/telemetry        # JSON: dist, angulo, velocidades, estado Kalman
  /odom                      # trayectoria del robot (para evo y gráfica de path)
  /commands/velocity         # comando de velocidad REAL enviado a la base
  /tracking/velocity_cmd     # comando crudo del tracking_node (antes de control_node)
  /person_position           # posicion observada de la persona (frame robot)
  /expected_person_position  # posicion filtrada por Kalman
  /person_detected           # bool deteccion (para analizar perdidas/oscilacion FSM)
  /gesture_command           # gestos start_tracking/stop_tracking (evidencia interaccion)
  /control/state             # estado FSM INIT/IDLE/TRACKING/MANUAL (arranque/parada del seguimiento)
  /control/mode              # AUTO/MANUAL (estado de la maquina de estados)
  /scan                      # LIDAR 2D (pesado; util para replay)
  /tf /tf_static             # transformadas (para evo/SLAM y replay)
)

echo "=========================================================="
echo " Grabando toma: ${STAMP}_${ETIQUETA}"
echo " Destino:       $OUTDIR"
[ -n "$DURACION" ] && echo " Duracion:      ${DURACION} s" || echo " Duracion:      hasta Ctrl-C"
echo " Topics:        ${#TOPICS[@]}"
echo "=========================================================="

# Comprobacion rapida de que hay datos antes de grabar
echo "[chk] /follower/telemetry ..."
timeout 4 ros2 topic hz /follower/telemetry 2>/dev/null | head -2 \
  || echo "  ⚠️  Sin telemetria — ¿esta el robot en TRACKING? (gesto start o camera_enabled:=False)"

CMD=(ros2 bag record -o "$OUTDIR" "${TOPICS[@]}")
if [ -n "$DURACION" ]; then
  timeout "$DURACION" "${CMD[@]}" || true
else
  "${CMD[@]}"
fi

echo ""
echo "✅ Grabacion terminada: $OUTDIR"
echo "   Tamaño: $(du -sh "$OUTDIR" 2>/dev/null | cut -f1)"
echo "   Siguiente paso (aqui o en el portatil):"
echo "     python3 validation/bag_to_csv.py $OUTDIR"
