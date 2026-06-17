# Diario de progreso — TFM Person Follower

## Sesión 2026-06-17

### Estado al inicio
- Robot en nuc-224 (no nuc-225 como decían los docs antiguos), ROS_DOMAIN_ID=24 (no 25). Cámara HOG nunca detectaba (`cam: False` siempre).

### Causa raíz de la cámara — NO era el umbral
- Capturando frames reales de `/dev/video0` se vio que la cámara apuntaba al **techo** (robot estaba sobre una mesa, no en el suelo). Con el robot en el suelo, a la distancia normal (~1m) la persona quedaba recortada (sin cabeza/pies) — el HOG de OpenCV necesita ver el cuerpo entero para detectar. A ~2.5m con cuerpo completo, HOG detectó correctamente (confianza 0.76).
- `hog_min_weight` se bajó 0.40 → 0.25 igualmente (margen extra), pero el problema real era encuadre/distancia, no el umbral.

### Bug de software: kobuki_node no arrancaba con los 3 workspaces sourceados
- `ros2_ws/install` y `ros2_ws/build` tenían una copia **duplicada y obsoleta** de `kobuki_node`/`rplidar_ros` (compilada 2025-10-20, un día antes que la copia buena en `kobuki_ws`, 2025-10-21). Al hacer source de `kobuki_ws` + `ros2_ws` juntos, la copia vieja ganaba prioridad → `rclcpp::exceptions::RCLInvalidArgument: failed to create guard condition: context argument is null` al lanzar kobuki_node.
- Solución: `rm -rf ros2_ws/install/{kobuki_node,rplidar_ros} ros2_ws/build/{kobuki_node,rplidar_ros}` (build artifacts regenerables, no se tocó /src). `ros2_ws` ahora solo construye `person_follower`.

### Bug de hardware: RPLIDAR con timeout de conexión
- `SL_RESULT_OPERATION_TIMEOUT` repetido al lanzar rplidar_ros, anillo del LIDAR sin girar. Se resolvió desconectando y reconectando el cable USB del RPLIDAR (el dispositivo se re-enumeró correctamente, `health status: OK`, escaneando a 10Hz). Causa probable: mal contacto/alimentación tras el último apagado.

### MediaPipe instalado offline (mejora sobre HOG)
- HOG de OpenCV solo detecta con cuerpo completo en cuadro (inútil a la distancia real de seguimiento, ~1m). Se instaló MediaPipe Pose offline en el NUC (sin internet):
  - Wheels para Python 3.12 / manylinux2014_x86_64 descargados en labrob01 (`pip3 download mediapipe --python-version 312 --platform manylinux2014_x86_64 --only-binary=:all:`) y transferidos por scp.
  - `pip3 install --no-index --find-links=<wheels> mediapipe --break-system-packages` en el NUC.
  - El modelo `pose_landmark_lite.tflite` (~2.8MB) se descarga en runtime desde Google Cloud Storage y no está en el wheel — se descargó manualmente en labrob01 y se copió a `~/.local/lib/python3.12/site-packages/mediapipe/modules/pose_landmark/pose_landmark_lite.tflite` en el NUC.
  - Resultado: con persona moviéndose con normalidad, `/person_detected` (fusión LIDAR+cámara) se mantuvo en `true` 117/117 lecturas en una ventana de 15s (antes oscilaba constantemente).

### Pendiente verificado hoy
- FSM TRACKING↔IDLE sigue oscilando en algunos tramos incluso con detección fusionada estable — no se ha aislado la causa exacta todavía (podría ser independiente de la detección, revisar `control_node.py`/`tracking_node.py` timeouts internos).
- Explorar a futuro: `OrbbecSDK_ROS2` está en `ros2_ws/src` pero sin compilar — la cámara Orbbec Astra (RGBD) podría dar detección de persona más robusta que LIDAR 2D + webcam, pero es un cambio de arquitectura mayor, no abordado hoy.

---

## Sesión 2026-06-04

### Estado al inicio
- El robot seguía "a trompicones": movimiento errático, obstacle avoidance permanentemente saturado, posiciones outliers a 3-5m, FSM oscilando IDLE↔TRACKING constantemente.

### Cambios aplicados

#### detection_node.py
- Defaults alineados con config.yaml (dbscan_min_samples, min/max_leg_cluster_size, max_leg_radius, max_leg_distance)
- Fix interpolate_lidar_points: np.arange → np.linspace (evitaba mismatch por precisión float)
- Circularity filter relajado 0.3 → 0.15 (rechazaba piernas válidas)
- Filtro outliers: candidate_positions filtradas por max_detection_distance (2.5m)

#### tracking_node.py
- obstacle_threshold parametrizado (antes hardcoded 0.65m → ahora 0.35m desde config)
- Zona muerta angular ±8°: elimina micro-oscilaciones cuando la persona está enfrente
- Clamp derivada angular (±0.3): evita pico angular brusco tras pérdida de detección
- Acoplamiento wz-vx: menos giro cuando el robot avanza rápido
- Saturación wz reducida ±1.8 → ±1.0 rad/s
- Reset prev_angle en _stop(): arranque suave tras estado IDLE

#### config.yaml
- target_distance: 0.4 → 1.0m
- max_speed: 0.4 → 0.3 m/s
- obstacle_threshold: 0.35m (excluye estructura del robot)
- max_detection_distance: 2.5m (filtro outliers lejanos)
- detection_loss_frames: 4 → 8 (FSM más estable)
- kalman_q: 0.02 → 0.01 / kalman_r: 0.04 → 0.15 (posición más suave)

### Estado al final
- Robot sigue a la persona de forma estable a ~1m
- Oscilación angular reducida significativamente
- Sin saturación de obstacle avoidance
- FSM estable

---

## Pendiente — próximas sesiones

### Resuelto en sesión 2026-06-17
1. ~~**Cámara HOG no detecta**~~ — resuelto: causa real era encuadre/distancia, no umbral. MediaPipe instalado offline como mejora adicional (ver sesión 2026-06-17 arriba).

### Prioridad ALTA
2. **FSM TRACKING↔IDLE sigue oscilando en tramos**, incluso con detección fusionada estable. Revisar `control_node.py` (`tracking_loss_timeout`) y `tracking_node.py` (timeout interno de observación) — la causa podría no ser la detección en sí. Si la intermitencia LIDAR vuelve a ser sospechosa: probar bajar dbscan_eps de 0.12 a 0.10 o subir a 0.15, o bajar dbscan_min_samples de 4 a 3.

### Prioridad MEDIA
3. **Oscilación angular residual**
   - Si sigue molestando: bajar angular_gain de 1.2 a 0.8 en config NUC
   - O aumentar zona muerta de 8° a 12°

4. **Explorar Orbbec Astra (RGBD)** para detección de persona más robusta que LIDAR 2D + webcam — `OrbbecSDK_ROS2` ya está en `ros2_ws/src` pero sin compilar. Cambio de arquitectura mayor, no abordado todavía.

5. **Grabación de demostración**
   - Grabar vídeo del robot siguiendo para incluir en TFM
   - Usar `ros2 bag record` para grabar datos de los topics
