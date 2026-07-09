# Diario de progreso — TFM Person Follower

## Sesión 2026-07-08

### Objetivo: prueba de fusión CON movimiento (validar `near_gain`)

Robot lanzado en nuc-224 (kobuki + rplidar + stack completo), sin incidencias
de hardware (RPLIDAR arrancó limpio, sin el timeout USB histórico).

### Gesto de activación: no utilizable esta sesión (encuadre de cámara)

El gesto de mano derecha no se detectó de forma fiable: la visibilidad
MediaPipe de la muñeca se mantuvo por debajo de `gesture_min_visibility=0.6`
la mayor parte del tiempo, y en los intentos donde sí superaba el umbral, al
levantar el brazo la muñeca/hombro se acercaban o salían del borde superior
del encuadre (`landmarks_visibles` cayó de 25 a 13, hombro estimado con `y`
negativo = fuera de frame). No es un problema de postura del usuario, es un
límite físico del encuadre vertical de la C270 en su montaje actual —
pendiente de re-inclinar/reposicionar la cámara, fuera de alcance de hoy.
**Workaround usado**: activar TRACKING publicando manualmente
`ros2 topic pub /gesture_command std_msgs/msg/String "{data: 'start_tracking'}"`
por SSH. Válido para las pruebas de hoy, pero el gesto real sigue sin
funcionar de cara al TFM.

### Primera toma con movimiento: reveló saltos de detección + saturación angular

Bag `movimiento_20260708` (ventana real de seguimiento ~130s, tras filtrar el
tiempo previo de depuración del gesto): FSM oscilando TRACKING↔IDLE 24 veces
en 130s, sólo 56.9% detección, saltos de posición de 2-3.5m en 80-260ms
(físicamente imposibles), y `v_ang` saturado a ±1.0 rad/s el 70% del tiempo
(94.5% incluso con posición localmente estable). Reporte inicial del usuario
("seguimiento irregular, se pierde, giros bruscos") confirmado con datos, no
solo de oído.

### Causa raíz y fix — ver detalle completo en `docs/decisiones.md`

Tres cambios encadenados, cada uno verificado con una toma nueva:
1. `detection_node`: filtro de continuidad anti-salto (rechaza candidatos
   con velocidad implícita implausible respecto a la última posición).
2. `tracking_node.KalmanTracker`: el gate de Mahalanobis ya no reancla con
   una sola observación lejana — exige 3 consecutivas.
3. `tracking_node`: rate-limit a `wz` (antes solo `vx` lo tenía).

**Progresión medida** (saltos >0.8m / saturación con posición estable):
- Original: 12.1% saltos / 94.5% saturación
- +fix 1: 2.2% saltos / 72.2% saturación
- +fix 2 y 3: **0.7% saltos / 12.4% saturación**

Detección subió de 71.7% a 82.6% entre la toma del fix 1 y la de los fixes
2+3 (efecto colateral positivo: menos saltos → Kalman más estable → FSM
pierde menos el track).

### Notas técnicas

- Para analizar bags en el portátil hizo falta convertir de mcap a sqlite3
  en el propio NUC (`ros2 bag convert`) — el portátil solo tenía ROS2 Humble
  con el plugin mcap, y el metadata.yaml de rosbag2 escrito por Jazzy usa un
  formato de QoS (strings tipo `history: unknown`) que el parser yaml-cpp de
  Humble no entiende. Con sqlite3 tampoco bastaba: el mismo problema de
  metadata.yaml aparecía al leerlo con `rosbag2_py`. Se esquivó leyendo la
  base sqlite3 directamente (tablas `topics`/`messages`) con un script ad-hoc
  (`bag_to_csv_direct.py`, en el scratchpad de esta sesión, no en el repo)
  que reutiliza la lógica de `validation/bag_to_csv.py` sin pasar por el
  metadata.yaml problemático.
- `sync_nuc.sh` tiene una ruta de destino de `config.yaml` que no existe
  (`/home/user/ros2_ws/src/person_follower/config/config.yaml` — la ruta real
  es `.../person_follower/person_follower/config/config.yaml`, duplicado en
  el propio script). Falla ese `scp` puntual pero no bloquea el resto; revisar
  si se usa `sync_nuc.sh` en vez de scp manual.
- El build en el NUC usa `--symlink-install`: `build/person_follower/...` es
  un symlink a `src/person_follower/...`, así que sincronizar con `scp` a los
  paths de `src/` dentro de `~/ros2_ws/src/person_follower/` basta — no hace
  falta recompilar ni `colcon build` para que el stack recoja cambios de
  código al relanzar el launch.
- El mensaje de `/gesture_command` publicado manualmente con
  `ros2 topic pub --once` no queda grabado en el rosbag pese a que
  `control_node` sí lo recibe (confirmado dos veces, en dos tomas distintas)
  — probablemente una condición de carrera de descubrimiento DDS específica
  de `--once`. Sin investigar más a fondo; no bloquea nada, solo hace que
  `gestures.csv` no sea fiable para ver activaciones manuales.

### Pendiente para la próxima sesión

- **Re-encuadrar/inclinar la cámara C270** para que el gesto de mano derecha
  sea utilizable sin el workaround manual — objetivo específico 1 del TFM
  depende de esto funcionando de verdad en vivo.
- El filtro de continuidad tiene fallback a "sin filtrar" cuando ningún
  candidato es plausible — siguen colándose saltos puntuales (máx. 1.84m
  observado tras el fix). Probar con mobiliario deliberadamente denso cerca
  y un recorrido más largo (>2 min) para ver si el fallback se activa mucho.
- Repetir la validación de `near_gain` específicamente (girar a corta
  distancia, ~0.5-0.7m) ahora que el ruido de fondo (saltos/saturación) está
  mayormente resuelto — la toma de hoy mezclaba movimiento general, no aisló
  ese caso.
- Decidir alcance de Nav2 (objetivo 3): sigue pendiente, no tocado hoy.

---

## Sesión 2026-06-25

### Causa raíz del fallo de seguimiento
- La posición de la persona dependía solo de que el LiDAR detectara un **par de piernas** (DBSCAN + emparejamiento). Una persona quieta, con las piernas juntas o lejana no generaba par válido → sin `/person_position` → `tracking_node` agotaba el timeout de observación (30s) → dejaba de seguir, aunque la cámara sí veía a la persona.

### Fusión cámara+LiDAR (solución elegida)
- `visual_detection_node` publica `/person_bearing` (Float32, rad): rumbo horizontal de la persona desde el punto medio de los hombros de MediaPipe, `beta = (x_mid - 0.5) * camera_hfov_deg` (51° del C270).
- `detection_node`, cuando NO encuentra par de piernas, ejecuta un fallback de fusión: convierte el rumbo al frame del láser (`theta = wrap(pi + bearing_sign*beta)`) y elige el clúster general mejor alineado (tolerancia 25°, distancia ≤4m), publicando su centroide como `/person_position`. Da posición aunque no se distingan dos piernas.
- Parámetros nuevos en `config.yaml`: `camera_hfov_deg`, `fusion_enabled`, `fusion_angle_tol_deg`, `fusion_max_distance`, `bearing_sign` (-1.0, calibrado en vivo), `bearing_timeout`.

### Fix crítico de infraestructura: sklearn roto en el NUC
- El NUC solo tiene Python 3.12, pero la instalación de `scikit-learn` disponible traía la extensión compilada para cpython-3.10 → `ImportError` al importar DBSCAN. Sin internet no se podía arreglar con pip; cualquier relanzamiento o reinicio habría hecho crashear `detection_node`.
- Eliminada la dependencia de sklearn: DBSCAN reimplementado de forma autocontenida sobre `scipy.spatial.cKDTree` (numpy+scipy sí funcionan en 3.12). Verificado idéntico al DBSCAN de sklearn en 200 pruebas aleatorias.

### Infraestructura de validación (Capítulo 7)
- `validation/test_nomotion.launch.py`: lanza el stack completo pero redirige `/cmd_vel` a `/cmd_vel_inhibited` → la base NO se mueve (pruebas de percepción/logging sin riesgo).
- `validation/bag_to_csv.py` + `validation/plot_run.py`: extraen rosbag2 a CSV/TUM y generan gráficas + `metrics.txt` (error de distancia MAE/RMS, error angular medio, % detección, pérdidas). Ver `validation/README.md` para el pipeline completo (grabar en NUC → analizar en portátil).

### Primera toma de validación: `fusion_track_20260625` (sin movimiento)
- 23.5s, 285 muestras de telemetría, 100% tiempo con persona detectada, 0 pérdidas de detección.
- `bearing_sign = -1.0` confirmado: el clúster LiDAR elegido coincide con el rumbo de la cámara con ~6° de desviación.
- `cmd_vel.csv` = 0 filas: confirma que el robot no se movió (seguridad OK).
- Nota: la velocidad angular sale saturada en esta toma porque la base está inhibida y nunca llega a girar; el comportamiento real de giro debe evaluarse en la prueba CON movimiento (pendiente, ver `docs/sesion_siguiente.md`).

### Pendiente para la próxima sesión
- **Prueba CON movimiento** (objetivo principal): validar que `near_gain` doma el giro brusco a corta distancia — en la toma sin movimiento no se puede juzgar el giro porque `vang` sale saturada. Plan detallado en `docs/sesion_siguiente.md`.
- Decidir alcance de Nav2 (objetivo 3): demo mínima (AMCL + mapa ya guardado) vs. documentarlo como trabajo futuro.
- Repetir tomas de validación (2-3 rosbags) para tener datos suficientes para el Capítulo 7.

---

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

### Módulo de interacción por gestos implementado (Objetivo específico 1 del TFM)
- `control_node.py` ya tenía toda la lógica de `/gesture_command` → `user_authorized` lista desde antes; lo que faltaba era la detección real del gesto en `visual_detection_node.py` (el publisher existía pero nunca se usaba).
- Implementado en `visual_detection_node.py` (`_check_gesture`, llamado desde `_detect_mp`): mano DERECHA levantada por encima del hombro (con margen relativo al torso) → `start_tracking`; mano IZQUIERDA levantada → `stop_tracking`. Requiere `gesture_confirm_frames` (3) consecutivos y un `gesture_cooldown_s` (2.0s) entre comandos para evitar falsos positivos.
- Requiere MediaPipe (no funciona con HOG, que no da landmarks) — ya está instalado desde hoy.
- `camera_enabled` en `config.yaml` activado a `True` (antes `False`, modo headless sin gesto).
- **Validado en el robot real**: ambos gestos se detectaron y aplicaron correctamente, con correlación exacta entre el log `[GESTO]` y la transición de la FSM (`>> TRACKING` / `>> IDLE`).
- Causa de un susto durante la prueba: tras probar "start" no se probó "stop" inmediatamente después; al volver a detectarse a la persona la FSM volvió sola a TRACKING (comportamiento esperado de la FSM, no del gesto) y el robot avanzó girando fuerte porque la persona estaba muy cerca (ver pendiente de tracking más abajo). Se cortó al instante publicando `stop_tracking` manualmente. **Lección operativa: siempre dar el gesto de stop (o alejarse) al acabar una prueba de gestos.**

### Pendiente de refinar (NO tocar la lógica de tracking todavía — anotado para sesión dedicada)
- **`tracking_node` gira al máximo (±1.0 rad/s) mientras avanza a velocidad casi máxima cuando la persona está muy cerca**, dando la sensación de que el robot "da vueltas sobre sí mismo". Sospecha: el ángulo de rumbo (bearing) se vuelve muy sensible a pequeños desplazamientos laterales a corta distancia, saturando el control angular. Revisar en sesión dedicada a tracking, no ahora.

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

### Resuelto en sesión 2026-06-25
2. ~~**FSM TRACKING↔IDLE oscilaba / pérdida de detección con persona quieta**~~ — causa raíz encontrada y resuelta: dependía solo del par de piernas del LiDAR. Fallback de fusión por rumbo de cámara (`/person_bearing`) implementado y validado sin movimiento (100% detección, 0 pérdidas). Ver sesión 2026-06-25 arriba y `docs/decisiones.md`.

### Prioridad ALTA (siguiente sesión)
3. **Prueba de fusión CON movimiento** — validar que `near_gain` doma el giro brusco a corta distancia; la toma del 25/06 fue sin movimiento (`vang` saturada, no evaluable). Plan detallado en `docs/sesion_siguiente.md`.

### Prioridad MEDIA
4. **Oscilación angular residual** (si reaparece tras la prueba con movimiento)
   - Si sigue molestando: bajar angular_gain de 1.2 a 0.8 en config NUC
   - O aumentar zona muerta de 8° a 12°

5. **Explorar Orbbec Astra (RGBD)** para detección de persona más robusta que LIDAR 2D + webcam — `OrbbecSDK_ROS2` ya está en `ros2_ws/src` pero sin compilar. Cambio de arquitectura mayor, no abordado todavía.

6. **Grabación de demostración**
   - Grabar vídeo del robot siguiendo para incluir en TFM
   - Usar `ros2 bag record` para grabar datos de los topics
