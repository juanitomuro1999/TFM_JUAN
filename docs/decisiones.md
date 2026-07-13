# Decisiones de diseño

> Registro de decisiones importantes: qué se decidió, por qué, y qué
> alternativas se descartaron. Complementa a `04_diario_desarrollo.md` (que
> es narrativo, para la memoria) con un registro corto y consultable.
> Entrada nueva arriba.

## 2026-07-13 — Vectorizar apply_median_filter en detection_node (fix de rendimiento)

- **Decisión:** reemplazar el bucle Python de `apply_median_filter`
  (`detection_node.py`, una llamada a `np.median` por punto del scan) por
  `scipy.ndimage.median_filter`, recalculando a mano solo los `window_size//2`
  puntos de cada borde (que `scipy` rellena por defecto con `mode='nearest'`,
  distinto del recorte sin relleno del original) para reproducir el
  comportamiento exacto.
- **Motivo:** perfilado en vivo (`top`) mostró `detection_node` consumiendo
  93.7% de un core del NUC. Un script standalone en el propio NUC (mismo
  tamaño real de scan, n=1080) aisló la causa: el pipeline completo de
  `detect_person` tardaba 80.2ms de los 87.7ms disponibles entre scans a
  11.4Hz (91% de duty cycle), y `apply_median_filter` por sí sola se llevaba
  56.5ms (70% del total) — sin margen para picos de carga.
- **Verificación:** 500 pruebas sintéticas (`window_size` y tamaños de array
  variados) + caso real (n=1080, window=7): 0 discrepancias frente a la
  implementación original. Desplegado y confirmado en vivo: CPU 93.7% →
  27.3%, pipeline 80.2ms → 24.0ms, detección sin cambios observables (mismo
  streak continuo).
- **Alternativas descartadas:** ninguna — vectorizar un filtro de ventana
  deslizante con `scipy` es la solución directa; no había trade-off real que
  registrar.

## 2026-07-13 — Subir continuity_confirm_frames: descartado tras verificación sintética

- **Decisión:** NO subir `continuity_confirm_frames` de 1 a 2-3, pese a que
  parecía la solución obvia para el enganche de clústeres espurios (mobiliario)
  del gate de continuidad visto en vivo tras el gesto.
- **Motivo:** verificado con un script sintético que replica
  `_gate_by_continuity` exactamente: el candidato espurio observado en el log
  real (mobiliario a 1.34m del último punto confirmado, tras 0.92s de hueco)
  cae **dentro del radio "plausible"** de `max_person_speed` (2.0 m/s × 0.92s
  + margen 0.3m = 2.14m) — y ese camino ("plausible") acepta el candidato
  **sin pasar nunca por el mecanismo de `continuity_confirm_frames`**, que
  solo se aplica a candidatos ya rechazados como implausibles. Subir el
  contador de 1 a 3 dio el mismo resultado exacto en la prueba sintética (los
  4 candidatos espurios seguían aceptándose) — cambiar este parámetro no
  toca el caso real que falla.
- **Alternativas para la próxima sesión (no implementadas hoy):** exigir
  confirmación *siempre* que el candidato venga del fallback de fusión
  cámara+LIDAR (señal más débil que un par de piernas emparejado), en vez de
  solo cuando falla el chequeo de velocidad — o acortar el radio "plausible"
  específicamente para ese camino. Requiere separar el estado de gating por
  origen del candidato (leg-pair vs. fusión), cambio no trivial aplazado por
  el tiempo disponible en sesión.

## 2026-07-13 — Parametrizar observation_timeout de tracking_node (antes hardcodeado)

- **Decisión:** convertir `self.timeout_s = 2.0` (hardcodeado en
  `tracking_node.py`, ni siquiera declarado como parámetro de ROS) en un
  parámetro `observation_timeout` declarado y expuesto en `config.yaml`,
  mismo valor por defecto (2.0s) — cambio sin efecto de comportamiento.
- **Motivo:** al investigar la oscilación FSM se descubrieron **tres
  mecanismos de timeout independientes y descoordinados** en tres nodos
  distintos: `detection_node` (`detection_confirm_frames=3`/
  `detection_loss_frames=8`), `control_node` (`tracking_loss_timeout=1.5s`),
  y este de `tracking_node`, que además era el único no parametrizado ni
  documentado junto a los otros dos.
- **Pendiente (no resuelto hoy):** los tres timeouts siguen sin coordinarse
  entre sí — solo se ha hecho visible/configurable el tercero. Diseñar cómo
  deberían relacionarse (o si conviene unificarlos en uno solo) queda para
  otra sesión.

## 2026-07-13 — Hallazgo: tracking_node no aplica el convenio "persona de frente ≈ π en el láser"

- **Hallazgo (no una decisión de fix — no se ha tocado el código):**
  `detection_node.py:431` documenta explícitamente que, en el frame del
  láser de este robot, una persona delante del robot da un ángulo ≈π (no
  ≈0) — *"Persona de frente ≈ π en el láser (TF base→laser con yaw=π)"* — y
  su propio fallback de fusión ya compensa ese desfase al calcular
  `theta_target`. Confirmado empíricamente hoy: con la persona delante del
  robot a 1m (verbal, sin ángulo), `/person_position` publicó `x=-1.18`
  (negativo).
- **El problema:** `tracking_node.py:283` (`angle_to = math.atan2(py, px)`)
  **no aplica ese mismo desfase de π** — su zona muerta (±8°) y PD angular
  tratan `angle_to≈0` (`px` positivo) como "persona delante". Esto hace que,
  con la persona realmente delante, el error angular calculado sea ≈180°, no
  ≈0.
- **Evidencia:** grabación de `near_gain` (42s, persona confirmada delante,
  activación por SSH sin gesto para evitar contaminación): `angle_deg` en
  `telemetry.csv` se queda oscilando pegado a ±180° durante toda la toma,
  sin converger nunca hacia 0 pese a `wz` saturado (±1.0 rad/s) casi todo el
  tiempo (71-76% del tiempo en un patrón de onda cuadrada — chattering en la
  singularidad antipodal, donde un ruido angular mínimo decide el sentido de
  giro).
- **Por qué no se ha roto el sistema hasta ahora:** el usuario confirma que
  en uso normal el seguimiento es "estable pero lento", no está roto.
  Hipótesis de cierre de la sesión: este desfase explica la lentitud/rigidez
  del giro y los episodios de saturación en casos límite (como este propio
  `near_gain`, donde la geometría de partida quedó casi exactamente
  antipodal), más que un fallo total — en operación típica el error angular
  probablemente no se estanca tanto tiempo tan cerca de la singularidad.
- **Verificación adicional (no concluyente por sí sola):** publicado
  `angular.z=+0.15` directo a `/commands/velocity` (bypass de todo el
  control), el robot giró hacia la izquierda (observación visual del
  usuario) — dato registrado pero sin una referencia externa fija no permite
  confirmar por sí solo el convenio de signo de `wz`; el hallazgo decisivo
  fue el contraste de código entre los dos nodos.
- **Pendiente de máxima prioridad, próxima sesión:** decidir cómo corregir
  `tracking_node.py` (offset de π directo en `angle_to`, o revisar si existe
  una transformación TF real `base_link→laser` en el URDF que debería
  aplicarse de forma consistente en todos los nodos en vez de un ajuste
  manual solo en `detection_node`). Cambio delicado del lazo de control
  angular — no tocado hoy a propósito, para revisarlo con calma. Bloquea
  poder aislar `near_gain` limpiamente.

## 2026-07-09 (sesión de lab) — Gesto real funcionando: umbral de visibilidad + cámara nueva

- **Decisión:** bajar `gesture_min_visibility` de 0.6 a 0.5 en `config.yaml`, y
  sustituir físicamente la cámara Logitech C270 por una SPCA2650 AV Camera
  tras comprobar en vivo que la geometría del gesto (`wrist.y < shoulder.y -
  margin`) ya se cumplía correctamente para ambas manos, pero la visibilidad
  de MediaPipe quedaba pegada al umbral (especialmente la muñeca izquierda,
  `v≈0.57-0.66`) y parpadeaba justo por debajo, rompiendo la racha de
  `gesture_confirm_frames=3` necesaria para disparar el comando.
- **Motivo:** objetivo específico 1 del TFM llevaba desde el 08/07 bloqueado
  por esto. Diagnosticado con el log `[GESTO-DBG]` en vivo: la mano derecha sí
  llegaba a `y` negativo (claramente fuera de encuadre por arriba) pero la
  izquierda rara vez bajaba de `y≈0.7-0.9`, con visibilidad marginal.
- **Resultado medido:** con el umbral en 0.5, `[GESTO] stop_tracking` y
  `[GESTO] start_tracking` se dispararon repetidamente y de forma fiable en
  varias tomas grabadas (`validation` — bags `gesto_real_v3`,
  `gesto_real_v4_fix`, `camara_nueva_velred` en `~/tfm_bags` del NUC, no
  copiados al repo por tamaño). Tras cambiar la cámara, la visibilidad de la
  muñeca derecha subió de forma sostenida (0.82-0.95 vs. 0.5-0.85 con la
  C270).
- **Alternativas descartadas:** re-encuadrar/inclinar la C270 físicamente sin
  cambiarla (era el plan original de la sesión) — se hizo primero el ajuste
  de software (umbral), y cuando el usuario decidió probar con una cámara
  distinta que tenía a mano, se comprobó que también ayudaba y se mantuvo.
- **Pendiente:** `camera_hfov_deg=51.0` y `bearing_sign=-1.0` (fusión
  cámara-LiDAR) se calibraron con la C270 — no reverificados con la SPCA2650.
  Si el FOV real difiere, el rumbo `/person_bearing` usado en el fallback de
  fusión podría desviarse; revisar en la próxima sesión si se observan
  desalineaciones en `dev_deg` de los logs de fusión.

## 2026-07-09 (sesión de lab) — Límite de deriva acumulada en el gate de continuidad (bug real encontrado y corregido en vivo)

- **Decisión:** añadir a `detection_node._gate_by_continuity` un segundo
  chequeo, además del salto respecto al frame anterior: ningún candidato se
  acepta si se aleja más de `max_person_speed·Δt_ventana + position_jump_margin`
  de la posición confirmada más antigua dentro de `continuity_window_s`
  (nuevo parámetro, 1.0s por defecto). Se aplica como filtro previo y duro,
  independiente del mecanismo de `continuity_confirm_frames` (ese mecanismo
  no sirve para este caso: una cadena de clústeres espurios consecutivos es,
  por definición, "consistente" frame a frame).
- **Motivo:** con el gesto ya funcionando, apareció en vivo un bug real —
  con la persona *quieta* delante del robot, la posición detectada barría un
  círculo completo alrededor del robot en 1-2 segundos (`x` de -2.1 a +2.1 m
  y viceversa), y el robot giraba sin control seguiéndola ("dando vueltas
  sobre sí mismo", en dos tomas distintas, una de ellas coincidiendo con una
  silla cercana). Causa raíz identificada leyendo `_gate_by_continuity`: el
  gate solo comprobaba el salto respecto al frame *inmediatamente anterior*;
  una cadena de clústeres espurios (patas de silla) separados poco más que
  `position_jump_margin` puede "caminar" de uno a otro, cada salto individual
  plausible, sumando una deriva de varios metros en 1-2s sin que ningún paso
  aislado la delate.
- **Verificación:** sin acceso a un entorno con ROS en el portátil, se
  extrajo la lógica de `_gate_by_continuity` a un script standalone y se
  probó con: (1) una cadena sintética de saltos de 0.3m replicando el
  barrido real observado — con el fix, empieza a rechazar candidatos en
  cuanto la deriva acumulada supera el presupuesto de la ventana; (2) una
  persona real caminando a 1.2 m/s y a 2.0 m/s (límite físico) en línea
  recta — 20/20 muestras aceptadas en ambos casos, el fix no restringe
  movimiento real; (3) una reaparición lejana tras pérdida larga (ancla
  limpiada) — aceptada sin filtrar, como antes. Validado también en vivo
  tras desplegar: la toma siguiente (`gesto_real_v4_fix`) no repitió el
  barrido (salto máximo entre muestras 1.49m, sin patrón circular repetido).
- **Alternativas descartadas:** usar una media móvil exponencial como ancla
  en vez de una ventana con historial explícito (más simple de mantener,
  pero más difícil de razonar/verificar con pruebas sintéticas exactas dado
  el tiempo disponible en sesión); subir directamente `continuity_confirm_frames`
  a 2-3 (ya estaba preparado desde el 07-08, pero no ataca la causa —una
  cadena de saltos "consistentes" entre sí seguiría confirmándose igual).

## 2026-07-09 (sesión de lab) — Arranque suave de `wz` tras activar el seguimiento

- **Decisión:** nuevos parámetros `startup_ramp_s` (1.5s) y `startup_max_wz`
  (0.5 rad/s) en `tracking_node`: durante los primeros `startup_ramp_s`
  segundos tras cada activación de `tracking_enabled` (gesto o
  reactivación), el techo de `|wz|` sube linealmente de `startup_max_wz` a
  1.0 en vez de permitir ya el máximo. Se aplica tras el clamp normal a
  [-1,1] y antes del rate-limit por ciclo (`ang_acc_limit`) ya existente.
- **Motivo:** el usuario reportó que el robot "se volvía loco dando
  vueltas" justo al arrancar el seguimiento. Con datos reales del bag
  (`camara_nueva_velred`, extraído con `bag_to_csv.py` en el NUC): el
  ángulo a la persona al activar era de -157.9° (casi detrás del robot), y
  `wz` saturaba a ±1.0 rad/s en ~0.3s (el rate-limit `ang_acc_limit=0.3`
  YA estaba funcionando como se diseñó — no había ningún salto instantáneo).
  Es decir: **no era un bug de control**, sino la respuesta físicamente
  correcta a un error de rumbo grande — pero se sentía brusca. El arranque
  suave añade un techo adicional, más conservador, solo en los primeros
  instantes tras activar, para que la corrección inicial sea más gradual
  incluso cuando el error de partida es grande.
- **Verificado:** con lógica aislada (réplica standalone del ramp), comparando
  antes/después con el error real observado (-157.9°): antes, `wz` llega a
  -1.0 en 0.3s; después, sube gradualmente hasta -1.0 a los 1.5s. Validado en
  vivo tras desplegar: el usuario confirmó una prueba completa sin fallos.
- **Alternativas descartadas:** bajar `ang_acc_limit` de forma permanente
  (ralentizaría también la corrección de errores angulares reales ya en
  curso, no solo el arranque); bajar el clamp global de `wz` de ±1.0 a un
  valor menor de forma permanente (mismo problema, afecta a todo el
  seguimiento, no solo al instante de activación).

## 2026-07-09 (sesión de lab) — Velocidad máxima reducida para pruebas

- **Decisión:** `max_speed` de 0.3 a 0.18 m/s en `config.yaml`.
- **Motivo:** petición explícita del usuario para pruebas de gesto más
  suaves y fáciles de observar con seguridad mientras se depuraban varios
  problemas a la vez (gesto, deriva de detección, arranque brusco). Es un
  valor de sesión de pruebas, no necesariamente el definitivo — revisar si
  se quiere subir de nuevo una vez el resto esté estable.

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
