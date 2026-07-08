# Decisiones de diseño

> Registro de decisiones importantes: qué se decidió, por qué, y qué
> alternativas se descartaron. Complementa a `04_diario_desarrollo.md` (que
> es narrativo, para la memoria) con un registro corto y consultable.
> Entrada nueva arriba.

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
