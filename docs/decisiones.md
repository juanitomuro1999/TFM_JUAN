# Decisiones de diseño

> Registro de decisiones importantes: qué se decidió, por qué, y qué
> alternativas se descartaron. Complementa a `04_diario_desarrollo.md` (que
> es narrativo, para la memoria) con un registro corto y consultable.
> Entrada nueva arriba.

## 2026-07-21 — Reproducibilidad de la tabla 7.4: saltos de posición sí reproducen, saturación angular no

- **Contexto:** punto 3 del objetivo de la Sesión 4 (reproducibilidad de
  métricas del Capítulo 7, pendiente desde el 2026-07-09). Requiere una
  máquina con ROS 2 para leer los bags `.db3` — con conectividad SSH al NUC
  confirmada hoy, se hizo posible sin esperar a otra sesión.
- **Procedimiento:** copiados por `scp` los tres bags de
  `validation/runs/20260708_movimiento_{original,fix1_gating,fix2_kalman_wz}`
  al NUC (`/tmp/tfm_bags_ch7/`, no versionado); ejecutado
  `bag_to_csv.py` (sincronizado también por `scp`, no está en
  `sync_nuc.sh`) en el NUC sobre cada uno; traídos los CSVs resultantes de
  vuelta al portátil (`analysis_new/` junto a cada `analysis/` original, sin
  sobreescribir la extracción del 08/07); ejecutado `plot_run.py`
  localmente (tiene matplotlib) con los umbrales por defecto
  (`--jump-threshold 0.8 --stable-radius 0.15 --stable-window 1.0
  --sat-threshold 0.95`).
- **Resultado (tabla completa):**

  | Toma | Saltos >0.8m: tabla / nuevo | Saturación estable: tabla / nuevo | Saturación global (nuevo) |
  |---|---|---|---|
  | Original | 12.1% / **3.5%** | 94.5% / **95.7%** | 96.9% |
  | + fix1 (gate continuidad) | 2.2% / **2.2%** | 72.2% / **99.3%** | 99.4% |
  | + fix2/3 (Mahalanobis+rate-limit) | 0.7% / **0.7%** | 12.4% / **86.9%** | 80.6% |

- **Lectura:** el % de saltos de posición reproduce perfectamente en fix1 y
  fix2 (mismo valor exacto) y razonablemente en la tendencia general, solo
  diverge en el valor absoluto de la toma "original" (3.5% vs 12.1% —
  posiblemente el script perdido usaba un umbral o ventana distintos, no
  documentados). La saturación angular es harina de otro costal: **no solo
  no coincide en valores, invierte la conclusión** — el script perdido
  sugería una mejora fuerte y monótona (94.5%→12.4%), pero el pipeline
  reproducible muestra saturación alta y no monótona en las tres tomas
  (95.7%→99.3%→86.9%). Se revisó `stable_mask`/`saturation_with_stability`
  en `plot_run.py` línea a línea buscando un bug antes de aceptar esta
  divergencia como real — la implementación es coherente, no se encontró
  ningún error.
- **Hipótesis de la causa (sin confirmar):** dos factores no excluyentes.
  (a) El número de muestras "estables" en fix1/fix2 es pequeño (272 y 191,
  frente a 900 en la toma original) — con tan pocas muestras el % es más
  ruidoso y sensible a qué momentos concretos caen en la ventana de
  estabilidad. (b) Los tres fixes de esta tabla (gate de continuidad,
  Mahalanobis, rate-limit de `wz`) atacan la *continuidad de la detección*,
  no la *ganancia* del controlador angular — el ajuste que sí ataca la
  saturación a corta distancia (`near_gain`, zona muerta angular ±8°) se
  añadió el 2026-07-15, una semana después de estos bags. Es plausible que
  las muestras "estables" de fix1/fix2 capturen momentos de acercamiento a
  corta distancia donde, sin `near_gain` todavía, el giro satura casi
  siempre — pero esto no se ha verificado hoy (requeriría cruzar
  `position.csv` con `distance` en esos instantes concretos).
- **Decisión:** actualizada la tabla 7.4 y su párrafo de "Lectura" en
  `docs/07_resultados.md` con las cifras reproducibles y una conclusión
  honesta: mejora clara y sostenida en saltos de posición, sin mejora
  sostenida en saturación angular con estos tres fixes concretos (queda
  como limitación abierta, no como logro). Actualizada también la entrada
  de `docs/sesion_siguiente.md` (objetivo 3 de la Sesión 4) y §7.5.
- **Alternativas descartadas:** dejar la tabla y la lectura antiguas
  intactas y solo anotar la discrepancia aparte — descartado porque la
  tabla 7.4 es parte del cuerpo de la memoria y afirmar una mejora que el
  propio pipeline reproducible del repo contradice sería inconsistente con
  el resto del documento.
- **Pendiente:** confirmar o descartar la hipótesis (b) de arriba cruzando
  `position.csv`/`distance` en los instantes "estables" de fix1/fix2; no
  bloquea nada, es refinamiento del análisis. Los ficheros CSV nuevos viven
  en `validation/runs/20260708_movimiento_*/analysis_new/` (no se ha
  sobreescrito `analysis/` original, que sigue reflejando la extracción del
  08/07 con el formato antiguo de `metrics.txt`).

## 2026-07-21 — CONFIRMADO Y CORREGIDO: la evasión de obstáculos de `tracking_node` vigilaba el sector trasero, no el frontal

- **Contexto:** primera tarea de la Sesión 4 de lab, priorizada por barata y
  de seguridad (ver hallazgo sin verificar del 17/07 justo debajo). Con
  conectividad SSH al NUC confirmada y el robot encendido, se verificó de
  forma empírica antes de tocar nada.
- **Verificación (sin mover el robot, solo lectura de `/scan`):** con el
  robot parado, se colocó una silla de laboratorio a 25cm y se leyó el
  `/scan` crudo con un script puntual (no forma parte del repo), buscando el
  ángulo del rango mínimo:
  - Silla **delante** (pegada a la base) → mínimo a 0.386m, ángulo crudo
    ≈ **-174°** (cerca de ±180°).
  - Misma silla **detrás**, misma distancia → mínimo a 0.365-0.375m, ángulo
    crudo ≈ **0-2°**.
  - Esto confirma sin ambigüedad la hipótesis del 17/07: "delante" real
    está en el ángulo crudo ≈ ±π, no en ≈0 — mismo desfase que
    `detection_node` ya corrige al publicar `/person_position`.
- **Decisión:** corregido en `tracking_node._obstacle_avoidance` — antes de
  aplicar el filtro `abs(ang)<=50°`, se normaliza el ángulo crudo restando π
  y envolviendo a `(-π, π]` con `atan2(sin(x), cos(x))`. El resto de la
  función (peso `cos(ang)`, `repulsion += w·(-ang)`) no cambia, solo pasa a
  operar sobre el ángulo ya corregido — coherente con el resto del fichero
  (`angle_to = atan2(py, px)` ya usa el convenio real, delante=0°).
- **Validado en vivo tras el fix** (sin movimiento real del robot):
  sincronizado a NUC, relanzado `person_follower`, con la silla delante y
  tracking activado manualmente (`ros2 service call /enable_tracking
  std_srvs/srv/SetBool "{data: true}"`, sin gesto, para no depender de la
  FSM) se disparó correctamente `"Obstáculo frontal: adj=-0.00
  lin_factor=0.95"` de forma sostenida. `adj≈0` es coherente con un
  obstáculo centrado justo delante (sin necesidad de girar para evitarlo).
  Velocidad en `/commands/velocity` confirmada en cero durante toda la
  prueba (persona simulada/real a la distancia objetivo, sin desplazamiento
  real). Desactivado el tracking al terminar
  (`std_srvs/srv/SetBool "{data: false}"`) y confirmado que el log deja de
  dispararse.
- **Alternativas descartadas:** ninguna — es una corrección directa de un
  bug de convenio de ángulo, no una decisión de diseño con alternativas.
- **Pendiente:** repetir en algún momento con el robot realmente en
  movimiento (avanzando hacia una persona) y un obstáculo real en su
  camino, para confirmar que `lin_factor` frena de verdad la marcha — la
  prueba de hoy solo confirmó el sector correcto y el disparo del log, no
  el efecto sobre `vx` con el robot en movimiento real.

## 2026-07-17 — HALLAZGO SIN VERIFICAR: la evasión de obstáculos de `tracking_node` podría mirar al sector trasero, no al frontal

- **Contexto:** revisión de escritorio del hallazgo del signo invertido del
  15/07 (tarea 2 de `docs/sesion_siguiente.md`). Al releer
  `tracking_node._obstacle_avoidance` para confirmar que el fix de signo
  del PD angular no dejaba nada suelto, apareció esta hipótesis nueva y
  distinta — no es el mismo bug, ni se ha tocado código.
- **La hipótesis:** `_obstacle_avoidance` calcula `ang = scan.angle_min +
  i·scan.angle_increment` directamente sobre `/scan` **crudo**, y filtra
  `if abs(ang) > radians(50): continue` (es decir, solo analiza el sector
  dentro de ±50° de `ang=0` en el frame crudo del láser). Pero
  `detection_node.py` documenta explícitamente, y lo tiene verificado en
  vivo desde el 13/07 (`docs/decisiones.md`, "Fix: normalizar el convenio
  de /person_position en el origen"), que en el frame crudo de este robot
  concreto **"persona de frente ≈ π en el láser"** — el RPLIDAR está
  montado invertido (TF `base_footprint→laser` con yaw=π,
  `docs/02_arquitectura.md` §2.5). Si ese desfase aplica de forma uniforme
  a todo `/scan` (no hay motivo aparente para que no sea así — es una
  propiedad del montaje físico del sensor, no del contenido del mensaje),
  entonces `ang≈0` en crudo es la parte **trasera** del robot, no la
  delantera, y el filtro `abs(ang)<=50°` de `_obstacle_avoidance` estaría
  vigilando el sector trasero en vez del sector frontal por el que el
  robot realmente avanza.
- **Por qué no se ha corregido ni confirmado todavía:** es una hipótesis
  derivada por analogía con un hallazgo ya verificado en *otro* nodo, no
  algo comprobado de forma directa para `tracking_node`. No hay forma de
  verificarlo con los datos ya grabados en este portátil —
  `validation/bag_to_csv.py` no extrae `/scan` crudo a CSV, así que no hay
  manera de comprobarlo sin ROS 2 instalado (este equipo no lo tiene, ver
  `PROGRESO.md` 2026-07-09) ni sin repetir la extracción de un bag ya
  grabado en una máquina con ROS.
- **Cómo verificarlo (barato, próxima sesión de lab):** colocar un
  obstáculo conocido justo delante del robot (dentro de
  `obstacle_threshold=0.35m`) y comprobar si se dispara el log
  `"Obstáculo frontal: adj=... lin_factor=..."` y si `lin_factor` baja de
  1.0. Repetir con el obstáculo justo detrás en vez de delante. Si el
  aviso solo se dispara con el obstáculo detrás (o con ambos, lo cual
  también sería raro), confirma la hipótesis. Alternativa sin gastar
  tiempo de robot: extender `bag_to_csv.py` para extraer `/scan` crudo de
  un bag ya grabado con un obstáculo en posición conocida (p. ej.
  `validation/runs/20260715_obstaculo*/`) y comprobar a qué ángulo cae el
  obstáculo real.
- **Impacto si se confirma:** relevante para seguridad — un robot que
  avanza sin ver obstáculos delante (porque su evasión reactiva vigila el
  sector equivocado) es un riesgo real, no solo una imprecisión de
  seguimiento. No bloquea el resto del sistema (la evasión de obstáculos
  es una capa adicional, no la única protección — `collision_handling_node`
  también vigila el `/scan` completo, aunque tampoco está conectado a
  `control_node` todavía, §2.3.5), pero merece prioridad si se confirma.
- **Alternativas descartadas:** ninguna todavía — es un hallazgo, no una
  decisión de diseño. No se ha tocado `tracking_node.py` para esto.

## 2026-07-16 — Confirmación obligatoria en el fallback de fusión (preparado sin robot, pendiente de validar en el lab)

- **Decisión:** en `detection_node.py`, el camino de fusión cámara+LIDAR ya
  no usa `_gate_by_continuity` (compartido hasta hoy con el camino de pares
  de piernas). Ahora usa un mecanismo dedicado,
  `_confirm_fusion_candidate`, que exige `continuity_confirm_frames` scans
  consecutivos con el candidato en aprox. el mismo sitio (tolerancia
  `position_jump_margin`) antes de aceptarlo — **siempre**, no solo cuando
  el candidato falla el chequeo de velocidad plausible. El filtro de deriva
  acumulada (ventana `continuity_window_s`) se extrajo a un helper
  compartido, `_filter_by_drift`, y sigue aplicándose igual en ambos
  caminos. `_gate_by_continuity` (pares de piernas) no cambia de
  comportamiento.
- **Motivo:** hallazgo de 2026-07-13 (entrada de más abajo, "Subir
  continuity_confirm_frames: descartado"): un candidato de fusión se
  aceptaba sin ninguna confirmación si caía dentro del radio "plausible" de
  `max_person_speed·Δt + position_jump_margin` respecto al último punto
  confirmado — y ese radio crece rápido (2.14m tras solo 0.92s con los
  valores por defecto), suficiente para que mobiliario cercano se cuele
  como si fuera la persona. Subir `continuity_confirm_frames` de 1 a 2-3 no
  arreglaba esto porque ese mecanismo solo se aplicaba a candidatos ya
  rechazados como implausibles — el caso real (mueble a 1.34m tras 0.92s)
  nunca llegaba a rechazarse. La tarea 1 de la Sesión 4
  (`docs/sesion_siguiente.md`) es exactamente diseñar este fix.
- **Por qué solo a fusión y no también a pares de piernas:** un par de
  piernas ya emparejado (dos clústeres a distancia coherente entre sí) es
  una señal geométrica bastante más fuerte que un único clúster general
  elegido solo por alinearse angularmente con el rumbo de cámara. Exigir la
  misma confirmación al camino de piernas penalizaría innecesariamente el
  camino más fiable de detección, sin necesidad — el problema documentado
  es específico del camino de fusión.
- **Verificación:** `validation/verify_fusion_confirm.py` (nuevo, sin ROS
  — este portátil no tiene `rclpy`, ver `PROGRESO.md` 2026-07-09).
  `FusionGateSim` replica la lógica exacta de `_filter_by_drift`,
  `_confirm_fusion_candidate` y `_gate_by_continuity`. Seis escenarios
  (ocho comprobaciones individuales), todos en verde:
  1. Reproduce el bug original con el mecanismo anterior (control negativo).
  2. El mismo caso real (mueble a 1.34m tras 0.92s) ya NO se acepta hasta
     el 3er scan consecutivo con `continuity_confirm_frames=3`.
  3. Ruido disperso (posiciones aleatorias) nunca acumula racha en 20 scans.
  4. Una persona real (posición consistente con ruido de medida pequeño) se
     confirma exactamente en el scan `continuity_confirm_frames`, ni antes
     ni después.
  5. Con el valor por defecto (`continuity_confirm_frames=1`), el
     comportamiento es idéntico al anterior — el fix no añade latencia si
     nadie sube el parámetro a mano.
  6. `_gate_by_continuity` (pares de piernas) no cambia de comportamiento.
  **Pendiente de validar con datos reales/en vivo en la Sesión 4** — esto
  es solo lógica aislada, replicada a mano en el script de verificación, no
  el nodo real ejecutándose con ROS.
- **Efecto colateral (positivo) del refactor:** antes, el camino de fusión
  llamaba a `_gate_by_continuity`, que también actualiza
  `_continuity_reject_streak`/`_pending_reanchor` — variables pensadas solo
  para el camino de pares de piernas. Un candidato de fusión rechazado
  podía así interferir con la racha de confirmación de un salto de piernas
  en curso, y viceversa. Al separar los caminos con estado dedicado
  (`_fusion_confirm_streak`/`_fusion_pending_candidate`), esa interferencia
  ya no es posible. No se observó en vivo (no hay log conocido que lo
  atribuya), pero es una fuente de bugs intermitentes descartada de paso.
- **Alternativas descartadas:**
  - *Subir `continuity_confirm_frames` sin más:* ya descartado el 13/07
    (ver abajo) — no ataca la causa.
  - *Aplicar la misma exigencia de confirmación también a pares de
    piernas:* más simple (un solo mecanismo), pero penaliza sin necesidad
    la señal más fiable del sistema con la misma latencia que necesita la
    señal más débil.
  - *Requerir confirmación proporcional a la distancia del salto* (más
    exigente cuanto más lejos el candidato): más preciso en teoría, pero
    añade un parámetro nuevo a calibrar sin evidencia de que el umbral fijo
    actual sea insuficiente; se prefirió el mecanismo más simple hasta ver
    datos reales que lo justifiquen.

## 2026-07-15 — CORREGIDO: signo invertido en el PD angular de tracking_node (causa raíz real de "gira al lado contrario")

- **Decisión:** revertir `ang_err = -angle_to` a `ang_err = angle_to` en
  `tracking_node.py` (línea junto al cálculo de `angle_to = atan2(py, px)`).
- **Motivo:** el 13/07 se concluyó, con una simulación numérica offline (sin
  medir el robot real), que "este robot gira en sentido contrario al
  estándar ROS" y que por tanto invertir el signo (`ang_err=-angle_to`) era
  necesario y correcto. Repetido hoy el problema en dos pruebas de
  movimiento real (ver entrada anterior de hoy sobre el diagnóstico de
  LIDAR+cámara) con el usuario confirmando en vivo "gira al lado contrario",
  se hizo una verificación directa y objetiva, sin pasar por percepción en
  absoluto: publicar `angular.z` constante en `/commands/velocity` y medir
  el yaw real vía `/odom` (integrado por el propio `kobuki_ros_node` desde
  IMU/encoders). Resultado, con dos ensayos independientes:
  `wz_cmd=+0.5 rad/s` (3s) → `yaw` sube +18.7°; `wz_cmd=-0.5 rad/s` (3s) →
  `yaw` baja -23.8°. **Mismo signo que el comando** — este robot sigue el
  convenio estándar (positivo = antihorario, REP103), al contrario de lo
  concluido el 13/07. Con `ang_err=-angle_to`, el PD angular empujaba
  sistemáticamente en la dirección contraria a la necesaria para reducir el
  error — enmascarado en pruebas casi estáticas (persona quieta y de frente)
  porque el error se queda dentro de la zona muerta angular (±8°) y apenas
  se nota, pero se convierte en una divergencia de realimentación positiva
  en cuanto el error crece por encima de la zona muerta (persona
  moviéndose/girando), justo el patrón visto en los dos tests de hoy
  (`angle_deg` creciendo sin parar hasta envolver en ±180° repetidamente).
- **Por qué la simulación del 13/07 no lo detectó:** simuló convergencia
  para un caso casi antipodal concreto observado en un bag ya grabado, sin
  una referencia externa dura del signo real de rotación del robot — la
  "confirmación en vivo" de esa fecha fue observación visual del usuario
  sin punto de referencia fijo, que resultó ambigua (ver
  `PROGRESO.md`, 2026-07-13, "test adicional... no concluyente"). La
  verificación de hoy usa `/odom` como referencia objetiva y elimina esa
  ambigüedad.
- **Cambio relacionado en la misma sesión:** además de este fix, se añadió
  `extrapolation_limit_s` (parar tras 0.6s sin observación fresca en vez de
  extrapolar con Kalman hasta 2.0s) y se bajó `camera_debounce_count` de 2 a
  1 — ambos siguen siendo mejoras válidas por sí mismas (evitan que el
  robot navegue a ciegas durante huecos de detección reales, que siguen
  existiendo — ver diagnóstico de arriba), pero **no eran la causa principal
  del síntoma reportado hoy** — el signo invertido lo era.
- **Pendiente de verificar:** repetir el test de seguimiento con movimiento
  real ahora con el signo corregido antes de dar el TFM por resuelto en este
  punto. Si el usuario confirma que ya no gira al lado contrario, esto
  reemplaza la conclusión de la entrada de 13/07 ("simulación con esa
  asunción SÍ reproduce...") como la explicación correcta y definitiva.
- **Alternativas descartadas:** ninguna — una vez medido el signo real de
  forma objetiva, la corrección es directa.

## 2026-07-15 — Diagnóstico: LIDAR y cámara pierden a la persona a la vez al girar (causa real de "gira al lado contrario")

- **Hallazgo (no es un bug de signo):** durante la prueba de movimiento real
  de la Sesión 3 (objetivo 1, confirmar el fix de π del 13/07), el usuario
  reportó en vivo que el robot "gira hacia el otro lado y se desorienta" al
  moverse/girar — el mismo síntoma que se había investigado y descartado
  como bug el 13/07 (ver entrada de esa fecha). Repetido el análisis con los
  datos de hoy (`validation/runs/20260715_sesion3_pi_movimiento/`), el fix
  de π **se mantiene** (`dev_deg` entre LIDAR y cámara se queda en 5-20°
  cuando ambos coinciden, ya no pegado a ±180°), pero aparece un problema
  distinto y más grave: **LIDAR y cámara dejan de detectar a la persona
  simultáneamente durante los giros**, dejando huecos de ~2-4s sin ninguna
  medición fresca. Durante esos huecos, el filtro de Kalman de
  `tracking_node` extrapola con la última velocidad conocida; cuando vuelve
  una medición (a menudo con salto grande tras el hueco), el PD angular
  reacciona de golpe — eso se percibe como "gira al lado contrario".
- **Causa raíz (dos modalidades con el mismo punto débil: la vista frontal):**
  - **LIDAR (`detect_person`/`detect_leg_clusters`):** el emparejamiento de
    piernas exige dos clústeres separados entre `min_leg_distance` (0.04m) y
    `max_leg_distance` (0.35m). Al girar el cuerpo, una pierna puede ocluir a
    la otra (colapsan a un solo clúster) o la separación aparente se sale de
    esa ventana — el emparejamiento falla justo cuando la persona no está de
    frente.
  - **Cámara (`visual_detection_node._detect_mp`):** `/person_detected_visual`
    se publica cada frame según si MediaPipe encuentra `pose_landmarks` en
    absoluto (no solo la visibilidad de hombros). Un giro rápido introduce
    motion blur que puede hacer fallar la detección de pose en un frame
    puntual. Como `detection_node` exige `camera_debounce_count=2` frames
    consecutivos en `True` tras cualquier `False` (y la cámara procesa a
    ~2.5Hz por el coste de MediaPipe), un solo frame perdido cuesta ~800ms+
    de "cam no válida" aunque la persona siga en el encuadre. Verificado en
    el log: a las 1784124266.517 ambos hombros visibility=1.00 y 33
    landmarks visibles; 437ms después (1784124266.954) ya aparece
    `lidar: False, cam: False` — y el hueco total sin ninguna detección se
    extiende de 1784124266.95 a 1784124270.55 (~3.6s).
  - **El fallback de fusión no cubre este caso** porque necesita *ambas*
    señales: sin clúster general dentro de `fusion_angle_tol_deg` (25°) o sin
    rumbo de cámara reciente (`bearing_timeout=1.5s`), no hay candidato que
    publicar — y aquí las dos fallan a la vez, no una sustituye a la otra.
  - **Los tres timeouts de "dar por perdida a la persona" siguen
    descoordinados** (ver entrada 2026-07-13): `detection_loss_frames=8`
    (~0.7s a 11.5Hz), `tracking_loss_timeout=1.5s` (`control_node`),
    `observation_timeout=2.0s` (`tracking_node`) — ninguno coincide con la
    duración real observada del hueco (~2-4s), así que cada capa reacciona
    en un momento distinto sin una política única.
- **No corregido hoy** — es un problema de arquitectura (las dos modalidades
  de fusión comparten el mismo punto ciego: la vista frontal de la persona),
  no una línea de código suelta. Requiere decidir una estrategia (¿girar el
  propio robot para mantener a la persona de frente en vez de asumir que
  camina de frente al sensor? ¿añadir una tercera señal — p. ej. seguir la
  velocidad de Kalman durante el hueco con un tope de tiempo más corto y
  coordinado? ¿relajar `max_leg_distance`/permitir clúster único como pierna
  "vista de perfil"?) — para la memoria, documentar como limitación conocida
  del enfoque de fusión si no da tiempo a resolverlo con las sesiones que
  quedan.
- **Alternativas descartadas:** ninguna aún — es un hallazgo de diagnóstico,
  pendiente de decidir el fix en una sesión futura (o de escritorio, ya que
  el análisis en sí no requirió el robot, solo los datos ya grabados).

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

## 2026-07-13 — Fix: normalizar el convenio de /person_position en el origen (corregido y verificado, misma sesión)

- **Decisión:** en vez de parchear `tracking_node` con un offset de π (opción
  mínima) o mantener el hallazgo sin resolver, se normalizó en el origen:
  `detection_node._publish_person_position` invierte el signo de `x,y`
  **solo en la frontera de publicación** (`Point(x=-xy[0], y=-xy[1])`); todo
  el estado interno (gating, `_position_history`, matching del fallback de
  fusión) sigue operando en el frame bruto del láser, sin tocar.
- **Por qué esta opción y no el offset en tracking_node:** confirmado que no
  existe una TF real `base_link→laser` (`/tf_static` vacío, `tf2_echo`
  reporta que el frame "laser" no existe) — el "yaw=π" era solo una
  convención de facto documentada en un comentario, no una transformación
  consultable. Y el único consumidor funcional de `/person_position` es
  `tracking_node` (`DWA.py`, con un `atan2` equivalente, es una
  implementación alternativa no usada en el launch — ver
  `person_follower/launch/start_person_follower.launch.py`). Con un solo
  consumidor real, es más limpio corregir el contrato de salida una vez en
  el origen que exigir que cada consumidor futuro recuerde aplicar el
  offset manualmente. `tracking_node` no necesitó ningún cambio — su
  `angle_to = atan2(py, px)` ya asumía el convenio estándar correctamente,
  solo estaba recibiendo datos con el signo equivocado.
- **Verificado en vivo** (persona delante confirmada, ~1.3m, TRACKING
  activado por SSH): `/person_position` pasa de publicar `x=-1.18` a
  `x=+0.86` (positivo) con la persona delante. `angle_deg` en telemetría
  pasa de oscilar pegado a ±180° a mantenerse estable en 5.5-6.8° (dentro de
  la zona muerta ±8°). `vang` pasa de saturar el 71-76% del tiempo a
  prácticamente 0 (0.001-0.002 rad/s).
- **Efecto colateral esperado (no verificado hoy):** los marcadores de RViz
  de `user_interface_node`/`UI_man.py` (que consumen `/expected_person_position`
  para visualización) deberían empezar a mostrar a la persona en el lado
  intuitivo/correcto en vez del opuesto — no crítico, no se ha comprobado
  visualmente.
- **Pendiente:** las dos tomas de `near_gain` grabadas hoy antes del fix
  quedaron contaminadas por este bug — repetir la validación con el sistema
  ya corregido en la próxima sesión.

## 2026-07-13 — Hallazgo original (contexto, ya corregido arriba): tracking_node no aplicaba el convenio "persona de frente ≈ π en el láser"

- **Hallazgo tal y como se registró en el momento (no una decisión de fix —
  el código seguía sin tocar cuando se escribió esto; ver la entrada de
  arriba para el fix aplicado después, misma sesión):**
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
- **Actualización (misma sesión, con tiempo extra):** corregido y verificado
  en vivo — ver la entrada de arriba ("Fix: normalizar el convenio de
  /person_position en el origen").

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
