# Capítulo 6 — Implementación

## 6.1 Introducción y alcance

El Capítulo 2 describe la arquitectura del sistema a nivel de topología:
qué nodos existen, qué topics los conectan y qué hace cada uno en términos
generales. Este capítulo baja un nivel más y documenta **cómo** está
implementado cada nodo activo: algoritmos concretos, estructuras de datos,
fórmulas de control y las decisiones de código que no encajaban en una
descripción de arquitectura. Se apoya en el propio código fuente de
`person_follower/` y en los valores reales de `config.yaml`, no en una
descripción idealizada del sistema.

Una precisión importante antes de entrar en detalle: **no todos los
ficheros `.py` del paquete están en ejecución**. `setup.py` registra
exactamente siete nodos como `console_scripts` (§6.2); varios directorios
contienen además versiones anteriores del mismo nodo, conservadas en el
repositorio pero no registradas ni importadas por nada. Este capítulo
documenta el código que realmente se ejecuta; la Sección 6.11 explica el
código legado y por qué se mantiene en el repositorio.

## 6.2 Estructura del paquete y gestión de configuración

`person_follower` es un paquete ROS 2 `ament_python` con un directorio por
nodo. `setup.py` registra los siete ejecutables:

```python
entry_points={
    'console_scripts': [
        'control_node = person_follower.control_node.control_node:main',
        'visual_detection_node = person_follower.visual_detection_node.visual_detection_node:main',
        'detection_node = person_follower.detection_node.detection_node:main',
        'tracking_node = person_follower.tracking_node.tracking_node:main',
        'user_interface_node = person_follower.user_interface_node.user_interface_node:main',
        'collision_handling_node = person_follower.collision_handling_node.collision_handling_node:main',
        'slam_node = person_follower.SLAM_node.SLAM_node:main',
    ],
},
```

Todos los parámetros ajustables de cada nodo se centralizan en
`person_follower/config/config.yaml`, un fichero por nodo bajo la clave
`ros__parameters`, cargado por los `Node(...)` de los ficheros de
`launch/`. Esto permite cambiar cualquier umbral (distancias, ganancias,
tiempos de espera) sin recompilar — solo hace falta relanzar el stack, y
como el paquete se compila con `colcon build --symlink-install`, ni
siquiera hace falta recompilar tras editar un `.py` (§6.10). Cada parámetro
en `config.yaml` lleva un comentario con su racional y, en varios casos,
la fecha y el motivo del último cambio de valor — es, de facto, un segundo
registro de decisiones más granular que `docs/decisiones.md`, a nivel de
parámetro individual.

`person_follower/launch/start_person_follower.launch.py` es el launch
file principal y lanza cinco nodos: `control_node`, `tracking_node`,
`visual_detection_node`, `detection_node` y `user_interface_node`.
**`collision_handling_node` y `slam_node` no están incluidos** — el
primero porque `control_node` no reacciona todavía a `/collision_detected`
(§2.3.5); el segundo porque está desactivado por defecto y sustituido por
SLAM Toolbox en un launch file separado
(`person_follower/launch/slam_toolbox.launch.py`, Fase 2).

## 6.3 `detection_node` — clustering, features de pierna y gating

### DBSCAN propio sobre `cKDTree`

`dbscan_labels()` (módulo, no método de clase) reimplementa el algoritmo
DBSCAN sobre `scipy.spatial.cKDTree` en vez de usar `scikit-learn` — el
NUC solo tiene una build de `scikit-learn` compilada para Python 3.10,
incompatible con el Python 3.12 del sistema, sin forma de arreglarlo sin
acceso a internet (§2.3.1, `docs/decisiones.md`). La implementación sigue
la semántica estándar de sklearn (un punto es *core* si tiene
`dbscan_min_samples` vecinos dentro de `dbscan_eps`, incluyéndose a sí
mismo) usando `tree.query_ball_point` para la consulta de vecindad y una
expansión de clúster por BFS manual sobre una lista de semillas. Para los
cientos de puntos de un scan filtrado el coste es despreciable frente al
resto del pipeline.

Valores reales en `config.yaml`, calibrados a partir de la geometría real
del RPLIDAR A2M8 (a 1m, ~57 pts/m de arco; con interpolación ×2, ~114
pts/m → una pierna de 0.1m produce 10-12 puntos interpolados):
`dbscan_eps=0.12m`, `dbscan_min_samples=4`.

### Filtro geométrico multi-feature de piernas

`_cluster_features()` extrae ocho características de cada clúster
(`size`, `radius`, `scatter`, `width`, `height`, `aspect`, `circularity`,
`compactness`), con área y perímetro aproximados por la *bounding box* del
clúster (`circularity = 4π·área / perímetro²`, 1.0 = círculo perfecto).
`_is_leg_cluster()` aplica seis filtros secuenciales sobre esas
características (tamaño, radio medio, elongación, dimensión máxima,
circularidad mínima, dispersión máxima). El diseño está **inspirado en
`ros2_leg_detector` (mowito) y el `leg_detector` de ROS 1 (Spencer)**,
combinando el filtro original (más simple) del sistema heredado de la
Fase 1 con features adicionales para reducir tanto falsos positivos
(patas de mueble) como falsos negativos (piernas parcialmente ocluidas).
Dos de estos umbrales llevan una nota de `# BUG FIX` en `config.yaml`
(`max_leg_radius` pasó de 0.05 a 0.15m — el valor anterior rechazaba ~50%
de las piernas reales; `min_leg_cluster_size` pasó de una comparación
estricta `> 5` a `>= 4`), documentando que no son valores de diseño desde
el principio sino correcciones sobre errores del sistema heredado.

El emparejamiento de piernas (`detect_person()`) es un *nearest-neighbor
greedy* simple: para cada clúster de pierna sin emparejar, busca el
clúster de pierna más cercano dentro de `[min_leg_distance,
max_leg_distance]` = `[0.05, 0.35]` m, y los combina en un candidato de
posición (centroide del conjunto de ambos clústeres). No hay optimización
global de emparejamiento (tipo asignación húngara) — con un número bajo de
clústeres de pierna por scan en la práctica, el greedy es suficiente y
mucho más simple de razonar y depurar.

### Gating de continuidad y confirmación (ver también `docs/decisiones.md`)

Tres mecanismos de filtrado temporal, capa sobre capa, protegen contra
falsos positivos que superan el filtro geométrico:

1. **Persistencia temporal** (`_detect_streak`/`_loss_streak` en
   `lidar_callback`): una detección debe sostenerse `detection_confirm_frames`
   scans consecutivos para "confirmarse", y fallar `detection_loss_frames`
   consecutivos para "perderse" — evita que objetos estáticos con
   detección intermitente (sillas) disparen `/person_detected` a ráfagas.
2. **`_filter_by_drift()`**: descarta candidatos cuya distancia a la
   posición confirmada más antigua dentro de `continuity_window_s` (1.0s)
   supere `max_person_speed·Δt + position_jump_margin` — un filtro *duro*
   sobre la deriva acumulada, no solo el salto entre dos scans
   consecutivos, para atrapar cadenas de clústeres espurios adyacentes que
   "caminan" de uno a otro (p. ej. las patas de una silla).
3. **Confirmación por consistencia**, con dos implementaciones separadas
   desde 2026-07-16 (`docs/decisiones.md`): `_gate_by_continuity()` para
   candidatos de pares de piernas (exige confirmación solo cuando el
   candidato *no* es "plausible" por velocidad) y `_confirm_fusion_candidate()`
   para el fallback de fusión (exige confirmación **siempre**, incluso
   dentro del radio plausible — ver 6.3.1 más abajo). Ambos comparten el
   patrón de "racha": si el candidato más próximo se repite en
   aproximadamente el mismo sitio (`position_jump_margin`) durante
   `continuity_confirm_frames` scans consecutivos, se acepta; si cambia de
   sitio entre scans, la racha se reinicia a 1. Con el valor por defecto
   (`continuity_confirm_frames=1`) ambos mecanismos son un no-op —
   aceptan en el primer scan, igual que el sistema heredado de la Fase 1.

#### 6.3.1 Fallback de fusión y su confirmación dedicada

Cuando no hay par de piernas válido, `detect_person()` calcula el ángulo
esperado en el frame del láser a partir del rumbo de cámara
(`theta_target`, con el desfase de `π` del TF `base→laser` y el signo de
calibración `bearing_sign`), elige el centroide de clúster general con
menor desviación angular dentro de `fusion_angle_tol_deg` (25°), y —desde
el fix de 2026-07-16— exige que ese candidato se repita
`continuity_confirm_frames` scans consecutivos vía
`_confirm_fusion_candidate()` antes de publicarlo. Este camino usa estado
dedicado (`_fusion_confirm_streak`/`_fusion_pending_candidate`),
deliberadamente separado del estado del camino de piernas
(`_continuity_reject_streak`/`_pending_reanchor`), para que un candidato
de fusión rechazado no interfiera con una racha de confirmación de piernas
en curso, y viceversa (`docs/decisiones.md`, 2026-07-16). El motivo de
tratar la fusión de forma más estricta está en la propia naturaleza de la
señal: un par de piernas emparejado es una confirmación geométrica en sí
misma, mientras que un único clúster general elegido solo por alineación
angular con un rumbo de cámara es una señal más débil, con más margen para
que mobiliario cercano se cuele dentro del radio de velocidad "plausible"
(caso real documentado: mueble a 1.34m del último punto confirmado tras
0.92s de hueco de detección, dentro de un radio plausible de 2.14m).

### Convenio de frame en la frontera de publicación

`_publish_person_position()` invierte el signo de `x` e `y` justo antes de
publicar en `/person_position` (`Point(x=-xy[0], y=-xy[1])`). El resto del
nodo —gating, historial de posiciones, cálculo del fallback de fusión—
trabaja en el frame bruto del láser de este robot concreto, donde "delante
del robot" corresponde a un ángulo ≈π (confirmado en vivo el 2026-07-13:
persona delante a 1m publicaba `x=-1.18` antes del fix). `tracking_node`,
en cambio, asume el convenio estándar (delante = +x). Invertir el signo
solo en esta frontera de publicación evita tener que reescribir toda la
lógica interna de gating al frame estándar, a cambio de que cualquier
lectura directa de las variables internas del nodo (logs, depuración)
tenga que recordar que están en el frame bruto, no en el publicado.

## 6.4 `visual_detection_node` — detector dual y gestos

### Selección de detector con fallback automático

El nodo soporta dos detectores intercambiables, seleccionados en tiempo de
ejecución: **MediaPipe Pose** (si el paquete `mediapipe` está instalado y
`use_mediapipe=True`) o **HOG** de OpenCV (`cv2.HOGDescriptor` con el SVM
preentrenado de personas), como *fallback* automático si MediaPipe no está
disponible. La detección de qué backend usar ocurre por `try/except
ImportError` a nivel de módulo (`_CV2_OK`, `_MP_OK`), no por parámetro
obligatorio — el nodo se degrada solo si falta una dependencia, en vez de
fallar al arrancar. Con HOG no hay landmarks corporales, así que los
gestos (start/stop) **no están disponibles** en ese modo — el nodo lo
advierte explícitamente en el log al arrancar.

El detector HOG solo analiza el `hog_center_crop_ratio` (70%) central del
frame, para concentrarse en la dirección de marcha del robot y reducir
falsos positivos de los bordes de la imagen; acepta la detección si el
peso máximo de confianza de `detectMultiScale` supera `hog_min_weight`
(0.25 en la config actual). Es el detector heredado de la Fase 1,
sustituido como detector *principal* por MediaPipe Pose (§2.3.2,
§5.4) porque requería el cuerpo completo en el encuadre, inviable a la
distancia real de seguimiento (~1m) — pero se conserva como *fallback* sin
dependencias adicionales.

### Captura en hilo separado

`_capture_loop()` corre en un `threading.Thread` daemon independiente del
executor de ROS 2, con `cv2.VideoCapture` configurado con
`CAP_PROP_BUFFERSIZE=1` para descartar frames antiguos en el buffer del
driver de la cámara y procesar siempre el más reciente. Publica
`/person_detected_visual` a un ritmo acotado por `detection_interval`
(0.4s → ~2.5 Hz), con *throttling* activo: mide el tiempo real de
procesado de cada frame y solo duerme el resto del intervalo
(`max(0, detection_interval - elapsed)`), en vez de dormir el intervalo
completo sin descontar el coste de MediaPipe/HOG.

### Gesto y rumbo a partir de los mismos landmarks

`_check_gesture()` reutiliza los landmarks de MediaPipe Pose (hombros=11/12,
muñecas=15/16, caderas=23/24) para dos cosas distintas en la misma
llamada:

- **Gesto**: `start_tracking` si la muñeca derecha está por encima del
  hombro derecho (en coordenadas de imagen, `y` crece hacia abajo, así que
  "por encima" es `wrist.y < shoulder.y - margin`); `stop_tracking` con la
  muñeca izquierda. El margen no es un valor fijo en píxeles, sino
  proporcional a la escala del torso de la persona en el frame
  (`scale = |hip.y - shoulder.y|`, `margin = scale · gesture_margin_ratio`)
  — así el umbral se adapta a la distancia real de la persona a la cámara
  en vez de asumir un tamaño de torso fijo en píxeles. Requiere
  `gesture_confirm_frames` (3) consecutivos y respeta un
  `gesture_cooldown_s` (2.0s) entre comandos publicados, para no disparar
  gestos accidentales al caminar o gesticular.
- **Rumbo** (`beta`, para el fallback de fusión de `detection_node`,
  §6.3.1): punto medio de ambos hombros, `beta = (x_mid - 0.5) ·
  camera_hfov_rad`, publicado en `/person_bearing` solo si ambos hombros
  superan la visibilidad mínima.

Un log de diagnóstico dedicado (`[GESTO-DBG]`, a 1 Hz por
`throttle_duration_sec`) vuelca visibilidad y posición cruda de ambas
muñecas/hombros en cada frame — fue la herramienta que permitió
diagnosticar en vivo, el 2026-07-08/09, que el problema real del gesto no
detectado era encuadre/distancia y no el umbral de visibilidad (§1.2,
objetivo 1).

## 6.5 `tracking_node` — Kalman de 6 estados, control PD y evasión

Es, junto a `detection_node`, el nodo con más iteración documentada del
sistema (marcado explícitamente como "v3" en su cabecera). La versión
activa reemplaza un diseño anterior de 4 estados sin modelo de aceleración
(conservado como código legado, §6.11).

### Filtro de Kalman de 6 estados con modelo de aceleración constante

`KalmanTracker` mantiene el estado `x = [px, py, vx, vy, ax, ay]` (6
dimensiones, frente a las 4 —solo posición/velocidad— del diseño
heredado), con modelo de observación `H` que solo mide posición
(`OBS=2`). La matriz de transición `F(dt)` implementa un modelo de
aceleración constante (*constant acceleration*, CA):

```
px_{k+1} = px_k + vx_k·dt + ½·ax_k·dt²
vx_{k+1} = vx_k + ax_k·dt
ax_{k+1} = ax_k
```

(análogamente para `y`). El diseño está inspirado en la implementación de
9 estados (posición+velocidad+aceleración+yaw+ω) del proyecto
`LiDAR_Human_Tracker_ROS2`, simplificada a 6 estados porque el RPLIDAR 2D
no aporta orientación directa del objetivo (no hay `yaw`/`ω` que estimar
desde la percepción disponible). La matriz de ruido de proceso `Q(dt)`
tiene bloques correlacionados por potencias de `dt` (posición-posición
∝dt³/3, posición-velocidad ∝dt²/2, velocidad-velocidad ∝dt, aceleración
con un factor reducido ×0.2 para mantenerla más suave), siguiendo la
forma estándar de ruido de proceso para un modelo CA discreto. La
corrección usa la **forma de Joseph** (`P = (I-KH)·P_pred·(I-KH)ᵀ +
K·R·Kᵀ`) en vez de la forma simplificada `(I-KH)·P_pred`, más costosa pero
numéricamente más estable (garantiza que `P` se mantenga semidefinida
positiva incluso con errores de redondeo acumulados).

### Gate de Mahalanobis con confirmación por racha

Cada observación pasa por un gate de distancia de Mahalanobis
(`mah² = innᵀ·S⁻¹·inn`, con innovación `inn = z - H·x_pred` y covarianza
de innovación `S = H·P_pred·Hᵀ + R`) contra el umbral χ² al 95% para 2
grados de libertad (`MAHAL_GATE = 5.991`), pero con un margen adicional:
solo se rechaza una observación si `mah² > 4 · MAHAL_GATE`, y si
`outlier_confirm` (3) observaciones consecutivas caen fuera de ese umbral
ampliado, el filtro se reancla directamente a la última observación (se
asume una reaparición real, no ruido) en vez de seguir prediciendo sobre
un estado obsoleto indefinidamente. Una observación aislada muy alejada se
ignora (se conserva la predicción, no se incorpora la observación); una
racha sostenida de observaciones lejanas consistentes se trata como una
reaparición legítima. Esto es, en el espacio de estimación de Kalman, el
mismo patrón de "racha de consistencia" que `_gate_by_continuity()` y
`_confirm_fusion_candidate()` aplican en `detection_node` sobre los
candidatos crudos (§6.3) — dos capas independientes con la misma
filosofía de diseño, en dos nodos distintos.

### Controlador de velocidad angular: PD con zona muerta y atenuación

La velocidad angular no es un simple proporcional al error de rumbo. El
cálculo real, en orden:

1. **Corrección PD** con zona muerta de ±8°: dentro de la zona muerta solo
   actúa el término derivativo (`Kd·d_ang`, amortigua micro-oscilaciones
   sin generar giro neto); fuera de ella, `wz = Kp·(ang_err - zona_muerta)
   + Kd·d_ang`, con la derivada del error acotada a ±0.3 rad/ciclo para
   evitar un pico cuando la detección salta tras una oclusión.
   `ang_err = angle_to` (sin invertir) desde el fix del 2026-07-15 — ver
   el comentario extenso en el propio código, que documenta la
   verificación objetiva con `/odom` que llevó a revertir la inversión de
   signo introducida el 13/07 (`docs/decisiones.md`).
2. **Acoplamiento con la velocidad lineal**: `wz *= max(0.4, 1.0 -
   0.5·|vx|/max_speed)` — gira menos cuando el robot ya avanza rápido,
   evitando arcos de giro excesivamente amplios a alta velocidad lineal.
3. **Atenuación a corta distancia** (`near_gain = min(1.0, distance /
   target_distance)`): la sensibilidad angular del rumbo crece como
   `1/distancia`, y dentro de `target_distance` la velocidad lineal es
   prácticamente nula (el robot no avanza), así que sin este factor el
   robot giraría sobre sí mismo de forma errática al estar muy cerca de la
   persona. `near_gain` escala `wz` de 0 (pegado al objetivo) a 1.0 (a
   `target_distance` o más), sin impedir reorientarse, solo suavizando el
   giro cuando ya casi no hace falta.
4. **Arranque suave** (`startup_ramp_s`=1.5s, `startup_max_wz`=0.5): los
   primeros 1.5s tras activar el seguimiento, el techo de `|wz|` sube
   linealmente de 0.5 a 1.0 en vez de permitir ya el máximo — un error de
   rumbo grande justo al activar (persona casi detrás del robot) sigue
   corrigiéndose, pero de forma más lenta y previsible.
5. **Rate-limit final** (`ang_acc_limit`=0.3 rad/ciclo), simétrico al de la
   velocidad lineal (`acc_limit`): protege tanto de un error angular real
   y grande como de un salto puntual de detección que se cuele pese al
   resto de filtros.

La velocidad lineal sigue una **rampa no lineal**: `vx_objetivo =
max_speed · norm^vel_ramp_exp`, con `norm = min(1, distancia -
target_distance)` normalizado a una referencia de 1m y `vel_ramp_exp=1.5`
— más suave que lineal cerca de `target_distance`, evitando arranques
bruscos cuando la persona se aleja poco del umbral de seguimiento.

### Evasión de obstáculos reactiva (no DWA)

Pese a que el diagrama del Capítulo 2 y el README heredan la etiqueta
"Kalman + DWA" del diseño original, `tracking_node.py` **no implementa un
Dynamic Window Approach real** (simulación de trayectorias en el espacio
de velocidades admisibles, §5.8) — la implementación real de DWA vive en
un fichero separado, no registrado (`DWA.py`, §6.11). `_obstacle_avoidance()`
es un método reactivo más simple, de tipo campo de repulsión: para cada
punto del sector frontal ±50° dentro de `obstacle_threshold` (0.35m),
acumula un peso `w = (obstacle_threshold - r)·cos(ángulo)` que pondera más
los obstáculos más cercanos y más frontales; el ajuste angular final es la
media ponderada de `-ángulo` sobre esos puntos (empuja hacia el lado
contrario al obstáculo), acotado a ±1.5 rad/s, y el factor de reducción de
velocidad lineal decrece de 1.0 a un mínimo de 0.3 según la "amenaza"
acumulada. Es intencionadamente más barato computacionalmente que un DWA
completo (sin simular trayectorias candidatas), a costa de no razonar
sobre las restricciones cinemáticas del robot ni sobre el futuro a varios
pasos — suficiente para el caso de uso actual (evasión reactiva mientras
se sigue a una persona a baja velocidad, `max_speed=0.18` m/s), pero es
una simplificación real frente al DWA que sí se usará en Nav2 (Fase 3,
§5.8-5.9), y frente a la etiqueta que todavía lleva en los diagramas de
arquitectura — una inconsistencia de documentación pendiente de corregir
en el Capítulo 2.

## 6.6 `control_node` — máquina de estados finitos y teleoperación

La FSM (`INIT → IDLE ↔ TRACKING`, con `MANUAL` y `SHUTDOWN` alcanzables
desde cualquier estado activo) se implementa como una única clase con
`current_state` como cadena y `transition_to()` como único punto de
entrada para cambiar de estado — sin una librería de FSM ni una tabla de
transición declarativa, las condiciones de transición viven repartidas
entre los *callbacks* (`person_detected_callback`, `gesture_command_callback`)
y las propias acciones de `transition_to()` (activar/desactivar
`tracking_node` vía el servicio `enable_tracking`, parar el robot,
publicar el modo).

Dos mecanismos evitan comportamiento errático en los bordes de la FSM:

- **Histéresis en la pérdida de detección**: al perder a la persona en
  `TRACKING`, no se vuelve a `IDLE` inmediatamente — se espera
  `tracking_loss_timeout` (1.5s) de pérdida sostenida
  (`_lost_person_time`), evitando oscilar `TRACKING↔IDLE` ante
  parpadeos puntuales de detección.
- **Autorización por gesto independiente de la detección**:
  `user_authorized` (controlado por `gesture_command_callback`) y
  `person_detected` son dos variables separadas; la transición a
  `TRACKING` requiere ambas. Si `camera_enabled=False` en `config.yaml`,
  `user_authorized` se fija a `True` en el constructor y el sistema seguía
  automáticamente a la primera persona detectada, sin gesto — modo
  *headless* usado, entre otras cosas, cuando la cámara está calibrándose
  aparte.

### Teleoperación por teclado en un hilo aparte

`start_keyboard_listener()` lanza un hilo daemon que lee `/dev/tty` en
modo *cbreak* (sin buffering ni eco, vía `termios`/`tty`) para capturar
teclas sin bloquear el executor de ROS 2. El hilo se desactiva
automáticamente si `stdin` no es un terminal interactivo (detectado con
`sys.stdin.isatty()`) — necesario porque, al lanzar el stack vía `ros2
launch`, un Ctrl-C anterior puede quedar en el buffer del tty y ser leído
por el proceso nuevo como una señal inesperada; el comentario en el código
lo documenta como un fix concreto, no una precaución genérica. En modo
`MANUAL`, las teclas w/s/a/d/x publican velocidades fijas directamente a
`/cmd_vel` (0.5 m/s lineal, 0.8 rad/s angular — sin relación con los
límites de `tracking_node`, es control directo); `q` alterna
`MANUAL`↔automático; `p` inicia la secuencia de apagado coordinado
(§2.4).

## 6.7 `collision_handling_node`

El nodo más simple del sistema: un único umbral de distancia
(`min_distance = 0.4` m, hardcodeado, no expuesto como parámetro ROS) sobre
el mínimo de `scan.ranges`, publicando `/collision_detected` solo en los
flancos de cambio (no en cada scan). Como se indica en §6.2, no está
incluido en el launch principal y `control_node` no se suscribe a
`/collision_detected` — es infraestructura preparada para la Fase 3
(Nav2, que sí puede reaccionar a colisiones vía sus *recovery behaviors*)
pero sin cerrar el bucle todavía en el sistema de seguimiento de personas.

## 6.8 `user_interface_node`

No implementa lógica de percepción ni control — es un agregador de estado
para observabilidad. Se suscribe a los topics de estado de todos los demás
nodos (`/camera/status`, `/detection/status`, `/tracking/status`,
`/control/mode`, `/control/teleop_status`, `/person_detected`) y republica:

- **Markers de RViz 2** (`visualization_msgs/Marker`): esfera verde para
  la posición estimada de la persona (con el mismo cambio de signo que
  `detection_node`, `x=-msg.x`, porque consume `/expected_person_position`
  en el frame bruto), puntos para clústeres de piernas/generales
  (limitados a un refresco cada 0.5s para no saturar RViz), cilindro
  amarillo fijo para el robot, y un panel de texto HUD fijo frente al
  robot con seis líneas de estado (cámara, detección, tracking, persona
  sí/no, modo, teleop).
- **`/diagnostics`** (`diagnostic_msgs/DiagnosticArray`): solo se publica
  en el cambio de modo de control, no periódicamente.
- **Consola**: un temporizador a 5s (`display_status`) vuelca el estado
  actual, pero solo si cambió desde la última vez (`current !=
  self.previous_status`) — evita inundar el log con el mismo estado
  repetido.

También lanza `rviz2` como subproceso (`subprocess.Popen`) al arrancar,
con la configuración de `person_follower/config/user_interface.rviz` si
existe, y lo termina de forma coordinada al recibir `/system_shutdown`.

## 6.9 `slam_node` — SLAM propio (experimental, desactivado por defecto)

Implementación mínima de SLAM 2D: mantiene un `OccupancyGrid` propio como
matriz `numpy` (20×20m a 0.05m/celda, origen fijo en el centro), publica
una TF estática `map→odom` y actualiza el mapa a partir de `/scan` y
`/person_position`, sin un algoritmo de *scan matching* ni cierre de
bucles — es, esencialmente, un acumulador de ocupación sobre odometría
cruda, no un SLAM en el sentido de optimizar la propia trayectoria
estimada. Sustituido en la Fase 2 por **SLAM Toolbox** (§5.9) precisamente
por carecer de esas capacidades. Se conserva desactivado por defecto
(`enabled: False` es el único parámetro del nodo) como referencia
histórica del sistema heredado de la Fase 1, no como alternativa viable a
SLAM Toolbox.

## 6.10 Despliegue: lanzamiento y sincronización al robot

El paquete se compila en el NUC con `colcon build --symlink-install`
(§README), lo que crea enlaces simbólicos a los `.py` fuente en vez de
copias — el executor de ROS 2 recoge cambios en el código al **relanzar**
el nodo, sin necesitar recompilar. Esto es lo que permite el flujo de
trabajo de sincronización por `scp` documentado en
`docs/sesion_siguiente.md`.

`sync_nuc.sh`, en la raíz del repositorio, automatiza esa sincronización,
pero **solo para tres ficheros**:

```bash
scp tracking_node/tracking_node.py   $NUC:.../tracking_node/tracking_node.py
scp detection_node/detection_node.py $NUC:.../detection_node/detection_node.py
scp config/config.yaml               $NUC:.../config/config.yaml
```

Es decir: cualquier cambio en `visual_detection_node.py`, `control_node.py`,
`user_interface_node.py`, `collision_handling_node.py`, `SLAM_node.py` o
en los ficheros de `launch/` **no** se sincroniza automáticamente con este
script — hay que copiarlo a mano o extender el script. Es una limitación
real y no documentada hasta ahora fuera del propio script: los dos nodos
que sí cubre son los que han recibido más iteración en las últimas
sesiones (`detection_node`, `tracking_node`, ambos con el fix de fusión de
§6.3.1), lo cual explica por qué el script quedó acotado a esos tres
ficheros, pero no es una garantía para cambios futuros en el resto del
paquete.

## 6.11 Código no registrado en `setup.py`

Varios directorios de nodo contienen más de un fichero `.py` con una clase
de nodo completa, pero `setup.py` (§6.2) solo registra uno por nodo:

| Directorio | Activo (registrado) | No registrado (legado) |
|---|---|---|
| `control_node/` | `control_node.py` | `C_man.py`, `cierre_seguro.py` |
| `tracking_node/` | `tracking_node.py` (v3, Kalman-6 + PD) | `DWA.py` (DWA real con visualización de trayectorias en RViz) |
| `user_interface_node/` | `user_interface_node.py` | `UI_man.py` |

Ninguno de estos ficheros no registrados es importado por otro módulo del
paquete (verificado por búsqueda textual en todo el repositorio) — no es
código muerto por descuido, sino versiones anteriores de la misma clase
(mismo nombre, p. ej. `class TrackingNode(Node)` en ambos
`tracking_node.py` y `DWA.py`) conservadas en el árbol de trabajo en lugar
de eliminarse tras cada reescritura. `DWA.py` es particularmente relevante
para este capítulo porque implementa lo que la documentación de
arquitectura (Capítulo 2, README) todavía describe como el comportamiento
de `tracking_node` — una búsqueda real en el espacio de velocidades
`(v, w)` con funciones de coste de *heading*, *clearance* y velocidad, y
publicación de las trayectorias candidatas como `MarkerArray` para RViz —
mientras que el nodo realmente activo usa el controlador PD reactivo más
simple de §6.5. Mantener estos ficheros sin eliminar ni versionarlos con
un sufijo explícito (`_v1`, `_legacy`) es una fuente real de confusión —
ya lo fue para este propio capítulo, al tener que verificar contra
`setup.py` cuál era el código activo antes de documentarlo — y una
limpieza razonable (eliminar o mover a un directorio `legacy/` con
`README` propio) para dejar el repositorio en un estado más claro de cara
a la entrega final del TFM.
