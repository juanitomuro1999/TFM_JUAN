# Script de sesión — Prueba de seguimiento real + evaluación

> **Objetivo:** primera prueba completa y controlada de seguimiento de persona,
> grabación de datos y análisis cuantitativo con `evo`.
>
> **Duración estimada:** 90 min  
> **Requiere:** robot Kobuki encendido, batería cargada, persona de prueba

---

## BLOQUE 0 — Preparación local (PC, antes de ir al laboratorio)

```bash
# Sincronizar código local → robot (por si hubo cambios)
rsync -avz --exclude='__pycache__' ~/TFM_JUAN/person_follower/ \
  user@10.48.0.1:~/ros2_ws/src/person_follower/person_follower/

rsync -avz ~/TFM_JUAN/person_follower/config/ \
  user@10.48.0.1:~/ros2_ws/src/person_follower/config/

# Copiar config al build dir (OBLIGATORIO cada vez)
ssh user@10.48.0.1 'cp ~/ros2_ws/src/person_follower/config/config.yaml \
  ~/ros2_ws/build/person_follower/person_follower/config/config.yaml'

# Rebuild (solo si hubo cambios de código)
ssh user@10.48.0.1 '
  source /opt/ros/jazzy/setup.bash
  source ~/kobuki_ws/install/setup.bash
  cd ~/ros2_ws
  colcon build --symlink-install --packages-select person_follower 2>&1 | tail -3'
```

---

## BLOQUE 1 — Arranque del robot (≈ 5 min)

```bash
# 1. Verificar conectividad
ping -c 2 10.48.0.1

# 2. Lanzar todos los sensores en tmux automático
ssh user@10.48.0.1 '
  tmux kill-server 2>/dev/null; sleep 1
  tmux new-session -d -s tfm -n kobuki
  tmux new-window -t tfm -n lidar
  tmux new-window -t tfm -n tf
  tmux new-window -t tfm -n slam
  tmux new-window -t tfm -n follower
  tmux new-window -t tfm -n monitor

  LAUNCH="bash ~/TFM_JUAN/scripts/launch_robot.bash"
  tmux send-keys -t tfm:kobuki  "$LAUNCH kobuki"   Enter; sleep 6
  tmux send-keys -t tfm:lidar   "$LAUNCH lidar"    Enter; sleep 3
  tmux send-keys -t tfm:tf      "$LAUNCH tf"       Enter; sleep 3
  tmux send-keys -t tfm:slam    "$LAUNCH slam"     Enter; sleep 10
  tmux send-keys -t tfm:follower "$LAUNCH follower" Enter
'
```

---

## BLOQUE 2 — Verificación del sistema (≈ 3 min)

```bash
# Esperar ~25 s y verificar que todos los nodos están activos
sleep 25
ssh user@10.48.0.1 '
  export ROS_DOMAIN_ID=24
  source /opt/ros/jazzy/setup.bash
  source ~/ros2_ws/install/setup.bash

  echo "=== NODOS ACTIVOS ==="
  ros2 node list

  echo ""
  echo "=== FRECUENCIAS ==="
  timeout 5 ros2 topic hz /scan              2>&1 | grep "average rate" || echo "FALLO: /scan"
  timeout 5 ros2 topic hz /person_detected   2>&1 | grep "average rate" || echo "FALLO: /person_detected"
  timeout 5 ros2 topic hz /person_detected_visual 2>&1 | grep "average rate" || echo "SIN cámara"

  echo ""
  echo "=== PARÁMETROS CLAVE ==="
  ros2 param get /detection_node  max_leg_radius
  ros2 param get /detection_node  detection_confirm_frames
  ros2 param get /tracking_node   angular_d_gain
  ros2 param get /tracking_node   target_distance
'
```

**Valores esperados:**
| Topic/Param | Esperado |
|---|---|
| `/scan` Hz | ~13 Hz |
| `/person_detected` Hz | ~10 Hz |
| `/person_detected_visual` Hz | ~2.5 Hz |
| `max_leg_radius` | 0.15 |
| `detection_confirm_frames` | 3 |
| `angular_d_gain` | 0.3 |
| `target_distance` | 0.4 |

---

## BLOQUE 3 — Prueba de seguimiento (≈ 30 min)

### 3.1 Monitorizar en tiempo real

```bash
# Terminal A — Telemetría (distancia, ángulo, velocidades)
ssh user@10.48.0.1 '
  export ROS_DOMAIN_ID=24
  source /opt/ros/jazzy/setup.bash
  source ~/ros2_ws/install/setup.bash
  ros2 topic echo /follower/telemetry'

# Terminal B — FSM y detección
ssh user@10.48.0.1 '
  export ROS_DOMAIN_ID=24
  source /opt/ros/jazzy/setup.bash
  source ~/ros2_ws/install/setup.bash
  ros2 topic echo /control/mode'
```

### 3.2 Protocolo de prueba

**Prueba A — Detección frontal (validar ángulo)**
1. Robot parado, persona a **1.5 m delante** (ángulo ~0°)
2. Verificar en telemetría: `angle_deg` ∈ [-15°, +15°]
3. Verificar que `data: true` en `/person_detected`
4. Verificar que FSM pasa a `TRACKING`

**Prueba B — Seguimiento en línea recta (3 m)**
1. Persona camina hacia atrás lentamente (0.3 m/s)
2. Robot debe seguir manteniendo ~0.4 m de distancia
3. Verificar que `dist` ∈ [0.3, 0.6] m en telemetría
4. Verificar que `vlin` > 0 cuando `dist` > 0.5 m

**Prueba C — Giro (persona cambia de dirección)**
1. Persona gira 90° lentamente
2. Robot debe girar sin oscilaciones excesivas
3. Verificar que `angle_deg` converge a 0° en < 2 s

**Prueba D — Pérdida de detección (silla entre robot y persona)**
1. Poner silla brevemente entre robot y persona
2. Robot NO debe seguir la silla
3. Verificar que vuelve a seguir en < 2 s al quitar la silla

### 3.3 Señales de alerta durante la prueba

| Síntoma | Causa probable | Acción |
|---------|---------------|--------|
| `angle_deg` ≈ ±180° | Persona detrás del robot | Reposicionar al frente |
| `vlin` siempre 0 | FSM en IDLE | Verificar `/person_detected` |
| Oscilaciones de giro | Kd bajo | Subir `angular_d_gain` a 0.5 |
| Distancia no converge | Kp alto | Bajar `angular_gain` a 1.5 |
| Robot acelera brusco | `acc_limit` alto | Bajar a 0.03 |

---

## BLOQUE 4 — Grabación de datos (simultánea a Bloque 3)

```bash
# En el robot — rosbag completo
ssh user@10.48.0.1 '
  tmux new-window -t tfm -n bag
  tmux send-keys -t tfm:bag "
    export ROS_DOMAIN_ID=24
    source /opt/ros/jazzy/setup.bash
    source ~/ros2_ws/install/setup.bash
    SESION=sesion_$(date +%Y%m%d_%H%M)
    mkdir -p ~/bags
    ros2 bag record -o ~/bags/\$SESION \
      /scan /person_detected /person_detected_visual \
      /person_position /follower/telemetry \
      /cmd_vel /odom /control/mode /control/teleop_status \
      /clusters/legs /clusters/general
    echo \"Bag guardado: ~/bags/\$SESION\"
  " Enter'

# En local — CSV de telemetría (análisis offline rápido)
SESION=sesion_$(date +%Y%m%d_%H%M)
cd ~/datos_seguimiento/logs
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash  # si ROS está en local
export ROS_DOMAIN_ID=24
python3 record_telemetry.py $SESION &
echo "Grabando telemetría en telem_${SESION}.csv (Ctrl-C para parar)"
```

---

## BLOQUE 5 — Análisis post-sesión (≈ 20 min)

### 5.1 Análisis rápido con matplotlib

```bash
cd ~/datos_seguimiento
# Usar el CSV más reciente
LAST_CSV=$(ls -t logs/telem_sesion_*.csv | head -1)
echo "Analizando: $LAST_CSV"
python3 plots/analyze_session.py "$LAST_CSV"
# Genera: plots/SESION_overview.png (4 paneles)
xdg-open plots/*.png 2>/dev/null &
```

### 5.2 Evaluación de trayectoria con evo

```bash
# Bajar el bag del robot al local
LAST_BAG=$(ssh user@10.48.0.1 'ls -td ~/bags/sesion_* | head -1')
echo "Descargando bag: $LAST_BAG"
scp -r user@10.48.0.1:$LAST_BAG ~/datos_seguimiento/bags/

BAG_LOCAL=$(ls -td ~/datos_seguimiento/bags/sesion_* | head -1)

# Extraer odometría y calcular métricas APE
cd ~/datos_seguimiento
python3 plots/eval_with_evo.py "$BAG_LOCAL"
```

### 5.3 Métricas objetivo

| Métrica | Objetivo | Inaceptable |
|---------|----------|-------------|
| Distancia media robot-persona | 0.3 – 0.6 m | < 0.2 m o > 1.0 m |
| Tiempo en zona de confort | > 70% | < 50% |
| RMSE angular | < 15° | > 30° |
| Eventos de pérdida (> 2 s sin tracking) | < 3 | > 8 |

---

## BLOQUE 6 — Ajuste de parámetros (si es necesario)

Modificar directamente en el robot **sin rebuild** (parámetros ROS en caliente):

```bash
ssh user@10.48.0.1 'export ROS_DOMAIN_ID=24; source /opt/ros/jazzy/setup.bash; source ~/ros2_ws/install/setup.bash

# Ejemplo: robot oscila lateralmente → subir Kd
ros2 param set /tracking_node angular_d_gain 0.5

# Ejemplo: robot demasiado cerca → aumentar zona muerta
ros2 param set /tracking_node target_distance 0.5

# Ejemplo: robot tarda en confirmar persona → bajar umbral
ros2 param set /detection_node detection_confirm_frames 2

# Verificar cambio
ros2 param get /tracking_node angular_d_gain'
```

> ⚠️ Los cambios en caliente **no persisten** al reiniciar.
> Si un valor funciona bien, actualizarlo en `config/config.yaml` y commitear.

---

## BLOQUE 7 — Cierre de sesión

```bash
# 1. Parar grabaciones
#    - Ctrl-C en la ventana del bag del robot
#    - Ctrl-C en el grabador local de CSV

# 2. Guardar mapa actualizado (si el robot se movió)
ssh user@10.48.0.1 '
  export ROS_DOMAIN_ID=24
  source /opt/ros/jazzy/setup.bash
  source ~/ros2_ws/install/setup.bash
  ros2 run nav2_map_server map_saver_cli -f ~/maps/mapa_lab_$(date +%Y%m%d)'

# 3. Apagar sistema del robot
ssh user@10.48.0.1 'tmux kill-server'

# 4. Commitear cambios (parámetros ajustados + datos)
cd ~/TFM_JUAN
git add person_follower/config/config.yaml docs/04_diario_desarrollo.md
git commit -m "tune: parámetros sesión $(date +%Y-%m-%d) — [describir qué mejoró]

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push origin main

# 5. Commitear datos de telemetría
cd ~/datos_seguimiento
git add .
git commit -m "data: sesión $(date +%Y-%m-%d) — prueba seguimiento real"
# git push (si hay remote configurado)
```

---

## Checklist de sesión

```
PRE-SESIÓN
[ ] Batería Kobuki cargada
[ ] Código sincronizado al robot (rsync)
[ ] config.yaml copiado al build dir
[ ] Espacio libre en robot para bag (df -h ~)

DURANTE
[ ] Todos los nodos activos (node list ✅)
[ ] /scan a 13 Hz ✅
[ ] /person_detected a 10 Hz ✅
[ ] /person_detected_visual a 2.5 Hz ✅
[ ] FSM transiciona a TRACKING con persona delante ✅
[ ] Rosbag grabando ✅
[ ] CSV telemetría grabando ✅

PRUEBAS
[ ] A — Detección frontal: angle_deg ∈ [-15°, +15°] ✅
[ ] B — Seguimiento lineal: dist ∈ [0.3, 0.6] m ✅
[ ] C — Giro: converge en < 2 s ✅
[ ] D — Pérdida/recuperación: NO sigue silla ✅

POST-SESIÓN
[ ] Gráficas generadas con analyze_session.py ✅
[ ] Métricas evo calculadas ✅
[ ] Parámetros ajustados guardados en config.yaml ✅
[ ] Diario 04_diario_desarrollo.md actualizado ✅
[ ] Git commit + push ✅
```
