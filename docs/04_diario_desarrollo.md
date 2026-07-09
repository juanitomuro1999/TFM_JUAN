# Capítulo 4 — Diario de desarrollo

Registro cronológico del progreso técnico del TFM.

---

## Mayo 2026

### 21 de mayo — Puesta en marcha del robot (Fase 1 completa)

**Contexto:** primera sesión de trabajo con el robot real (nuc-225, 10.48.0.1).

**Trabajo realizado:**

1. **Revisión del repositorio:** se analizó la estructura completa del paquete `person_follower` heredado, identificando los siguientes problemas:
   - `setup.py` usaba `packages=[package_name]` en lugar de `find_packages()`, impidiendo que colcon encontrara los sub-paquetes.
   - `package.xml` declaraba `ament_cmake` como buildtool en lugar de `ament_python`.
   - Dependencias faltantes: `visualization_msgs`, `diagnostic_msgs`, `std_srvs`, `tf2_ros`, `numpy`, `sklearn`.
   - `collision_handling_node` y `slam_node` no registrados en `entry_points` de `setup.py`.
   - Doble suscripción a `/system_shutdown` en `tracking_node.py`.
   - Ruta hardcodeada de RViz en `user_interface_node.py`.

2. **Correcciones aplicadas:** todos los bugs anteriores fueron corregidos y compilados correctamente con `colcon build --symlink-install`.

3. **Conexión SSH al robot:** se accedió al NUC (nuc-225, Ubuntu 24.04, ROS 2 Jazzy) y se realizó un diagnóstico completo del entorno:
   - Dispositivos detectados: `/dev/kobuki` (ttyUSB1, FT232), `/dev/rplidar` (ttyUSB0, CP210x), cámara Logitech C270, cámara Orbbec Astra.
   - Workspaces existentes: `kobuki_ws` (Kobuki + RPLIDAR compilados), `ros2_ws` (person_follower versión anterior).

4. **Identificación de bugs en el robot:**
   - El `kobuki_node_params.yaml` apuntaba a `/dev/ttyUSB0` en lugar de `/dev/kobuki`.
   - El `launch_lidar.bash` usaba `ros2_ws/install` que no tenía `rplidar_ros` compilado; se corrigió a `kobuki_ws/install`.
   - Se detectaron dos instancias de `kobuki_ros_node` ejecutándose simultáneamente, con el proceso antiguo bloqueando el puerto del RPLIDAR.

5. **Lanzamiento exitoso de sensores:**
   - Kobuki: `Version info - Hardware: 1.0.4. Firmware: 1.2.0` — conectado.
   - RPLIDAR: `S/N: BAA2EDF9, Firmware 1.31, status OK, 10 Hz` — escaneando.
   - Topics activos verificados: `/scan`, `/odom`, `/commands/velocity`, `/tf`.

6. **Test de movimiento:** se publicó una velocidad de 0.1 m/s en `/commands/velocity` durante ~1 segundo. **El robot se movió correctamente.**

7. **Despliegue de la nueva versión:** el paquete `person_follower` (arquitectura multi-nodo, TFM_JUAN) fue copiado al robot y compilado exitosamente. Los 7 ejecutables fueron verificados con `ros2 pkg executables`.

**Estado al cierre de la sesión:**
- ✅ Fase 1 completada
- ✅ Robot operativo (Kobuki + RPLIDAR)
- ✅ Paquete person_follower v0.0.1 desplegado en el robot
- 🔄 Fase 2 iniciada: SLAM Toolbox en desarrollo

---

### 21 de mayo (continuación) — SLAM Toolbox operativo

**Diagnóstico del problema:**

El nodo `async_slam_toolbox_node` arrancaba pero no publicaba `/map`. Diagnóstico en el robot:
```
ros2 lifecycle list /slam_toolbox
```
El nodo se encontraba en estado `unconfigured` — es un **lifecycle node** de ROS 2 que requiere transiciones explícitas `configure → active` antes de operar.

**Causa raíz:** el `slam_toolbox.launch.py` original lanzaba el nodo sin gestión de ciclo de vida. El nodo esperaba ser configurado externamente.

**Solución aplicada:**

1. **Verificación manual:** se configuró y activó el nodo manualmente con:
   ```bash
   ros2 lifecycle set /slam_toolbox configure
   ros2 lifecycle set /slam_toolbox activate
   ```
   Confirmando que `/map` y `/map_metadata` empezaron a publicarse inmediatamente.

2. **Corrección del launch file:** se añadió un nodo `lifecycle_manager` (de `nav2_lifecycle_manager`) con `autostart: true` y `bond_timeout: 0.0`:
   - `autostart: true` — configura y activa `slam_toolbox` automáticamente al arrancar.
   - `bond_timeout: 0.0` — deshabilita el heartbeat de monitorización que `slam_toolbox` no implementa y que causaba un error de bond en los logs.

3. **Resultado:** log de lanzamiento limpio:
   ```
   [lifecycle_manager]: Configuring slam_toolbox
   [slam_toolbox]: Configuring
   [slam_toolbox]: Using solver plugin solver_plugins::CeresSolver
   [lifecycle_manager]: Activating slam_toolbox
   [slam_toolbox]: Activating
   [lifecycle_manager]: Managed nodes are active
   [slam_toolbox]: Registering sensor: [Custom Described Lidar]
   ```
   Topics publicados: `/map`, `/map_metadata`, `/slam_toolbox/feedback`, `/slam_toolbox/scan_visualization`, `/slam_toolbox/graph_visualization`.

**Estado al cierre:**
- ✅ SLAM Toolbox operativo: nodo activo, `/map` publicando
- ✅ `slam_toolbox.launch.py` corregido con lifecycle manager
- ✅ Mapa del laboratorio generado y guardado (ver sección siguiente)

---

### 21 de mayo (continuación) — Test del sistema person_follower completo

**Contexto:** con SLAM activo en el robot, se lanzó `bringup_full.launch.py slam_enabled:=false` para probar los 6 nodos del sistema de seguimiento.

**Bugs encontrados y corregidos:**

| Nodo | Bug | Corrección |
|------|-----|-----------|
| `visual_detection_node` | `import mediapipe` falla si no está instalado → crash | `try/except ImportError` + auto-desactivación con log de aviso |
| `visual_detection_node` | `publish_status()` llamado antes de crear el publisher (cuando `enabled=False`) | Publisher creado antes del check de `enabled` |
| `collision_handling_node` | Mismo bug: `publish_status()` antes del publisher | Igual que arriba |

**mediapipe no disponible en el robot:** el NUC-225 no tiene acceso a internet (pip y apt fallan). El `visual_detection_node` se desactiva automáticamente con un aviso y el sistema continúa en modo solo-LiDAR.

**sklearn no disponible:** igual, sin internet. Se descargaron los wheels en el PC local y se transfirieron vía SCP:
```bash
pip3 download scikit-learn --python-version 312 --platform manylinux2014_x86_64 --only-binary=:all: -d /tmp/sklearn_wheels/
sshpass -p 'qwerty' scp /tmp/sklearn_wheels/*.whl user@10.48.0.1:/tmp/
pip3 install /tmp/*.whl --break-system-packages  # en el robot
```

**Resultado del lanzamiento:**

| Nodo | Estado |
|------|--------|
| `detection_node` | ✅ Activo, detectando persona a 0.7–1.1m |
| `visual_detection_node` | ⚠️ Desactivado automáticamente (sin mediapipe) |
| `tracking_node` | ✅ Activo, publicando velocity_cmd |
| `control_node` | ✅ Activo, FSM IDLE→TRACKING |
| `collision_handling_node` | ✅ Activo, obstacle a 0.57m detectado |
| `user_interface_node` | ✅ Activo (RViz no carga en headless, no fatal) |

**Pipeline completo verificado:**
```
/scan → detection_node (DBSCAN) → /person_detected
→ control_node (FSM) → /tracking/velocity_cmd
→ /commands/velocity (Kobuki) @ ~10 Hz
```

**Ajustes en config.yaml:**
- `camera_enabled: False` — FSM entra en TRACKING automáticamente sin gesto (modo headless)
- `dbscan_min_samples: 5`, `min_leg_cluster_size: 5` — parámetros reducidos para detectar piernas a 0.5–2m con RPLIDAR A2M8 (57 pts/m de arco → ~5 pts por pierna a 1m)

**Estado:**
- ✅ Sistema person_follower completo probado en el robot real
- ✅ Detección LiDAR funcionando (DBSCAN con sklearn)
- ✅ FSM IDLE↔TRACKING funcionando
- ✅ Robot recibe velocidades de seguimiento (~10 Hz)
- 🔄 Pendiente: instalar mediapipe (necesita conexión o paquete offline)

---

### 27 de mayo — Sesión de integración completa (bugs críticos + cámara)

**Objetivo:** depurar el sistema completo con batería nueva tras la sesión anterior. El robot golpeaba la silla al intentar seguir.

#### Bugs críticos corregidos

**Bug 1 — `control_node`: callbacks de la FSM nunca se procesaban**

`wait_for_service()` llamaba a `rclpy.spin_once(self, timeout_sec=1.0)` dentro de `__init__`.
En ROS 2 Jazzy esto vincula el nodo a un executor temporal; cuando después `main()` llama a `rclpy.spin(node)`,
el nodo ya está asociado a otro executor y las callbacks nunca se ejecutan (fallo silencioso).

*Corrección:* sustituir `spin_once` por `time.sleep(0.5)` en el bucle de espera.

**Bug 2 — `control_node`: proceso muerto por Ctrl-C del proceso anterior**

Al lanzar con `ros2 launch`, el carácter `\x03` (Ctrl-C) que mató la sesión anterior quedaba en el
buffer del tty. El hilo de teclado lo leía, el driver enviaba SIGINT al nuevo proceso y `rclpy.spin()`
terminaba a los ~2.5 s.

*Corrección:* añadir `if not sys.stdin.isatty(): return` en `start_keyboard_listener()` para desactivar
el teclado cuando no hay terminal interactivo (como es siempre el caso con `ros2 launch`).

**Bug 3 — `detection_node`: persona nunca detectada**

Dos causas:
- `max_leg_radius = 0.05 m` demasiado pequeño para el RPLIDAR A2M8 interpolado (radio real: 0.03–0.12 m).
- `min_leg_cluster_size = 5` con comparación estricta (`> 5`) → requería ≥ 6 puntos.

*Corrección:* `max_leg_radius → 0.15 m`, `min_leg_cluster_size → 4` con `>=`.

**Bug 4 — Robot seguía sillas**

El detector no distinguía piernas de patas de silla (clusters similares en tamaño).

*Corrección A (multi-feature):* se añade `_cluster_features()` + `_is_leg_cluster()` con 6 filtros geométricos:
tamaño, radio, aspect ratio (< 4.5), dimensiones bounding box (< 0.30 m), circularity (> 0.3), scatter.

*Corrección B (persistencia temporal):* un objeto debe detectarse `detection_confirm_frames = 3` scans
consecutivos antes de "confirmar" a la persona, y `detection_loss_frames = 4` scans sin detección para
perderla. Las sillas estáticas generan detecciones intermitentes y quedan filtradas.

#### Mejoras en el modelo de seguimiento (tracking_node v3)

| Parámetro/Feature | Antes | Después |
|---|---|---|
| Kalman filter | 4-state (px, py, vx, vy) CV | 6-state (px, py, vx, vy, ax, ay) CA |
| Gate Mahalanobis | No | χ²(95%, 2DOF) = 5.991, reinit si > 4× |
| Control angular | Solo P (Kp=2.0) | PD (Kp=2.0, Kd=0.3) — amortigua oscilaciones |
| Rampa velocidad | Lineal | Adaptativa: `vel_ramp_exp=1.5` |
| Telemetría | Ninguna | `/follower/telemetry` JSON @10Hz |
| Predicción oclusión | No | Predicción Kalman si `obs_age > 0.3 s` |

#### Integración de cámara Logitech C270

- **Hardware verificado:** `/dev/video0` accesible, OpenCV 4.9.0 lo abre directamente.
- **Limitación:** MediaPipe no está instalado en el robot (sin internet → no `pip install`).
- **Solución:** `visual_detection_node` reescrito para usar el **detector HOG de OpenCV** (incluido en python3-opencv, sin dependencias externas).
  - Captura directa de `/dev/video0` en hilo independiente (~2.5 Hz).
  - Crop central del 70% del frame para evitar bordes ruidosos.
  - Umbral de confianza HOG configurable (`hog_min_weight: 0.40`).
  - Fallback automático a MediaPipe si en el futuro se instala.
  - No requiere `usb_cam` ni `cv_bridge`.
- **Publicación:** `/person_detected_visual` → fusión OR con LIDAR en `detection_node`.
- **Estado verificado:** nodo activo, publicando a 2.5 Hz, `enabled: True` en config.

#### Verificación del sistema completo

```
Nodos activos (12): /kobuki /rplidar_node /slam_toolbox /detection_node
                    /tracking_node /control_node /collision_handling_node
                    /visual_detection_node /user_interface_node
                    /lifecycle_manager_slam /static_transform_publisher ...
/scan:                  13.1 Hz ✅
/person_detected:       10.1 Hz ✅
/person_detected_visual: 2.5 Hz ✅ (HOG, C270)
FSM: IDLE → TRACKING al detectar persona ✅
```

**Estado al cierre de sesión:**
- ✅ Sistema estable — persona detectada, FSM transiciona correctamente
- ✅ Cámara C270 integrada vía HOG (sin MediaPipe)
- ✅ Robot no sigue sillas (filtro de persistencia + multi-feature)
- ✅ Control angular PD + Kalman 6-estado en producción
- 🔄 Pendiente: prueba completa de seguimiento real (persona caminando en línea recta)
- 🔄 Pendiente: instalar MediaPipe offline si se obtiene paquete wheel
- 🔄 Pendiente: evaluación cuantitativa con `evo` (RMSE trayectoria)

---

### 21 de mayo (continuación) — Corrección del movimiento a tirones

**Problema observado:** el robot se movía a tirones (arranques y parones repetidos) al seguir a una persona.

**Diagnóstico:** tres causas identificadas:

1. **FSM sin histéresis** — cualquier scan sin detección provocaba `TRACKING→IDLE→TRACKING` varias veces por segundo. Causa: `person_detected_callback` hacía la transición inmediatamente en cada mensaje.

2. **`tracking_node` paraba en cada fallo de scan** — la condición `if not person_detected: stop_robot()` actuaba antes de que el filtro de Kalman pudiera predecir la posición.

3. **`acc_limit = 0.005`** — la aceleración máxima era 0.05 m/s², tardando 16 segundos en alcanzar la velocidad de seguimiento; el robot nunca llegaba a velocidad antes del siguiente parón.

**Correcciones aplicadas:**

| Componente | Antes | Después |
|------------|-------|---------|
| `control_node` — histéresis | Transición IDLE inmediata al perder detección | `tracking_loss_timeout: 1.5 s` — espera antes de volver a IDLE |
| `tracking_node` — continuidad Kalman | Paraba al primer scan sin detección | Solo para si el timeout de posición (2 s) expira |
| `tracking_node` — aceleración | `acc_limit: 0.005` (0.05 m/s²) | `acc_limit: 0.05` (0.5 m/s²) |
| `tracking_node` — zona muerta | 10 cm | `target_distance: 0.4 m` |
| `tracking_node` — velocidad máxima | 0.8 m/s | `max_speed: 0.4 m/s` |

**Resultado verificado en logs del robot:**
- Antes: oscilaciones `TRACKING↔IDLE` cada ~200 ms
- Después: fases de TRACKING continuas de **11 s y 24 s**

**Estado al cierre de sesión (batería agotada):**
- ✅ Correcciones compiladas y desplegadas en el robot
- ✅ Fases de TRACKING estables confirmadas en log
- 🔄 Pendiente: prueba de seguimiento real en el laboratorio (sesión siguiente)

---

### 21 de mayo (continuación) — Mapa del laboratorio

**Movimiento de exploración:**

Con SLAM activo, se ejecutó una secuencia de movimiento autónoma desde el PC vía `/commands/velocity`:

| Paso | Movimiento | Duración | Distancia |
|------|-----------|----------|-----------|
| 1 | Adelante (0.2 m/s) | 3 s | ~0.6 m |
| 2 | Giro izquierda (0.4 rad/s) | 2 s | — |
| 3 | Adelante (0.2 m/s) | 3 s | ~0.6 m |
| 4 | Giro derecha (−0.4 rad/s) | 3 s | — |
| 5 | Adelante (0.2 m/s) | 2 s | ~0.4 m |

**Resultado del mapa (`/map_metadata`):**
- Resolución: 0.05 m/celda (5 cm)
- Tamaño: 261 × 338 celdas ≈ 13 × 17 metros
- Origen: (−8.32, −11.35) m

**Guardado con `map_saver_cli`:**
```
[map_io]: Received a 261 X 338 map @ 0.05 m/pix
[map_io]: Writing map occupancy data to mapa_laboratorio.pgm
[map_saver]: Map saved successfully
```

Archivos generados en `maps/`:
- `mapa_laboratorio.pgm` — imagen de ocupación (87 KB)
- `mapa_laboratorio.yaml` — metadatos (resolución, origen, umbrales)

**Estado:**
- ✅ Fase 2 completada: SLAM operativo + mapa del laboratorio guardado

---

## Junio 2026

### 4 de junio — Estabilización del seguimiento

Sesión de ajuste fino tras detectar movimiento errático ("a trompicones") y FSM oscilando IDLE↔TRACKING constantemente. Correcciones en `detection_node.py` (interpolación, filtro de circularidad) y `tracking_node.py` (zona muerta angular, clamp de derivada, acoplamiento wz-vx). Detalle completo en `PROGRESO.md`.

**Estado:** robot sigue de forma estable a ~1m, FSM estable.

### 17 de junio — Cámara HOG, MediaPipe y módulo de interacción por gestos

**Contexto:** la cámara no detectaba nunca (`cam: False` en todos los logs). Sesión de trabajo en el NUC real (renombrado `nuc-224`, `ROS_DOMAIN_ID=24` — los documentos antiguos referenciaban `nuc-225`/`25`).

**Diagnóstico de la cámara:** capturando frames reales de `/dev/video0` se confirmó que el problema no era el umbral de confianza HOG, sino el encuadre: el robot estaba sobre una mesa (cámara apuntando al techo) y, ya en el suelo, a la distancia normal de seguimiento (~1m) la persona quedaba recortada sin cabeza ni pies — el HOG de OpenCV necesita ver el cuerpo entero. A ~2.5m con cuerpo completo, detectó correctamente.

**Dos bugs adicionales encontrados y corregidos en la misma sesión:**
- `ros2_ws` contenía una copia duplicada y obsoleta de `kobuki_node`/`rplidar_ros` que rompía la inicialización de rclcpp al combinarse con `kobuki_ws` — eliminada (solo build artifacts).
- El RPLIDAR daba timeout de conexión por un problema de contacto USB — resuelto reconectando el cable.

**MediaPipe Pose instalado offline** en el NUC (sin acceso a internet, mediante wheels descargadas en `labrob01` y transferidas por SCP, incluyendo el modelo `pose_landmark_lite.tflite` que el paquete pip no incluye y se descarga en runtime). Mejora sustancial sobre HOG: detecta de forma fiable a la distancia real de seguimiento, donde HOG no podía. Con persona moviéndose con normalidad, la fusión LiDAR+cámara se mantuvo en detección positiva 117/117 lecturas en una ventana de 15s.

**Módulo de interacción por gestos implementado (Objetivo específico 1 del TFM):** `control_node.py` ya tenía toda la lógica de autorización por gesto (`/gesture_command` → `user_authorized`) lista desde el desarrollo original; faltaba la detección real del gesto. Se implementó en `visual_detection_node.py` usando los landmarks de MediaPipe Pose: mano derecha levantada por encima del hombro → `start_tracking`, mano izquierda → `stop_tracking`, con confirmación por frames consecutivos y cooldown anti-falsos-positivos. Validado en el robot real con correlación exacta entre el gesto detectado y la transición de la FSM.

**Estado al cierre:**
- ✅ Cámara funcionando (HOG a distancia adecuada + MediaPipe como mejora)
- ✅ Objetivo 1 (interacción por gestos) completado y validado
- ✅ Objetivo 2 (SLAM) ya completado en sesión de mayo
- 🔄 Pendiente (anotado, no abordado hoy): `tracking_node` satura el giro a corta distancia; FSM con oscilación residual en algunos tramos; explorar cámara Orbbec Astra (RGBD) sin compilar todavía en `ros2_ws/src`

### 25 de junio — Fusión LiDAR-cámara: causa raíz del seguimiento intermitente

**Diagnóstico:** la oscilación FSM y las pérdidas de seguimiento anotadas como pendientes el 17 de junio no eran ruido de la detección en sí, sino una limitación estructural: `detection_node` solo publicaba `/person_position` cuando el LiDAR encontraba un **par** de clústeres compatibles con dos piernas. Una persona quieta, con las piernas juntas, o a cierta distancia, no generaba ese par — sin posición, `tracking_node` agotaba su timeout de observación (30s) y dejaba de seguir, aunque la cámara siguiera viendo a la persona con normalidad.

**Solución — fusión por rumbo:** `visual_detection_node` calcula el rumbo horizontal de la persona a partir del punto medio de los hombros detectados por MediaPipe Pose y lo publica en `/person_bearing`. Cuando `detection_node` no encuentra un par de piernas, usa ese rumbo (convertido al frame del láser, con un signo de calibración `bearing_sign=-1.0` confirmado en vivo) para elegir el clúster general del LiDAR mejor alineado, y publica su centroide como posición de la persona. El sistema deja de depender de distinguir dos piernas para saber dónde está la persona.

**Bug de infraestructura no relacionado, pero crítico:** durante la sesión se descubrió que `scikit-learn` estaba roto en el NUC — Python 3.12 instalado, pero la extensión compilada disponible era para 3.10, así que cualquier `import sklearn` fallaba. Sin acceso a internet en el NUC no se podía resolver instalando una versión compatible. Se optó por eliminar la dependencia: el DBSCAN de `detection_node` se reimplementó de forma autocontenida sobre `scipy.spatial.cKDTree` (verificado idéntico al de sklearn en 200 pruebas aleatorias), dejando el stack robusto a reinicios del NUC.

**Primera validación experimental (Capítulo 7):** se construyó el pipeline de validación (`validation/`: grabar en el NUC → extraer CSV → graficar en el portátil) y se registró la primera toma, `fusion_track_20260625`, con el robot inhibido (sin movimiento, por seguridad al ser la primera prueba del mecanismo nuevo): 100% del tiempo con persona detectada, 0 pérdidas de detección, desviación del rumbo estimado frente al clúster elegido de ~6°. Al estar la base inhibida, la velocidad angular sale saturada en los datos y no permite evaluar el comportamiento de giro — eso queda para la siguiente sesión, con el robot en movimiento real.

**Estado al cierre:**
- ✅ Objetivo específico 4 del TFM (fusión sensorial) completado y validado sin movimiento
- ✅ Pipeline de validación experimental operativo, primeros datos para el Capítulo 7
- 🔄 Pendiente: validar la fusión y el `near_gain` con el robot moviéndose de verdad; decidir alcance de Nav2 (objetivo 3)

---

## Julio 2026

### 8 de julio — Validación con movimiento: saltos de detección y saturación angular

**Objetivo de la sesión:** completar la validación pendiente desde el 25 de
junio — probar la fusión LiDAR-cámara con el robot moviéndose de verdad, y
comprobar que `near_gain` doma el giro brusco a corta distancia.

**El gesto de activación no funcionó:** al intentar el gesto de mano derecha
para arrancar el seguimiento, la visibilidad MediaPipe de la muñeca se quedó
sistemáticamente por debajo del umbral necesario, y en los intentos donde sí
la superaba, levantar el brazo sacaba la muñeca/hombro del encuadre vertical
de la cámara C270. Diagnóstico con datos (no solo visual): `landmarks_visibles`
caía de 25 a 13 al levantar el brazo, y coordenadas `y` de hombro fuera del
rango [0,1]. Es una limitación física del montaje actual de la cámara, no un
problema de umbral ni de postura — pendiente de re-encuadrar en la próxima
sesión. Se activó TRACKING manualmente por SSH como workaround para poder
seguir con el objetivo real de la sesión.

**Lo que reveló la primera toma con movimiento:** el robot mostró exactamente
el comportamiento que describió el usuario tras la prueba — seguimiento
irregular, pérdidas frecuentes, giros bruscos. El análisis de la telemetría
grabada lo confirmó con números: la posición de la persona saltaba de golpe
2-3.5 metros en menos de 300 milisegundos (una velocidad imposible para una
persona caminando), y el robot respondía girando a velocidad angular máxima
el 70% del tiempo — incluso el 94.5% de las veces en que la posición
trackeada estaba, en apariencia, estable de un instante a otro.

**Causa raíz, leyendo el código con esos datos en la mano:** tres problemas
independientes se sumaban. `detection_node` elegía, entre los pares de
piernas candidatos del LiDAR, el más cercano al robot — sin comparar con
dónde había estado la persona el instante anterior, así que un objeto
cualquiera (una pata de silla, por ejemplo) más cercano que la persona real
podía ganar la selección. El filtro de Kalman de `tracking_node`, que en
teoría protege contra observaciones erráticas mediante un gate estadístico
(distancia de Mahalanobis), hacía justo lo contrario de lo esperado: en vez
de rechazar una observación demasiado alejada, reiniciaba el filtro
aceptándola como si fuera la nueva verdad. Y la velocidad angular comandada
al robot no tenía ningún limitador de cambio brusco por ciclo, a diferencia
de la velocidad lineal, que sí lo tenía desde la sesión del 4 de junio.

**La solución encadenó un arreglo en cada capa:** un filtro de continuidad en
`detection_node` que descarta candidatos con velocidad implícita físicamente
implausible; una corrección al gate de Mahalanobis para que exija varias
observaciones lejanas consecutivas antes de aceptar una reanclada real; y un
límite de aceleración angular simétrico al que ya tenía la velocidad lineal.
Cada cambio se verificó con una toma nueva antes de añadir el siguiente. El
resultado, medido: los saltos de posición pasaron de aparecer en 1 de cada 8
muestras a 1 de cada 140; la saturación angular con posición estable bajó
del 94.5% al 12.4%. Detalle completo, con las cifras de las tres tomas
intermedias, en `PROGRESO.md` y `docs/decisiones.md`.

**Estado al cierre:**
- ✅ Causa raíz de los saltos de detección y la saturación angular
  identificada y corregida, con mejora medida (no solo observada)
- ⚠️ Objetivo específico 1 del TFM (interacción por gestos) sigue sin validar
  en esta sesión — encuadre de cámara pendiente
- 🔄 Pendiente: repetir la validación de `near_gain` de forma aislada (la
  toma de hoy mezcló movimiento general); decidir alcance de Nav2

### 9 de julio — Reproducibilidad de las métricas de saltos/saturación (trabajo de escritorio)

**Sin acceso al laboratorio.** Primero se resolvió una duda de planificación
que llevaba tiempo latente: el usuario confirmó que no habrá acceso al
laboratorio en agosto, así que las 9 sesiones previstas para julio son todo
el tiempo de robot disponible antes del cierre del TFM, no "julio con margen
detrás" como asumía el reparto anterior. Se corrigió esa suposición en los
tres sitios donde aparecía (introducción, README, plan de la próxima
sesión) y se dejó una guía explícita de qué recortar primero si el tiempo
aprieta: Nav2, por ser el bloque que empieza de cero.

Con eso aclarado, se adelantó trabajo de escritorio de la Sesión 3 del plan:
las cifras de saltos de posición y saturación angular citadas en la tabla
de resultados del 8 de julio se habían calculado con un script improvisado
que nunca llegó a formar parte del repositorio, y que ya no está disponible
— una limitación de reproducibilidad pendiente desde entonces. Revisando qué
datos se graban realmente en cada toma de validación, resultó que la
posición cruda de la persona (`/person_position`) siempre se había estado
grabando; simplemente el script que convierte los bags a CSV nunca la
extraía. Con ese hueco cerrado, se añadió al pipeline de análisis (que corre
en el portátil, sin ROS) el cálculo automático de ambas métricas: el
porcentaje de saltos de posición por encima de un umbral, y el porcentaje de
saturación angular cuando la posición observada se mantiene estable en una
ventana reciente — con los umbrales elegidos documentados explícitamente,
porque no hay forma de confirmar que reproducen la definición exacta del
script perdido.

Esta sesión no tuvo acceso a una máquina con ROS 2 instalado, así que el
cambio se verificó de la única forma posible sin robot: construyendo a mano
un pequeño conjunto de datos sintético (una persona quieta con un salto de
detección espurio intercalado, y un tramo caminando de forma continua) y
comprobando que las métricas nuevas distinguían correctamente ambos casos.
Queda pendiente, para cuando haya acceso a una máquina con ROS, volver a
pasar el pipeline actualizado sobre los tres bags reales de la sesión del 8
de julio y comparar los números contra los ya publicados en la memoria.

**Estado al cierre:**
- ✅ Pipeline de análisis (`bag_to_csv.py` + `plot_run.py`) extiende
  `metrics.txt` con saltos de posición y saturación con posición estable,
  verificado con datos sintéticos
- 🔄 Pendiente: re-ejecutar sobre los bags reales del 8 de julio en cuanto
  haya acceso a una máquina con ROS 2, y actualizar la tabla de resultados
  si las cifras difieren de las ya publicadas

### 9 de julio (continuación, lab por la tarde) — El gesto real funciona: objetivo específico 1 conseguido

**Contexto:** con acceso al laboratorio ya avanzada la tarde, se decidió
atacar el bloqueante del gesto (pendiente desde el 8 de julio) con las
herramientas disponibles por SSH, en vez de esperar a la sesión de cámara
formalmente planificada. El diagnóstico del `[GESTO-DBG]` de la mañana ya
apuntaba a que la geometría del gesto era correcta pero la visibilidad de
MediaPipe, sobre todo en la muñeca izquierda, se quedaba justo al filo del
umbral. Bajar `gesture_min_visibility` de 0.6 a 0.5 fue suficiente para que
el gesto de parada empezara a dispararse. A mitad de sesión, el propio
usuario cambió la cámara Logitech C270 por una SPCA2650 que tenía a mano; la
visibilidad de la muñeca subió de forma notable con la cámara nueva. Con
ambos cambios, los gestos de inicio y parada se dispararon de forma repetida
y fiable en varias tomas grabadas — la primera vez que el objetivo
específico 1 del TFM (interacción por gestos) funciona de verdad, sin el
workaround manual publicando el comando por SSH.

**Un bug real, encontrado en directo:** con el gesto ya activando el
seguimiento, apareció un problema nuevo — con la persona completamente
quieta delante del robot, este se ponía a girar sin control, como dando
vueltas sobre sí mismo. Los datos del log no dejaban dudas: la posición
detectada de la persona barría un círculo casi completo alrededor del
robot en uno o dos segundos, algo físicamente imposible para alguien de
pie. Leyendo el código de `detection_node` con ese síntoma en la mano, la
causa quedó clara: el filtro que protege contra saltos de detección solo
comparaba cada candidato con el del instante inmediatamente anterior. Si
hay varios objetos parecidos a piernas muy cerca unos de otros —las cuatro
patas de una silla, por ejemplo— el filtro puede ir "caminando" de una pata
a la siguiente frame a frame, sin que ningún paso individual parezca
sospechoso, hasta trazar una vuelta completa a la sala. De hecho, en una de
las pruebas el propio usuario avisó de que el robot "se había liado con una
silla" antes incluso de que se revisara el log. La solución fue añadir un
segundo límite, independiente del anterior: además de no poder saltar mucho
respecto al frame previo, ningún candidato puede alejarse más de lo
físicamente plausible respecto a la posición confirmada de hace un segundo.
Sin acceso a una máquina con ROS en el portátil, la lógica se extrajo a un
script de prueba aislado y se verificó con varios escenarios construidos a
mano antes de desplegarla; la siguiente prueba en el robot confirmó que el
barrido había desaparecido.

**Un "arranque brusco" que resultó no ser un bug:** el usuario también
reportó que el robot arrancaba de forma muy agresiva al activar el
seguimiento. Aquí el hallazgo fue distinto: usando por primera vez en
vivo el pipeline de análisis preparado esa misma mañana (extrayendo el bag
directamente en el NUC, que sí tiene ROS, y trayendo los CSV al portátil),
los números mostraron que el ángulo hacia la persona en el instante de
activar el gesto era de casi 158 grados —prácticamente detrás del robot— y
que el limitador de aceleración angular ya implementado el 8 de julio
funcionaba exactamente como se diseñó, alcanzando la velocidad máxima de
forma gradual en unas tres décimas de segundo, no de golpe. No había ningún
fallo de control: el giro brusco era la respuesta correcta a un error de
orientación real y grande. Aun así, se añadió un arranque suave adicional
—un techo más bajo sobre la velocidad angular durante el primer segundo y
medio tras cada activación— para que la corrección inicial se sienta menos
agresiva incluso cuando el punto de partida es tan desfavorable. La
siguiente prueba salió, en palabras del usuario, "correctamente, sin ningún
fallo".

**Estado al cierre:**
- ✅ Objetivo específico 1 del TFM (interacción por gestos) funcionando de
  verdad con ambas manos, validado en varias tomas reales
- ✅ Bug de deriva acumulada en el gate de continuidad encontrado, corregido
  y validado en vivo
- ✅ Arranque suave añadido tras diagnosticar que el giro brusco era
  comportamiento correcto, no un fallo
- 🔄 Pendiente: oscilación de la FSM (ya conocida, reproducida varias veces
  hoy, sin resolver); recalibrar `camera_hfov_deg`/`bearing_sign` con la
  cámara nueva; aislar `near_gain`; decidir qué bags de hoy incorporar al
  Capítulo 7

---

## Julio 2026 (planificado)

### Fase 3 — Navegación autónoma (Nav2)

**Objetivos:**
- [ ] Configurar Nav2 con el mapa generado por SLAM Toolbox.
- [ ] Probar navegación a waypoints predefinidos en el laboratorio.
- [ ] Implementar comportamiento de guiado: seguir persona → navegar a destino.
- [ ] Evaluar planificador (NavFn vs Smac).

---

## Agosto 2026 (planificado)

### Fase 4 — Validación experimental

**Objetivos:**
- [ ] Diseñar escenario de evaluación en las instalaciones de la UJI.
- [ ] Métricas: tasa de detección, tiempo de respuesta, trayectoria real vs planificada.
- [ ] Evaluar robustez ante oclusiones y cambios de iluminación.
- [ ] Redactar sección de resultados.

---

## Septiembre 2026 (planificado)

### Fase 5 — Cierre

**Objetivos:**
- [ ] Revisión final del documento de TFM.
- [ ] Preparación de la presentación y defensa.
- [ ] Repositorio con tag `v1.0.0`.
