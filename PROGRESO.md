# Diario de progreso — TFM Person Follower

## Sesión 2026-07-21 (lab, Sesión 4) — Bug de seguridad confirmado y corregido: evasión de obstáculos vigilaba el sector trasero

### Arranque de sesión

Conectividad SSH al NUC confirmada al empezar (`ping 10.48.0.1` OK), así que
sesión de lab real, no de escritorio. Repo local sincronizado con GitHub
(5 commits nuevos desde el 17/07: capítulos 5-6, fix de confirmación de
fusión, confirmación del signo angular, calendario de sesiones). Código
(`tracking_node.py`, `detection_node.py`, `config.yaml`) sincronizado al NUC
con `sync_nuc.sh` — estaba desactualizado (última sync antes del fix de
fusión del 16/07). USB de kobuki/rplidar sin reenumerar hoy (`ttyUSB0`
sigue siendo la Kobuki). Stack completo (kobuki, rplidar, 7 nodos de
`person_follower`) levantado sin errores.

### Hallazgo del 17/07 verificado y corregido: sector de obstáculos invertido

Primera tarea de la sesión (barata, prioridad de seguridad, ver
`docs/sesion_siguiente.md` punto 4). Verificado con una silla de
laboratorio a 25cm del LIDAR, leyendo `/scan` crudo directamente (sin mover
el robot):
- Silla delante → mínimo del láser en ángulo crudo ≈ **-174°**.
- Silla detrás → mínimo del láser en ángulo crudo ≈ **0-2°**.

Confirma que `tracking_node._obstacle_avoidance` (que trataba `ang≈0` como
"delante") vigilaba en realidad el sector **trasero**. Corregido aplicando
el mismo desfase de π que `detection_node` ya tiene documentado desde el
13/07. Sincronizado el fix al NUC, relanzado `person_follower`, y validado
en vivo (sin movimiento real): con la silla delante y tracking activado
manualmente por servicio, el log `"Obstáculo frontal"` se dispara de forma
sostenida con `adj≈0` (coherente, obstáculo centrado). Desactivado el
tracking al terminar y confirmado que deja de dispararse. Detalle completo
en `docs/decisiones.md` (2026-07-21).

**Pendiente:** repetir con el robot en movimiento real hacia una persona y
un obstáculo real en el camino, para confirmar que `lin_factor` frena la
marcha de verdad — hoy solo se confirmó el sector correcto y el disparo del
log, sin desplazamiento.

### Gate de continuidad estresado con mobiliario denso — continuity_confirm_frames 1→3

Última tarea de la Sesión 4. Con mobiliario denso cerca de la trayectoria
y el robot siguiendo de verdad (~2 min por toma, dos tomas): con
`continuity_confirm_frames=1` (valor anterior), 12.9% de saltos de
posición >0.8m (máx 3.40m) y 4.9% de saturación angular global — el
mobiliario se cuela ocasionalmente por el fallback de pierna única/fusión
(ninguno de los dos tiene chequeo de salto inmediato frame a frame, solo
deriva acumulada). Subido a `continuity_confirm_frames=3`: saltos bajan a
4.6%, saturación a 0.0%, a cambio de una detección ligeramente menor
(100%→97.8%) y MAE de distancia peor (0.633m→0.854m, aunque son dos
caminatas reales distintas, no una repetición controlada — no se puede
achacar con seguridad al parámetro). Se mantiene 3 como nuevo valor por
defecto en `config.yaml`. Detalle completo, incluida la comparación de
métricas, en `docs/decisiones.md` (2026-07-21). Bags de ambas tomas en
`validation/runs/20260721_continuidad_mobiliario*/`.

### Fallback de pierna única para el hueco de detección al girar (objetivo principal de la sesión)

Implementado en `detection_node.detect_person`: cuando no hay par de
piernas válido pero sí un clúster único ya clasificado como pierna, se
acepta como candidato (gateado con `_confirm_single_leg_candidate`, mismo
mecanismo que la fusión cámara+LIDAR del 16/07), antes de caer al fallback
de cámara. Verificado sintéticamente
(`validation/verify_single_leg_fallback.py`, 4 escenarios en verde) y en
vivo: con una persona girando delante del robot ~30s (sin mover el robot,
sin activar tracking), el log registró 630 detecciones vía el nuevo
fallback, 315 vía par normal (sin regresión), 0 vía cámara y 0 errores.
Solo una pérdida de racha de ~1.6s en toda la prueba, frente a los 2-4s
documentados el 15/07. Detalle completo en `docs/decisiones.md`
(2026-07-21). Pendiente: repetir con el robot realmente siguiendo
(tracking activo) y cuantificar el hueco residual con más repeticiones.

### Reproducibilidad de la tabla 7.4 (Capítulo 7): saltos sí, saturación no

Punto 3 del objetivo de la Sesión 4, pendiente desde el 09/07 (requería una
máquina con ROS 2 para leer los bags `.db3`, imposible desde este portátil
— ver `PROGRESO.md` 2026-07-09). Con el NUC accesible hoy, se copiaron los
tres bags de `validation/runs/20260708_movimiento_*` al NUC, se re-extrajeron
con `bag_to_csv.py` (sincronizado a mano, no está en `sync_nuc.sh`) y se
analizaron localmente con `plot_run.py`. Resultado: el % de saltos de
posición reproduce bien (exacto en fix1/fix2: 2.2% y 0.7%; más bajo de lo
esperado en la toma original: 3.5% vs 12.1%). La saturación angular **no**
reproduce la mejora que sugerían las cifras del script perdido — se
mantiene alta (86-99%) en las tres tomas en vez de bajar a 12.4%, e incluso
sube tras el primer fix. Revisada la implementación de `plot_run.py` en
detalle, no hay bug — es una divergencia real, con dos hipótesis sin
confirmar (pocas muestras "estables" en las tomas cortas; posible efecto de
acercamiento a corta distancia sin `near_gain`, que no existía todavía el
08/07). Actualizada la tabla 7.4 y su lectura en `docs/07_resultados.md`
con las cifras reproducibles y una conclusión honesta: mejora sostenida en
saltos, sin mejora sostenida en saturación con estos tres fixes concretos.
Detalle completo en `docs/decisiones.md` (2026-07-21).

### Notas operativas de la sesión

- El primer intento de `ros2 launch ... & disown` por SSH se quedó colgado
  localmente porque el proceso lanzado no tenía su `stdin` redirigido
  (heredaba el pty de la sesión SSH) — añadir `< /dev/null` al comando lo
  resuelve. El proceso remoto en sí arrancaba bien pese al colgado local.
- Al matar `start_person_follower.launch.py` con `pkill -f`, los nodos hijos
  quedaron huérfanos (el `ros2 launch` no llegó a reenviarles la señal de
  parada) — hubo que matarlos uno a uno por PID antes de relanzar.

---

## Sesión 2026-07-17 (trabajo de escritorio, sin robot) — Capítulo 6 redactado + hallazgo de signo confirmado + nuevo hallazgo (sector de obstáculos) sin verificar

### Objetivo: redactar el capítulo 6 de la memoria (implementación), pendiente tras el 16/07

Sin acceso al laboratorio hoy tampoco. Con el capítulo 5 y el fix del
fallback de fusión ya cerrados el 16/07, se abordó el capítulo 6
("Implementación"), el último bloque grande de la memoria que seguía a 0%.

Redactado `docs/06_implementacion.md`: a diferencia del Capítulo 2
(topología — nodos, topics, flujo de datos), este capítulo documenta cómo
está implementado cada nodo *activo* — algoritmos, fórmulas de control,
estructuras de datos — leyendo directamente el código fuente de los siete
nodos registrados en `setup.py` y los valores reales de `config.yaml`, no
una descripción idealizada. Cubre: el DBSCAN propio sobre `cKDTree` y el
filtro geométrico multi-feature de `detection_node` (incluye el gating de
continuidad y la confirmación de fusión rediseñada ayer); el detector dual
HOG/MediaPipe y la lógica de gestos+rumbo de `visual_detection_node`; el
Kalman de 6 estados (modelo de aceleración constante, gate de Mahalanobis
con confirmación por racha, forma de Joseph) y el controlador PD con zona
muerta/arranque suave/evasión reactiva de `tracking_node`; la FSM y la
teleoperación por teclado de `control_node`; y los nodos más simples
(`collision_handling_node`, `user_interface_node`, `slam_node` legado).

**Dos hallazgos no triviales durante la redacción, verificados contra el
código y no solo contra la documentación existente:**

1. **`tracking_node` no implementa DWA real**, pese a que el diagrama del
   Capítulo 2 y el README todavía lo etiquetan como "Kalman + DWA". La
   evasión de obstáculos activa es un método reactivo de campo de
   repulsión, más simple. La implementación real de un Dynamic Window
   Approach (búsqueda en el espacio de velocidades, visualización de
   trayectorias en RViz) existe en el repositorio (`tracking_node/DWA.py`)
   pero **no está registrada en `setup.py`** — es código anterior, no en
   ejecución. Documentado en `docs/06_implementacion.md` §6.5 y §6.11.
   Queda pendiente corregir la etiqueta "DWA" del diagrama del Capítulo 2
   para que no contradiga al Capítulo 6 — no se ha tocado hoy para no
   mezclar el alcance de ambos capítulos en la misma sesión.
2. **Tres nodos más tienen una versión no registrada conviviendo en el
   mismo directorio** (`control_node/C_man.py` y `cierre_seguro.py`,
   `user_interface_node/UI_man.py`), con el mismo patrón que `DWA.py`:
   misma clase, mismo nombre, no importados por nada. Verificado con
   búsqueda textual en todo el repo que ninguno de estos ficheros se
   importa desde otro módulo. Inventariado en §6.11 con una recomendación
   de limpieza (eliminar o mover a un directorio `legacy/`) de cara a la
   entrega final, pero no ejecutada hoy — es una decisión de repositorio,
   no de contenido de la memoria, y se prefirió dejarla para que el autor
   la revise antes de borrar nada.

**Sin verificar por el usuario todavía**, igual que el capítulo 5 — texto
nuevo, pendiente de que Juan lo repase, en particular las dos
observaciones anteriores (confirmar que el DWA real y los ficheros `_man`/
`cierre_seguro` son efectivamente prescindibles antes de limpiarlos).

Actualizados también `docs/01_introduccion.md` §1.5, `README.md` (árbol de
`docs/`) y `docs/sesion_siguiente.md` (tarea 1 ya recoge ambos capítulos).

### Relectura del hallazgo del signo invertido (tarea 2) — confirmado, y hallazgo nuevo sin verificar

Con tiempo de sobra, se abordó también la tarea 2 (opcional): releer con
calma el hallazgo del 13/07 y su corrección del 15/07 (`ang_err` invertido
en el PD angular de `tracking_node`) para confirmar que el razonamiento
del fix convence. **Confirmado** — la corrección del 15/07 está bien
fundamentada: el test directo con `/odom` (bucle abierto, referencia
externa, desacoplado de la propia percepción que se investigaba) es
metodológicamente mucho más fuerte que la simulación offline en bucle
cerrado del 13/07 que llevó a la conclusión contraria. Encontradas además
dos corroboraciones no documentadas hasta ahora: (a) con el convenio de
giro ya confirmado por `/odom`, `ang_err=angle_to` sin invertir es
geométricamente la ley de control correcta, coherente con
`angle_to=atan2(py,px)` en convención estándar; (b) la evasión de
obstáculos del mismo nodo ya usaba esa misma convención sin invertir
(`repulsion += w·(-ang)`) — antes del fix, seguimiento y evasión de
obstáculos usaban convenios de signo incoherentes entre sí dentro del
mismo fichero. Detalle completo de la revisión en la conversación de esta
sesión; no se ha escrito una entrada nueva en `docs/decisiones.md` para
esto porque no cambia ninguna decisión ya tomada, solo la confirma.

**Hallazgo nuevo, sin verificar, encontrado al releer el mismo fichero:**
`tracking_node._obstacle_avoidance` filtra el sector frontal
(`abs(ang)<=50°`) sobre el ángulo crudo de `/scan`, sin aplicar el desfase
de π que `detection_node` sí tiene documentado y corregido desde el 13/07
para ese mismo robot ("persona de frente ≈ π en el láser", RPLIDAR
montado invertido). Si ese desfase aplica igual a todo `/scan` (no hay
motivo aparente para que no sea así, es una propiedad física del montaje
del sensor), la evasión de obstáculos podría estar vigilando el sector
**trasero** en vez del frontal — relevante para seguridad, no solo para
precisión. Documentado como hallazgo sin confirmar, con plan de
verificación barato (obstáculo conocido delante/detrás, revisar el log
`"Obstáculo frontal"`), en `docs/decisiones.md` (2026-07-17) y añadido
como punto 4 de las tareas de `docs/sesion_siguiente.md`, priorizado al
principio de la Sesión 4 por ser barato de comprobar y potencialmente de
seguridad. **No se ha tocado código** — es una hipótesis derivada por
analogía con un hallazgo ya verificado en otro nodo, pendiente de
confirmación real.

### Pendiente para la próxima sesión

Sigue pendiente la Sesión 4 de lab — ahora con un punto añadido al
principio: verificar el sector de `_obstacle_avoidance` (barato, ver
arriba) antes de entrar en el resto (fallback de fusión en vivo + hueco de
detección al girar + gate de continuidad con mobiliario + reproducibilidad
de Capítulo 7). De escritorio sigue pendiente: revisar `DWA.py` y los
ficheros `_man`/`cierre_seguro` legado (decidir limpieza) y corregir la
etiqueta "DWA" del diagrama del Capítulo 2.

---

## Sesión 2026-07-16 (trabajo de escritorio, sin robot) — Capítulo 5 redactado + fix del fallback de fusión diseñado y verificado sintéticamente

### Objetivo: tarea de escritorio nº1 de `docs/sesion_siguiente.md` ("redactar capítulo 5 o 6")

Sin acceso al laboratorio hoy (trabajo). Se eligió el capítulo 5 (estado del
arte) frente al 6 (implementación) por no depender de releer el código en
detalle y poder avanzarse con una revisión bibliográfica.

Redactado `docs/05_estado_del_arte.md` (nuevo): revisión de sistemas de
seguimiento de personas con robots móviles, detección de piernas por LiDAR
2D, estimación de pose por visión (MediaPipe/BlazePose), fusión sensorial
LiDAR-cámara, interacción por gestos, filtros bayesianos de seguimiento
(Kalman), evitación de obstáculos (DWA) y navegación autónoma (SLAM
Toolbox, Nav2). Cada sección conecta la literatura revisada con la decisión
de diseño real tomada en este proyecto (referenciando `docs/02_arquitectura.md`
y `docs/decisiones.md`), en vez de quedarse en una revisión bibliográfica
desconectada del sistema. Incluye una sección de síntesis (5.10) que
resume en qué se diferencia la integración de este TFM de los trabajos
citados, y un listado de referencias con enlaces verificables (14 fuentes:
artículos de revista/conferencia, arXiv y la documentación de SLAM Toolbox/
Nav2/BlazePose).

**Sin verificar por el usuario todavía** — texto nuevo, no releído aún por
Juan. Revisar antes de darlo por cerrado, especialmente las afirmaciones de
la síntesis (5.10) sobre por qué se prefirió cada método frente a las
alternativas, para confirmar que reflejan el razonamiento real y no solo
una justificación a posteriori.

Actualizado también `docs/01_introduccion.md` §1.5 (capítulo 5 ya no
"pendiente"), `README.md` (árbol de `docs/`) y `docs/sesion_siguiente.md`
(tarea 1 de la lista de escritorio marcada como hecha).

### Objetivo: tarea de escritorio nº3 de `docs/sesion_siguiente.md` ("diseñar el fix del fallback de fusión")

Con el capítulo 5 encarrilado, se atacó también la tarea 3 — puramente
código + verificación sintética, no necesita el robot — para dejarla lista
antes de la Sesión 4 de lab.

**Cambios en `person_follower/detection_node/detection_node.py`:**

- Nuevo `_filter_by_drift(positions, now)`: extrae el filtro de deriva
  acumulada (ventana `continuity_window_s`) que antes vivía dentro de
  `_gate_by_continuity`, ahora compartido por los dos caminos de gating.
- Nuevo `_confirm_fusion_candidate(candidate, now)`: exige
  `continuity_confirm_frames` scans consecutivos con el candidato en el
  mismo sitio (tolerancia `position_jump_margin`) antes de aceptarlo,
  **siempre** — no solo cuando falla el chequeo de velocidad plausible,
  que era el hueco que dejaba colarse mobiliario cercano (hallazgo
  13/07). Solo se usa en el camino de fusión cámara+LIDAR; los pares de
  piernas siguen usando `_gate_by_continuity` sin cambios.
- `detect_person`: el bloque de fallback de fusión ya no llama a
  `_gate_by_continuity` — calcula el mejor candidato por desviación
  angular como antes, pero la aceptación final pasa por
  `_confirm_fusion_candidate`.
- Nuevo estado: `_fusion_confirm_streak`, `_fusion_pending_candidate`
  (separados de `_continuity_reject_streak`/`_pending_reanchor`, que
  siguen siendo solo del camino de piernas — evita que un candidato de
  fusión interfiera con una racha de piernas en curso, y viceversa).

**Verificación:** `validation/verify_fusion_confirm.py` (nuevo, sin ROS).
Réplica exacta de la lógica (`FusionGateSim`) porque este portátil no tiene
`rclpy` (ver sesión 09/07 más abajo). Reproduce el caso real documentado
el 13/07 (mueble a 1.34m tras 0.92s de hueco) y confirma: (a) con el
mecanismo anterior se colaba en el primer scan, (b) con el nuevo, no se
acepta hasta el 3er scan consecutivo con `continuity_confirm_frames=3`,
(c) ruido disperso nunca acumula racha, (d) una persona real se confirma
exactamente en el scan N, (e) con el valor por defecto
(`continuity_confirm_frames=1`) el comportamiento es idéntico al anterior
— sin latencia añadida si nadie sube el parámetro, (f) el camino de piernas
no cambia. Las seis pruebas pasan (`python validation/verify_fusion_confirm.py`
→ `TODO OK`, exit 0). Detalle completo, motivo y alternativas descartadas
en `docs/decisiones.md` (2026-07-16).

**Sin verificar en el robot/con datos reales todavía** — es lógica
aislada. La Sesión 4 (`docs/sesion_siguiente.md`) sigue necesitando probar
esto en vivo (o contra un rosbag) antes de darlo por cerrado, y sigue
pendiente el hueco de detección conjunta LIDAR+cámara al girar (hallazgo
del 15/07), que la Sesión 4 también cubre.

### Pendiente para la próxima sesión

Este trabajo de escritorio no consumió tiempo de robot. La Sesión 4 de lab
(`docs/sesion_siguiente.md`) ahora tiene el fix del fallback de fusión ya
implementado y verificado sintéticamente — solo falta sincronizar
(`bash sync_nuc.sh`) y probar en vivo. Sigue pendiente el resto de la
Sesión 4 (hueco de detección al girar, gate de continuidad con mobiliario
denso, reproducibilidad de Capítulo 7). Capítulo 6 (implementación) y la
relectura del hallazgo de π/signo (tarea 2 de escritorio) siguen sin hacer.

---

## Sesión 2026-07-15 (lab, en curso) — Puerto USB kobuki/rplidar intercambiado + diagnóstico del "gira al lado contrario"

### Objetivo: Sesión 3 del plan (confirmar fix de π con movimiento + near_gain + recalibrar cámara)

### Arranque: kobuki y RPLIDAR habían intercambiado de puerto USB

Al lanzar el stack, `rplidar_node` moría con "operation time out". Diagnosticado:
`kobuki_node_params.yaml` tiene hardcodeado `device_port: /dev/ttyUSB0`, pero en este
arranque la reenumeración USB asignó ttyUSB0 al adaptador CP2102 (el mismo que usa
`/dev/rplidar`) y ttyUSB1 a la base Kobuki (confirmado con
`/dev/serial/by-id/`: `usb-Silicon_Labs_CP2102...→ttyUSB0`,
`usb-Yujin_Robot_iClebo_Kobuki...→ttyUSB1`) — kobuki_node intentaba hablar con el
LIDAR. Solucionado relanzando `kobuki_ros_node` con
`-p device_port:=/dev/serial/by-id/usb-Yujin_Robot_iClebo_Kobuki_kobuki_AH02IGFT-if00-port0`
(ruta estable, no depende del orden de enumeración) en vez del launch file por
defecto. No es un cambio de código del repo — solo afecta a cómo se lanza kobuki_node
en el NUC; anotar en `docs/sesion_siguiente.md` para no repetir el diagnóstico.

### Objetivo 1 (confirmar fix de π con movimiento real): fix de π confirmado, pero aparece un problema más grave

Grabación de 74s (`validation/runs/20260715_sesion3_pi_movimiento/`) con la persona
moviéndose/girando alrededor del robot. El fix de π del 13/07 **se sostiene**: cuando
LIDAR y cámara coinciden, `dev_deg` se queda en 5-20° (ya no pegado a ±180°). Pero
durante la prueba el usuario reportó en vivo "gira al lado contrario y se desorienta"
— el mismo síntoma investigado y descartado el 13/07. Métricas globales de la toma:
error angular medio 103.7°, saturación de `|vang|` 50.2% del tiempo — mucho peor que
el caso fácil ya confirmado.

Diagnóstico inicial (con evidencia de log, ver `docs/decisiones.md` 2026-07-15):
**LIDAR y cámara pierden a la persona a la vez al girar** — un mecanismo real y
confirmado, ver detalle abajo. El emparejamiento de piernas del LIDAR
(`min_leg_distance`/`max_leg_distance`, 0.04-0.35m) falla cuando una pierna ocluye a
la otra o la separación se sale de rango; la detección de pose de MediaPipe puede
fallar un frame puntual por motion blur, y el debounce (`camera_debounce_count=2` a
~2.5Hz de proceso) convierte ese frame suelto en ~800ms+ de "cámara no válida". Ambas
fallan a la vez porque las dos modalidades comparten el mismo punto ciego (vista
frontal de la persona). Hueco real observado: ~3.6s sin ninguna detección
(1784124266.95-1784124270.55).

**Corrección aplicada tras este diagnóstico (mitigación parcial, no la causa
principal):** añadido `extrapolation_limit_s=0.6` en `tracking_node` (parar en vez de
seguir extrapolando con Kalman pasado ese tiempo sin observación fresca, antes eran
hasta 2.0s) y bajado `camera_debounce_count` de 2 a 1. Sincronizado y relanzado en el
NUC. **Repetido el test de movimiento con estos cambios y el usuario reportó
en vivo que seguía sin funcionar ("PARA, NO FUNCIONA")** — los datos de ese segundo
test (`validation/runs/20260715_verif_fix_extrapolacion/`) mostraron `obs_age` bajo
casi todo el tiempo (sin huecos largos esta vez) pero el ángulo seguía divergiendo
igualmente — es decir, el mecanismo de "huecos de detección" no era la causa
dominante del síntoma.

### CAUSA RAÍZ REAL encontrada y corregida: signo invertido en el PD angular

Con dos síntomas distintos (huecos de detección Y divergencia con datos frescos)
apuntando al mismo síntoma final, se hizo una verificación directa del signo de
`wz`: publicar `angular.z` constante en `/commands/velocity` (bypass total de
percepción y control) y medir el `yaw` real vía `/odom`. Resultado, dos ensayos:
`wz_cmd=+0.5` → yaw sube +18.7°; `wz_cmd=-0.5` → yaw baja -23.8°. **Mismo signo que
el comando** — este robot sigue el convenio estándar de ROS, al contrario de lo
concluido el 13/07 (que se basó en una simulación offline, sin medir el robot real).
`tracking_node.py` tenía `ang_err = -angle_to`; corregido a `ang_err = angle_to`.
Detalle completo, incluyendo por qué la simulación del 13/07 no lo detectó, en
`docs/decisiones.md` (2026-07-15).

**Verificado en vivo tras el fix** (`validation/runs/20260715_verif_signo/`, paso
lateral corto y controlado): `angle_deg` se mantuvo entre -18° y +14° durante toda
la toma (18.7s), sin ningún disparo ni envoltura en ±180°. Error angular medio 8.7°
(antes 103.7° y 41.3° en los dos tests fallidos de hoy), saturación de `|vang|` 0.0%
(antes 50.2% y 19.4%), 100% detección, 0 pérdidas, 0 saltos de posición. `vang`
responde de forma suave y proporcional, convergiendo hacia 0 según la persona vuelve
a quedar de frente — comportamiento de control estable, coherente con el signo ya
corregido.

Objetivo 1 del plan original (confirmar el fix de π) queda cerrado: el fix de π
seguía siendo correcto, y el síntoma de "gira al lado contrario" reportado hoy (y
originalmente el 13/07) tenía una causa distinta y más fundamental, ya corregida y
verificada. El diagnóstico de huecos de detección LIDAR+cámara al girar sigue siendo
real y documentado como limitación pendiente (ver `docs/decisiones.md`), pero ya no
es crítico con el signo corregido.

### Objetivo 2 (near_gain): aislado con el signo ya corregido — comportamiento sano

Dos tomas adicionales tras el fix de signo:

- `validation/runs/20260715_near_gain_v4_signo_fix/` (distancia 1.38-2.12m, no llegó
  a la zona de `near_gain`): error angular medio 6.4°, 0% saturación, 0 pérdidas,
  100% detección — seguimiento general ya muy estable.
- `validation/runs/20260715_near_gain_v5_close/` (distancia 0.49-0.86m, sí dentro de
  la zona objetivo): error angular medio 34.3°, saturación de `|vang|` 5.0%, 89.1%
  detección (3 pérdidas). `angle_deg` se mueve entre -52° y +52° durante toda la
  toma — **acotado, sin ningún disparo a ±180°**, y siempre con el signo correcto
  (vang converge hacia el signo que reduce el error). La saturación puntual es
  esperable: `near_gain = min(1.0, distance/target_dist)` con `target_dist=1.0m` ya
  reduce `wz` a la mitad a 0.5m, pero un giro rápido de la persona a esa distancia
  todavía puede saturar el PD antes de que `near_gain` termine de amortiguarlo — es
  una dificultad física real del seguimiento de cerca (el mismo desplazamiento
  lateral cambia el ángulo mucho más deprisa cuanto más cerca), no un bug. Candidato
  a ajuste fino en una sesión futura (bajar `angular_gain` a distancias <0.7m, o
  hacer que `near_gain` decaiga más agresivo), pero no bloquea nada.

### Objetivo 3 (recalibrar cámara SPCA2650): cerrado sin cambios — no hace falta

Antes de montar una prueba dedicada, se revisó `dev_deg` (desviación entre el rumbo
de cámara y el clúster LIDAR elegido) agregando las ~2600 muestras de fusión de
todas las pruebas de hoy (ya con los fixes de π y de signo aplicados): mediana 3.2°,
media 5.0°, rango 0.0-24.9°. Frente a los ~9-10° medidos el 13/07 con esta misma
cámara SPCA2650 (antes de los fixes de hoy), la mejora es clara — gran parte de esa
desviación de 13/07 era arrastre de los bugs de π/signo contaminando el cálculo de
`theta_target`, no una mala calibración de `bearing_sign`/`camera_hfov_deg` en sí.
Con el usuario decidido: no se toca `bearing_sign=-1.0` ni `camera_hfov_deg=51.0`
(sigue siendo el valor nominal de la C270, no recalibrado específicamente para la
SPCA2650, pero funciona empíricamente bien) — no se justifica una prueba dedicada
hoy. Si en sesiones futuras `dev_deg` vuelve a crecer de forma sostenida, revisar
esto primero.

### Extra (adelanto de la Sesión 5): 8 grabaciones para el Capítulo 7

Con el sistema ya estable, se adelantó parte de la Sesión 5 — una toma por cada
escenario de `validation/README.md` (recta, curva, parada, corto, oclusión,
obstáculo), más dos repeticiones de oclusión/obstáculo. Bags y análisis en
`validation/runs/20260715_<escenario>[_v2][_signo_fix|_breve]/`.

- **`recta`, `curva`, `parada`, `corto`:** comportamiento sano, sin sorpresas.
  Nota: `curva_signo_fix` reportó "0.2s / 4 muestras" de telemetría en el resumen
  de `plot_run.py` pese a tener 302 pares de posición — parece un artefacto del
  script (desajuste entre el conteo de `telemetry.csv` y `position.csv`), no un
  problema de control; revisar `plot_run.py` si se repite en sesiones futuras.
- **`obstaculo` (1ª toma):** a los 7.5s, con la cámara sin ver a la persona
  (oculta cerca del obstáculo), el fallback de fusión enganchó momentáneamente
  el propio obstáculo como candidato (salto de posición a 3.35m y luego a
  0.37m), causando `angle_deg` hasta -69° y `vang` saturado ~3s antes de
  recuperarse solo y re-enganchar bien a la persona. **No es un bug nuevo** —
  es la manifestación directa, con evidencia de log clara, del fallo ya
  documentado (fallback de fusión sin confirmación obligatoria para candidatos
  fuera del par de piernas, ver diagnóstico de arriba y Sesión 4). `obstaculo_v2`
  (repetición) salió limpio: ángulo acotado -19° a +22°, sin saturación,
  evasión suave — buena toma de referencia para el Capítulo 7, con la primera
  toma como evidencia documentada de la limitación.
- **`oclusion` (1ª toma):** hueco real de ~27s sin telemetría mientras la
  persona estaba oculta — el robot se quedó parado correctamente
  (`extrapolation_limit_s` en efecto) y no hizo nada raro, solo que la
  publicación de telemetría se corta junto con el movimiento durante la espera
  (por diseño del fix de hoy, no es un bug). Repetido con una ocultación más
  breve (`oclusion_v2_breve`): esta vez la persona nunca llegó a "perderse"
  del todo (100% detectada) pero la posición fusionada saltó varias veces
  cerca del obstáculo (`angle_deg` picos de hasta -98°, una lectura anómala a
  0.11m), siempre recuperándose sola — el mismo fallo de fusión sin confirmar
  que en `obstaculo`, disparado repetidamente por la cercanía al obstáculo.
- **Conclusión:** las 8 tomas, tomadas en conjunto, son buena evidencia para el
  Capítulo 7 tanto del comportamiento normal (ya sano tras el fix de signo)
  como de la limitación conocida y pendiente (fusión sin confirmar cerca de
  objetos) — no hace falta descartarlas, documentar ambas cosas con datos
  reales es más honesto que solo mostrar los casos limpios.

## Sesión 2026-07-13 (lab) — Fix de CPU, causa raíz de la oscilación FSM, y bug de convenio angular en tracking_node

### Objetivo: Sesión 2 del plan (FSM oscilando + near_gain + recalibrar cámara)

### Fix de rendimiento: detection_node saturaba un core de CPU (93.7%)

Antes de tocar la FSM, perfilado en vivo (`ps aux`/`top`) reveló que `detection_node`
consumía el 93.7% de un core del NUC — casi sin margen respecto al periodo real de
`/scan` (11.4Hz, ~87.7ms). Medido con un script standalone en el propio NUC
(mismo tamaño de scan real, n=1080): pipeline completo 80.2ms, de los cuales
`apply_median_filter` (bucle Python con una llamada a `np.median` por punto)
se llevaba 56.5ms (70%). Vectorizado con `scipy.ndimage.median_filter`
(bordes recalculados aparte para reproducir el comportamiento exacto, sin
relleno). Verificado con 500 pruebas sintéticas (varios `window_size`/tamaños)
+ caso real: 0 discrepancias. Desplegado y confirmado en vivo: CPU
93.7% → 27.3%, detección sin cambios (mismo streak continuo, mismas
posiciones). Ver `docs/decisiones.md`.

### Causa raíz de la oscilación FSM: reproducida en vivo, no era (solo) lo que se sospechaba

Con el gesto real, la FSM osciló TRACKING↔IDLE ~14 veces/min. Secuencia
diagnosticada con logs en vivo: al gesticular, el propio movimiento del brazo
desincroniza LIDAR y cámara durante ~2s reales (no un parpadeo de un frame).
Durante ese hueco, el fallback de fusión cámara+LIDAR enganchó clústeres
espurios de mobiliario a 2.6-2.9m — porque **el candidato entra dentro del
radio "plausible" de `max_person_speed` (2.0 m/s) y nunca pasa por el
mecanismo de `continuity_confirm_frames`**, que solo actúa sobre candidatos
ya rechazados como implausibles. Verificado sintéticamente: subir
`continuity_confirm_frames` de 1 a 2-3 **no soluciona nada** (probado, 0
cambio de resultado) — la solución real requeriría exigir confirmación
siempre en el fallback de fusión, no solo cuando falla el chequeo de
velocidad. Aplazado a la próxima sesión (cambio delicado del gate).

También se descubrieron **tres timeouts independientes y descoordinados**
en tres nodos distintos: `detection_node` (`detection_confirm_frames=3`/
`detection_loss_frames=8`, este último subido de 4 a 8 en una sesión
anterior sin quedar documentado en este diario — comentario en
`config.yaml:81`), `control_node` (`tracking_loss_timeout=1.5s`), y
`tracking_node` (`self.timeout_s=2.0` **hardcodeado, ni siquiera parámetro
de ROS**). Parametrizado hoy como `observation_timeout` en `config.yaml`
(mismo valor por defecto, sin cambio de comportamiento) para que quede
documentado junto a los otros dos.

### Hallazgo mayor: tracking_node no aplica el mismo convenio angular que detection_node

Al repetir `near_gain` (grabado dos veces: con gesto y activando por SSH sin
gesto para evitar la disrupción del brazo) apareció algo más grave que
`near_gain` en sí: el error angular (`angle_deg` en `telemetry.csv`) **no
converge nunca**, se queda oscilando pegado a ±180° durante toda la toma
(42s), con `|vang|` saturado el 71-76% del tiempo en un patrón de onda
cuadrada — incluso en la segunda toma, mucho más limpia (sin los saltos de
posición espurios de la primera: 0.4% saltos >0.8m vs 1.5%, máx 0.93m vs
3.38m).

Confirmado con la persona físicamente delante del robot a 1m (verbal, sin
ángulo): `/person_position` publica `x` **negativo** (`x=-1.18, y≈-0.008`).
Esto no es un bug de `detection_node` — su propio código lo documenta y
compensa explícitamente: `detection_node.py:431`, *"Persona de frente ≈ π en
el láser (TF base→laser con yaw=π)"*, usado correctamente en el cálculo de
`theta_target` del fallback de fusión. Pero **`tracking_node.py:283`
(`angle_to = math.atan2(py, px)`) no aplica ese mismo desfase de π** — su
zona muerta y PD angular tratan `angle_to≈0` (es decir, `px` positivo) como
"persona delante", cuando el convenio real del láser dice que delante es
`≈π`. Esto explica el error angular pegado a ±180° sin converger y la
saturación en onda cuadrada (chattering en la singularidad antipodal, donde
un ruido mínimo decide "girar por la izquierda o la derecha").

**Importante — no se rompe el sistema:** el usuario confirma que en uso
normal el seguimiento es "estable pero lento", no está roto. La hipótesis de
cierre de hoy es que este desfase de convenio explica la lentitud/rigidez
del giro (el `near_gain`/acoplamiento wz-vx atenúan un error que
estructuralmente nunca debería ser tan grande) y los episodios de
oscilación/saturación en casos límite (como el propio `near_gain`, donde la
persona quedó casi exactamente antipodal), más que un sistema que no
funciona en absoluto. **No se ha tocado el código de `tracking_node` para
esto hoy** — es un cambio delicado del lazo de control angular, que merece
revisión cuidadosa (incluyendo repasar si hay una transformación TF real
`base_link→laser` con yaw=π en el URDF que debería aplicarse de forma
consistente en todos los nodos, en vez de un offset manual solo en
`detection_node`). Máxima prioridad de la próxima sesión — ver
`docs/sesion_siguiente.md`.

Test adicional de verificación de convenio de `wz`: publicado
`angular.z=+0.15` directo a `/commands/velocity` (bypass de todo el control),
robot giró hacia la izquierda (observación visual del usuario) — dato
recogido pero no concluyente por sí solo sobre el convenio de signos sin
una referencia externa fija; el hallazgo decisivo fue el comentario de
`detection_node.py:431` contrastado con el código de `tracking_node.py`.

### Datos recogidos (bags en el NUC, no copiados al repo por peso)

- `near_gain_20260713` (con gesto, contaminado por el bug de fusión — 8
  pérdidas de detección, salto máx 3.38m).
- `near_gain_v2_sin_gesto` (activado por SSH, mucho más limpio — 3 pérdidas,
  salto máx 0.93m — pero reveló el bug de convenio angular).
- CSVs y figuras de ambas en `validation/runs/20260713_near_gain_analysis/`
  y `validation/runs/20260713_near_gain_v2_analysis/` (sí están en el repo,
  son ligeros).

### Otro fix menor: pipeline de validación desactualizado en el NUC

`validation/bag_to_csv.py` y `validation/plot_run.py` en el NUC estaban
desincronizados desde la sesión de escritorio del 09/07 (`validation/` no
está cubierto por `sync_nuc.sh`, que solo sincroniza los tres archivos de
`person_follower/`). Sincronizado manualmente hoy para poder extraer
`position.csv`/`expected_position.csv` de los bags grabados.

### Addendum (misma sesión, hora extra): fix del desfase de π implementado y confirmado

No se dejó para la próxima sesión — con tiempo extra el mismo día se decidió
el enfoque, se implementó y se verificó en vivo. Confirmado: no existe una
TF real `base_link→laser` (`/tf_static` vacío, `tf2_echo` dice que el frame
"laser" no existe) — el "yaw=π" era solo una convención de facto en un
comentario. Único consumidor funcional de `/person_position` es
`tracking_node` (`DWA.py` es una implementación alternativa no usada en el
launch). Fix aplicado en el origen: `detection_node._publish_person_position`
ahora invierte el signo de `x,y` **solo en la frontera de publicación**
(`Point(x=-xy[0], y=-xy[1])`), dejando todo el estado interno (gating,
`_position_history`, fallback de fusión) sin tocar, en el frame bruto del
láser de siempre. No hizo falta cambiar `tracking_node` — su `atan2` ya
asumía el convenio estándar, solo estaba recibiendo datos en el convenio
equivocado.

**Verificado en vivo tras el fix** (persona delante confirmada, ~1.3m,
activado por SSH sin gesto): `/person_position` publica ahora `x` positivo
(antes negativo). `angle_deg` en telemetría se mantiene estable en 5.5-6.8°
(dentro de la zona muerta ±8°) en vez de pegado a ±180°. `vang` prácticamente
en 0 (0.001-0.002 rad/s) en vez de saturado 71-76% del tiempo. Robot parado
con `stop_tracking` tras la prueba.

**Pendiente real para la próxima sesión:** retest limpio de `near_gain` y
de la oscilación FSM ahora que el control angular converge de verdad —
las dos tomas de hoy quedaron contaminadas por este bug, así que sus
métricas (saturación 71-76%, MAE de distancia) no son representativas del
sistema corregido. También sigue pendiente el fix del fallback de fusión
(mobiliario colándose) y la recalibración de cámara.

**Prueba adicional con movimiento real (tras el fix, mismo día):** con
TRACKING activo y la persona moviéndose, el seguimiento funcionó bien
(consistente con la mejora del fix) hasta que la persona se acercó a
**~0.24m del robot** (`dist: 0.24` en el log) — a esa distancia la detección
se perdió de verdad durante ~1s (LIDAR y cámara sin ver a la persona,
puntos ciegos conocidos a corta distancia), disparando el
`observation_timeout` de `tracking_node` y la transición a IDLE. Al
recuperar la posición, la persona apareció al lado contrario (giro del
robot o rodeo muy cercano). **Esto no es un efecto secundario del fix de
hoy** — es el problema de robustez a muy corta distancia ya documentado y
aplazado para la Sesión 4 (gate de continuidad + fallback de fusión).
Confirma que ese sigue siendo el pendiente correcto, no algo nuevo.

### Confirmación adicional del fix de π con movimiento real (19s, TRACKING activo)

Grabación `pi_fix_movimiento_20260713`: TRACKING activo 19.1s sin ningún
timeout ni pérdida de FSM, terminado por gesto de stop deliberado. Frente a
la toma equivalente de antes del fix (`near_gain_v2_sin_gesto`):

| Métrica | Antes del fix | Después del fix |
|---|---|---|
| Error angular medio | 159.7° | **21.4°** |
| % saturación `\|vang\|≥0.95` (global) | 74.3% | **0.0%** |

La gráfica de error angular muestra convergencia limpia: arranca cerca de
±180° (persona aún posicionándose el primer segundo) y converge de forma
suave y monótona a 0° en ~6s, manteniéndose ahí estable el resto de la
toma pese al movimiento real de la persona. `vang` corrige de forma suave,
sin ningún pico de saturación. CSVs/figuras en
`validation/runs/20260713_pifix_movimiento_analysis/`. (Distancia mínima de
nuevo 0.24m con 5 pérdidas de detección — mismo problema de corta distancia
ya documentado arriba, no relacionado con este fix.)

### Investigación descartada: posible bug de izquierda/derecha en tracking_node

Tras el fix de π, el usuario probó de cara al robot y reportó: al dar un
paso a su derecha, el robot giró "al lado contrario" en vez de seguirle, y
después se desorientó (varias vueltas erráticas). Investigado a fondo:

1. Confirmado empíricamente (persona quieta delante, luego un paso a su
   derecha): `/person_position.y` pasa de ≈0 a positivo (+0.70). Verificado
   por geometría que esto es el convenio esperado (persona a su derecha =
   lado izquierdo del propio robot, relación espejo cuando están cara a
   cara) — el signo de `y` es correcto, no es un bug.
2. Simulación numérica pura (réplica exacta de las fórmulas de
   `tracking_node.py`: zona muerta, PD, rate-limit) usando los ángulos
   reales de la toma `pi_fix_movimiento_20260713`: con el convenio estándar
   de ROS (giro antihorario = `wz` positivo), el código actual
   (`ang_err = -angle_to`) **nunca converge** en la simulación — oscila sin
   asentarse, coincidiendo con la sensación de "vueltas erráticas". Pero
   probando la simulación asumiendo que el giro físico real de este robot
   está invertido respecto al estándar ROS, el mismo código **sí converge**
   limpiamente, reproduciendo los números reales observados (-169°→-8° en
   ~4s, igual que la toma real).
3. Como la prueba en vivo de antes **sí convergió de verdad** con el código
   tal cual está (sin tocarlo), eso es la evidencia decisiva: este robot
   gira en sentido contrario al estándar ROS, y `ang_err = -angle_to` ya
   compensa correctamente ese hecho — **no es un bug, no se toca.**
4. Conclusión: lo que se percibió como "giro al lado contrario" es
   probablemente el efecto espejo normal (cara a cara, mi derecha es su
   izquierda) combinado con pérdidas reales de detección — en el log de esa
   franja horaria (~17:00-17:05h) hay varios ciclos TRACKING→IDLE con
   "Timeout observación" real, el problema de corta distancia/gate de
   continuidad ya documentado y aplazado para la Sesión 4, no algo nuevo.

Script de simulación en el scratchpad de esta sesión (no en el repo, es
desechable) — si se quiere repetir el análisis, reproducir con las fórmulas
exactas de `_on_scan` en `tracking_node.py`.

### Pendiente para la próxima sesión

Ver bloque "OBJETIVO de la Sesión 3" (reescrito) en `docs/sesion_siguiente.md`.

---

## Sesión 2026-07-09 (lab, tarde) — Gesto real funcionando + fixes en vivo

### Objetivo: cámara/gesto (Sesión 1 del plan), improvisado sobre la marcha

Sesión no planificada inicialmente (la Sesión 1 formal requería reencuadrar
la C270 físicamente) — el usuario tenía acceso al lab y se decidió atacar el
bloqueante del gesto con las herramientas disponibles por SSH primero.

**Gesto arreglado:** `gesture_min_visibility` 0.6→0.5 (la geometría ya era
correcta desde el diagnóstico por `[GESTO-DBG]`; la visibilidad de la
muñeca, sobre todo la izquierda, se quedaba pegada al umbral). Además, el
usuario cambió físicamente la cámara C270 por una SPCA2650 a mitad de
sesión (reinicio del NUC incluido). Con ambos cambios, **los gestos de
inicio (mano derecha) y parada (mano izquierda) se dispararon de forma
repetida y fiable** en varias tomas grabadas — primera vez que el objetivo
específico 1 del TFM funciona sin el workaround manual por SSH. Detalle y
verificación en `docs/decisiones.md`.

### Bug real encontrado y corregido: barrido/deriva del gate de continuidad

Con el gesto ya activando el seguimiento, apareció un problema nuevo: con la
persona *quieta*, el robot se ponía a "dar vueltas sobre sí mismo" — la
posición detectada barría un círculo completo alrededor del robot en 1-2s.
Diagnosticado en el código (`detection_node._gate_by_continuity`): el gate
solo miraba el salto respecto al frame anterior, así que una cadena de
clústeres espurios adyacentes (patas de una silla, confirmado por el
usuario: "se ha liado con una silla") podía "caminar" de uno a otro sin que
ningún paso individual pareciera implausible. Fix: límite adicional de
deriva acumulada respecto a la posición confirmada de hace
`continuity_window_s` segundos (nuevo parámetro, 1.0s). Verificado con
lógica aislada (sin ROS, portátil sin entorno ROS disponible) y confirmado
en vivo: la toma siguiente ya no repitió el barrido. Detalle completo en
`docs/decisiones.md`.

### Arranque brusco: diagnosticado como comportamiento correcto, suavizado igualmente

El usuario reportó que el robot "se volvía loco" al arrancar. Con datos
reales extraídos del bag `camara_nueva_velred` (usando `bag_to_csv.py` en el
propio NUC, que sí tiene ROS — cierra el círculo del trabajo de esta mañana
sobre el pipeline de métricas): el ángulo a la persona al activar el gesto
era de -157.9° (casi detrás del robot), y el rate-limit de `wz`
(`ang_acc_limit`, del fix del 08/07) ya funcionaba como estaba diseñado,
saturando a ±1.0 rad/s en ~0.3s de forma gradual, no de golpe. No era un bug
de control, sino un giro de corrección grande pero correcto. Se añadió
igualmente un arranque suave (`startup_ramp_s=1.5s`, `startup_max_wz=0.5`)
que limita `wz` a un techo más bajo justo tras activar, para que la
corrección inicial se sienta menos brusca aunque el punto de partida
angular sea malo. Confirmado por el usuario: prueba siguiente sin fallos.

### Otros cambios de sesión

- `max_speed` 0.3→0.18 m/s (petición explícita, pruebas más suaves).
- Establecido un protocolo operativo: enviar `stop_tracking` explícito por
  SSH tras cada prueba, para que el seguimiento no se reactive solo al
  detectar de nuevo a la persona (comportamiento ya conocido de la FSM desde
  el 17/06).
- NUC reiniciado una vez (para que el sistema reconociera la cámara nueva) —
  recuperado sin incidencias, stack completo relanzado.

### Pendiente / observado sin resolver

- **Oscilación de la FSM** (TRACKING↔IDLE cada pocos segundos con detección
  intermitente) sigue viva — reproducida varias veces hoy, no es nueva ni
  causada por los cambios de hoy. Sigue pendiente de sesión dedicada.
- `camera_hfov_deg`/`bearing_sign` (calibrados con la C270) no reverificados
  con la cámara nueva — revisar si `dev_deg` en los logs de fusión se ve
  sistemáticamente desviado.
- Bags de esta sesión (`gesto_real_20260709`, `_v2`, `_v3`, `gesto_izq_test`,
  `gesto_real_v4_fix`, `camara_nueva_velred`) quedaron en
  `~/tfm_bags/` del NUC, no copiados al repo (pesan, ver `.gitignore` de
  `validation/`) — pendiente decidir cuáles vale la pena traer para el
  Capítulo 7.

---

## Sesión 2026-07-09 (trabajo de escritorio, sin robot)

### Objetivo: reproducibilidad de las métricas de saltos/saturación (Sesión 3 de `docs/sesion_siguiente.md`)

Sin acceso al laboratorio hoy. Se confirmó primero que no hay acceso al lab
en agosto (ver commit anterior de hoy, `docs/sesion_siguiente.md`): las 9
sesiones planificadas son todo el tiempo de robot restante, no "julio con
margen detrás".

Con eso claro, se adelantó trabajo de escritorio de la Sesión 3: las cifras
de "% saltos >0.8m" y "% saturación angular" de la tabla 7.4
(`docs/07_resultados.md`) se calcularon el 08/07 con un script *ad-hoc*
(`bag_to_csv_direct.py`) que no se commiteó y ya no está disponible. Se
descubrió que el dato crudo que hacía falta (`/person_position`) **ya se
graba en todos los bags** vía `record_run.sh` — solo faltaba que
`bag_to_csv.py` lo extrajera. Cambios:

- `validation/bag_to_csv.py`: extrae `/person_position` y
  `/expected_person_position` a `position.csv`/`expected_position.csv`.
- `validation/plot_run.py`: si existe `position.csv`, añade a `metrics.txt`
  el % de saltos de posición cruda (umbral configurable, `--jump-threshold`,
  def. 0.8m) y el % de saturación angular (`--sat-threshold`, def. 0.95)
  tanto global como restringido a instantes con posición "estable" (sin
  variación mayor que `--stable-radius` en la ventana `--stable-window`).
  Degrada con un aviso (no falla) si `position.csv` no existe, para no
  romper el análisis de bags antiguos generados con la versión anterior del
  script.

Detalle completo, metodología y alternativas descartadas en
`docs/decisiones.md` (entrada 2026-07-09).

### Verificación: solo pruebas de lógica aisladas, sin ROS ni datos reales

Este portátil no tiene `rclpy`/`rosbag2_py` instalados, así que no se pudo
ejecutar `bag_to_csv.py` contra los bags reales de `validation/runs/`. Se
verificó la lógica nueva de `plot_run.py` con CSVs sintéticos construidos a
mano (una persona quieta con un salto espúreo intercalado + un tramo
caminando de forma continua): el % de saltos y el % de saturación con
posición estable salieron con los valores esperados a mano. **Pendiente de
validar con datos reales** — no asumir que las cifras nuevas reproducirán
exactamente la tabla 7.4 hasta re-ejecutar el pipeline actualizado sobre los
tres bags del 08/07 en una máquina con ROS 2 (ver `docs/sesion_siguiente.md`,
Sesión 3).

### Pendiente para la próxima sesión de lab (Sesión 1: cámara)

No cambia respecto a lo ya planificado — este trabajo de escritorio no
consumió tiempo de robot ni tocó la prioridad de la Sesión 1 (re-encuadrar
la C270 y validar el gesto real). Ver `docs/sesion_siguiente.md`.

---

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
