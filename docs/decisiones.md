# Decisiones de diseño

> Registro de decisiones importantes: qué se decidió, por qué, y qué
> alternativas se descartaron. Complementa a `04_diario_desarrollo.md` (que
> es narrativo, para la memoria) con un registro corto y consultable.
> Entrada nueva arriba.

## 2026-07-09 — Métricas de saltos/saturación incorporadas al pipeline de validación (preparado sin robot, pendiente de re-ejecutar sobre bags reales)

- **Decisión:** `validation/bag_to_csv.py` ahora extrae `/person_position` y
  `/expected_person_position` a `position.csv`/`expected_position.csv` (ya se
  grababan en todos los bags vía `record_run.sh`, solo faltaba extraerlos).
  `validation/plot_run.py` añade a `metrics.txt`, cuando existe
  `position.csv`: `%` de saltos de posición cruda por encima de un umbral
  configurable (`--jump-threshold`, def. 0.8 m, entre muestras consecutivas)
  y `%` de saturación angular (`|vang| >= --sat-threshold`, def. 0.95) tanto
  global como restringido a instantes con posición cruda "estable" (sin
  variación mayor que `--stable-radius`, def. 0.15 m, en la ventana
  `--stable-window`, def. 1.0 s hacia atrás). Si `position.csv` no existe
  (bags generados con una versión anterior de `bag_to_csv.py`), el script
  degrada a un aviso en vez de fallar.
- **Motivo:** cerrar la limitación de reproducibilidad de `docs/07_resultados.md`
  §7.5 — las cifras de la tabla 7.4 (saltos 12.1%→0.7%, saturación
  94.5%→12.4%) se calcularon con un script *ad-hoc* de la sesión 2026-07-08
  (`bag_to_csv_direct.py`) que nunca se commiteó y ya no está disponible.
  Objetivo de la Sesión 3 de `docs/sesion_siguiente.md`.
- **Metodología nueva, no una reconstrucción del script perdido:** no hay
  forma de confirmar que el script ad-hoc definía "salto" o "posición
  estable" exactamente así — se documentan los umbrales elegidos y el motivo
  (0.8 m coincide con el que ya aparece citado en `PROGRESO.md`; el resto son
  elección propia razonable). **No asumir que las cifras nuevas coincidirán
  con las de la tabla 7.4** hasta re-ejecutar el pipeline sobre los tres bags
  de la sesión 08/07 (`validation/runs/20260708_movimiento_*`) y comparar.
- **Sin validar todavía:** esta sesión no tiene acceso a un entorno con ROS 2
  (`rclpy`/`rosbag2_py` no están instalados en este portátil), así que no se
  ha podido ejecutar `bag_to_csv.py` sobre los bags reales. La lógica de
  `plot_run.py` (saltos + saturación con estabilidad) se verificó con CSVs
  sintéticos construidos a mano (persona quieta con un salto espúreo
  intercalado + persona caminando de forma continua) — pendiente de
  confirmar con datos reales en una sesión con acceso al NUC o a una máquina
  con ROS 2 Jazzy instalado.
- **Alternativas descartadas:** recuperar el `bag_to_csv_direct.py` original
  (mencionado en `PROGRESO.md` como guardado en el scratchpad de otra sesión,
  no accesible desde aquí — y aunque se recuperase, seguiría sin estar
  commiteado ni integrado en el pipeline estándar, que era el problema de
  fondo). Definir "estable" sobre la salida ya filtrada por Kalman
  (`telemetry.csv: dist/angle_deg`) en vez de la posición cruda: se descartó
  porque el Kalman es precisamente lo que suaviza los saltos que se quiere
  medir, así que mediría la salida ya corregida, no el problema de entrada.

## 2026-07-09 — Alcance de Nav2 (objetivo 3): demo mínima completa (AMCL + navegación a un punto)

- **Decisión:** implementar Nav2 como demo mínima completa — AMCL
  localizando sobre `maps/mapa_laboratorio.yaml` + navegación a un único
  punto predefinido — en vez de documentarlo como trabajo futuro o limitarlo
  a solo localización. Preparado sin robot:
  [`person_follower/launch/nav2_localization_demo.launch.py`](../person_follower/launch/nav2_localization_demo.launch.py)
  (nuevo — antes no existía ningún launch file de Nav2) y
  [`scripts/nav2_send_goal.py`](../scripts/nav2_send_goal.py) (envía el
  objetivo con `nav2_simple_commander`).
- **Motivo:** cumplir el objetivo específico 3 tal como está planteado en
  `docs/01_introduccion.md`, no una versión recortada.
- **Estado real de partida (importante para valorar el riesgo):** antes de
  esta sesión, `person_follower/config/nav2_params.yaml` existía pero era un
  borrador explícitamente sin verificar (su propia cabecera: *"escrito sin
  acceso al robot"*, *"verificar en julio contra los defaults instalados en
  el NUC"*), **no existía ningún launch file de Nav2**, y **AMCL/Nav2 nunca
  se había ejecutado ni una sola vez** en el robot real. Es decir: se parte
  de cero, no de una integración a medio terminar.
- **Riesgo aceptado explícitamente:** a 2026-07-09 quedan sin cerrar del
  todo el objetivo 1 (gesto real por cámara, bloqueado por el encuadre de
  la C270), la validación aislada de `near_gain`, la prueba en robot del
  gate de continuidad (entrada de abajo), y el Capítulo 7 necesita
  repeticiones y arreglar su reproducibilidad (`docs/07_resultados.md`
  §7.5). Julio era el mes asignado a Nav2 en el plan original
  (`docs/01_introduccion.md` §1.4), así que este trabajo compite por tiempo
  de laboratorio con objetivos que ya tienen inversión real y datos. Se
  decidió asumir ese riesgo conscientemente en vez de recortar el alcance.
- **Mitigación de riesgo en la implementación:** el launch file separa
  explícitamente localización y navegación en dos grupos de lifecycle
  managers (patrón estándar de `nav2_bringup`, igual que ya usa
  `slam_toolbox.launch.py` con un único grupo) y su propia cabecera
  recomienda probar primero *solo* AMCL en RViz antes de añadir la pila de
  navegación completa — para poder cortar el alcance a "solo localización"
  sobre la marcha en el lab si el tiempo aprieta, sin haber tirado el
  trabajo de preparación.
- **Alternativas descartadas:** *Nav2 como trabajo futuro* (recomendado
  inicialmente por el análisis de riesgo — más seguro para el calendario,
  pero deja el objetivo 3 sin cumplir). *Alcance intermedio, solo AMCL sin
  navegación* (punto medio razonable, pero se descartó a favor de intentar
  el objetivo completo).
- **Simplificaciones deliberadas del demo** (documentadas en los propios
  archivos, no ocultas): no usa `velocity_smoother` (está en
  `nav2_params.yaml` pero se deja fuera para reducir piezas sin probar);
  corre independiente de `person_follower` — remapea `cmd_vel` directamente
  a `/commands/velocity`, sin integrar con `control_node`/`tracking_node`
  (esa integración "seguir → navegar a destino" es el objetivo específico 5,
  fuera de alcance aquí); **no lanzar a la vez que
  `start_person_follower.launch.py`**, ambos publicarían en
  `/commands/velocity`.

## 2026-07-09 — Confirmación por consistencia en el gate de continuidad (preparado sin robot, pendiente de validar en el lab)

- **Decisión:** `_gate_by_continuity` (`detection_node.py`) ahora exige
  `continuity_confirm_frames` scans consecutivos con un candidato
  *consistente* (repitiéndose en aprox. el mismo punto, tolerancia
  `position_jump_margin`) antes de aceptar un salto implausible como
  reanclaje real, en vez de aceptarlo en el primer scan. Nuevo parámetro en
  `config.yaml`, **por defecto `continuity_confirm_frames: 1`** (sin espera,
  idéntico al comportamiento anterior) — no cambia nada hasta que se suba a
  mano tras medir en el lab con qué frecuencia se activa este caso (punto 3
  de `docs/sesion_siguiente.md`).
- **Motivo:** era el punto pendiente explícito de la sesión 2026-07-08: el
  filtro de continuidad, cuando ningún candidato pasaba el gate de
  plausibilidad, se rendía y devolvía la lista sin filtrar — ahí se colaban
  los saltos residuales (máx. 1.84m observado). No se pudo probar en el
  robot en esta preparación (hecha fuera del laboratorio), así que se dejó
  parametrizado y verificado con pruebas de lógica aisladas (sin ROS), no
  con datos reales — **pendiente de validar con un rosbag antes de confiar
  en el comportamiento con `continuity_confirm_frames > 1`.**
- **Alternativas descartadas:**
  - *Contar solo "N scans seguidos con algo implausible", sin comprobar que
    fuera el mismo punto:* fue el primer diseño probado y falló su propio
    test de lógica — un cluster espurio distinto en cada scan (ruido, no una
    reaparición real) se habría aceptado igual al llegar a N, que es
    exactamente el caso que se quería filtrar. Se descartó en favor de exigir
    consistencia entre el candidato de un scan y el anterior.
  - *Aplicar el mismo gate de Mahalanobis del Kalman también en
    `detection_node`:* el Kalman ya actúa después de `detection_node` en la
    tubería (`tracking_node`), así que un segundo gate probabilístico
    equivalente aquí sería redundante; un filtro de distancia física simple
    es suficiente en esta capa y más fácil de razonar con los datos de
    validación ya existentes.

## 2026-07-08 — Filtro de continuidad, gate de Mahalanobis y rate-limit angular contra saltos de detección en movimiento

- **Decisión:** tres cambios encadenados tras la primera prueba de fusión
  CON movimiento (objetivo de la sesión):
  1. `detection_node`: gating por continuidad física (`_gate_by_continuity`,
     `max_person_speed=2.0 m/s`, `position_jump_margin=0.3 m`) — descarta
     candidatos (par de piernas o clúster de fusión) que impliquen una
     velocidad implausible respecto a la última posición publicada, salvo
     que ningún candidato pase el filtro (entonces se admite sin filtrar,
     para no bloquear una reaparición real tras pérdida larga).
  2. `tracking_node.KalmanTracker`: el gate de Mahalanobis (`mah2 > GATE*4`)
     ya no reancla el filtro con la primera observación lejana — exige
     `outlier_confirm=3` observaciones lejanas consecutivas antes de aceptar
     la reanclada; una observación aislada se descarta (se conserva la
     predicción).
  3. `tracking_node`: rate-limit a `wz` (`ang_acc_limit=0.3 rad/s/ciclo`),
     simétrico al `acc_limit` que ya tenía `vx` — impide que la velocidad
     angular salte de golpe a saturación en un solo ciclo de scan.
- **Motivo:** la prueba con movimiento (ver `PROGRESO.md`, sesión de hoy)
  reveló saltos de posición de 2-3.5 m en 80-260 ms (imposibles físicamente)
  y saturación angular (`|wz|=1.0`) el 94.5% del tiempo incluso con posición
  localmente estable. Causa raíz identificada en el código: (a)
  `detect_person` elegía el candidato leg-pair más cercano al robot sin
  comparar con la posición anterior, así que un cluster espurio (p.ej. patas
  de silla) más cercano ganaba la selección; (b) el propio gate de
  Mahalanobis, en vez de rechazar outliers, reiniciaba el filtro aceptándolos
  como verdad; (c) `wz` no tenía ningún limitador de cambio por ciclo, a
  diferencia de `vx`.
- **Resultado medido** (mismo tipo de toma, antes/después de los 3 cambios):
  saltos de posición >0.8 m: 12.1% → 0.7% de las muestras; saturación
  angular con posición estable: 94.5% → 12.4%; cambios bruscos de `wz`
  (>0.5 rad/s entre muestras): 0.2%. Detalle completo con las tres tomas
  intermedias en `PROGRESO.md`.
- **Alternativas descartadas:** rediseñar el uso del Kalman para que corrija
  siempre con menor peso en vez de gate binario (más correcto en teoría, pero
  cambio mayor de arquitectura fuera de alcance de la sesión); bajar
  directamente `angular_gain` sin rate-limit (habría suavizado la respuesta a
  errores angulares *reales* grandes, no solo a los espurios — el rate-limit
  ataca el síntoma exacto, el salto brusco, sin perder capacidad de girar
  fuerte si el error persiste varios ciclos).
- **Pendiente:** el filtro de continuidad tiene un fallback a "sin filtrar"
  cuando ningún candidato es plausible — siguen colándose saltos puntuales
  (máx. 1.84 m observado tras el fix). No se ha repetido la toma con
  mobiliario deliberadamente denso ni un recorrido largo (>2 min); ver
  `docs/sesion_siguiente.md`.

## 2026-06-25 — Fusión LiDAR-cámara por rumbo en vez de exigir par de piernas

- **Decisión:** cuando `detection_node` no encuentra un par de clústeres LiDAR
  compatible con dos piernas, usar el rumbo horizontal de la persona
  publicado por `visual_detection_node` (`/person_bearing`, derivado del
  punto medio de hombros de MediaPipe) para elegir el clúster general del
  LiDAR mejor alineado, en vez de dejar sin posición a `tracking_node`.
- **Motivo:** la causa raíz del seguimiento intermitente (FSM oscilando,
  pérdidas de detección) no era ruido de sensor, sino que la posición
  dependía estructuralmente de ver dos piernas — una persona quieta, con las
  piernas juntas o lejana nunca las generaba, y `tracking_node` agotaba su
  timeout de 30s sin que la cámara hubiera dejado de ver a la persona en
  ningún momento.
- **Alternativas descartadas:** subir el timeout de observación de
  `tracking_node` (habría enmascarado el síntoma sin resolver la causa: el
  robot seguiría sin posición real de la persona durante ese margen, solo
  tardaría más en notarlo). Relajar los parámetros DBSCAN para detectar pares
  de piernas con más facilidad (no soluciona el caso de piernas juntas o
  persona muy quieta, que es geométricamente indistinguible de una sola
  pierna para el LiDAR).

## 2026-06-25 — Reimplementar DBSCAN sobre scipy en vez de scikit-learn

- **Decisión:** eliminar la dependencia de `scikit-learn` en `detection_node`
  y reimplementar el algoritmo DBSCAN a mano sobre `scipy.spatial.cKDTree`.
- **Motivo:** el NUC tiene Python 3.12, pero la instalación de
  `scikit-learn` disponible traía la extensión compilada para cpython-3.10,
  lo que rompía el `import sklearn` con `ImportError`. Sin acceso a internet
  en el NUC no había forma de instalar una rueda (`wheel`) compatible con
  `pip`. Cualquier reinicio del NUC habría dejado `detection_node` sin poder
  arrancar.
- **Alternativas descartadas:** compilar `scikit-learn` desde fuente en el
  NUC (requiere toolchain de compilación y dependencias que tampoco estaban
  disponibles sin internet); descargar la wheel correcta en `labrob01` y
  transferirla por SCP (viable en teoría, pero más frágil a largo plazo que
  eliminar la dependencia — cualquier futura reinstalación del entorno
  volvería a tropezar con lo mismo). La reimplementación sobre `scipy`
  (que sí funciona en 3.12) se verificó idéntica al DBSCAN de sklearn en 200
  pruebas aleatorias antes de sustituirlo.

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
