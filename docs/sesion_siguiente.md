# Prompt — Próxima sesión

## Tareas de escritorio para mañana (sin robot, sin acceso al lab)

Pendientes de la sesión de lab del 2026-07-13 que no requieren el robot —
se pueden hacer en cualquier máquina con este repo, incluida la de casa:

1. ~~**Redactar capítulo 5 (estado del arte) o 6 (implementación) de la
   memoria**~~ — **✅ hecho 2026-07-16 (trabajo de escritorio, ambos
   capítulos):** redactados `docs/05_estado_del_arte.md` (14 referencias
   bibliográficas verificables) y `docs/06_implementacion.md` (detalle real
   de algoritmos/fórmulas de cada nodo activo, a partir del código fuente
   — incluye el hallazgo de que `tracking_node` no implementa DWA real
   pese a lo que dice el Capítulo 2/README, y un inventario del código
   legado no registrado en `setup.py`). Ambos pendientes de revisión por
   el autor antes de darlos por cerrados.
2. ~~**Revisar el hallazgo del "posible bug izquierda/derecha"**~~ — **✅
   hecho 2026-07-17.** Nota: esta entrada quedó desactualizada — la
   conclusión del 13/07 aquí descrita (`ang_err=-angle_to` correcto,
   "robot gira al revés del estándar ROS") **fue revertida el 15/07** tras
   una verificación directa con `/odom` (ver `docs/decisiones.md`,
   2026-07-15): el robot sí sigue el convenio estándar, y el código
   correcto es `ang_err=angle_to` (ya aplicado). La revisión de hoy
   confirma que el razonamiento del fix del 15/07 es sólido — evidencia
   convergente de varias fuentes independientes (test `/odom` en bucle
   abierto, consistencia geométrica con la evasión de obstáculos, incluso
   el propio test visual del 13/07 que se descartó entonces por "no
   concluyente" apuntaba ya en la dirección correcta). No reabrir esta
   duda. De paso, revisando el mismo fichero, salió un hallazgo nuevo y
   distinto — ver punto 4.
3. ~~**Diseñar el fix del fallback de fusión**~~ — **✅ hecho 2026-07-16
   (trabajo de escritorio):** implementado en `detection_node.py`
   (`_confirm_fusion_candidate` + `_filter_by_drift`, ver
   `docs/decisiones.md` 2026-07-16) y verificado con
   `validation/verify_fusion_confirm.py` (sin ROS, réplica exacta de la
   lógica — reproduce el caso real del 13/07, mueble a 1.34m tras 0.92s de
   hueco, y confirma que ya no se cuela). **Pendiente para la Sesión 4:**
   sincronizar (`bash sync_nuc.sh`) y validar en vivo o con un rosbag antes
   de darlo por cerrado — esto solo verifica la lógica aislada, no el nodo
   real con ROS.
4. **NUEVO (2026-07-17), barato — verificar el sector de la evasión de
   obstáculos de `tracking_node`.** Hallazgo sin confirmar (ver
   `docs/decisiones.md`, 2026-07-17): `_obstacle_avoidance` filtra el
   sector frontal (`abs(ang)<=50°`) sobre el ángulo **crudo** de `/scan`,
   sin aplicar el desfase de π que `detection_node` sí tiene documentado y
   corregido desde el 13/07 ("persona de frente ≈ π en el láser", RPLIDAR
   montado invertido). Si ese desfase aplica igual a todo `/scan`, la
   evasión podría estar vigilando el sector **trasero**, no el frontal —
   relevante para seguridad, no solo para precisión de seguimiento.
   Verificación de segundos: colocar un obstáculo conocido delante del
   robot (dentro de `obstacle_threshold=0.35m`) y comprobar si se dispara
   el log `"Obstáculo frontal: adj=... lin_factor=..."`; repetir con el
   obstáculo detrás. Priorizar esto al principio de la Sesión 4, antes de
   entrar en el resto del objetivo (es barato y de seguridad) — ver
   `docs/decisiones.md` para el detalle completo y cómo verificarlo
   también sin robot si se extiende `bag_to_csv.py` para extraer `/scan`
   crudo de un bag ya grabado.

> Repo: `juanitomuro1999/TFM_JUAN` (rama `main`). Robot: NUC **nuc-224**,
> `ssh user@10.48.0.1` (password `qwerty`), `ROS_DOMAIN_ID=24`, ROS 2 Jazzy,
> paquete en `~/ros2_ws/src/person_follower/`. Build con `--symlink-install`,
> así que sincronizar código a `src/` con `scp` es suficiente — no hace falta
> `colcon build` para que el stack recoja cambios al relanzar el launch.
>
> **Importante:** en el NUC **no hay `tmux`** ni acceso a internet. Para
> procesos persistentes, usar `nohup ... > /tmp/algo.log 2>&1 & disown` por
> SSH. Sincronizar código desde el portátil con `bash sync_nuc.sh` (el bug de
> la ruta duplicada de `config.yaml` que fallaba en la sesión 2026-07-08 —
> ver `PROGRESO.md` — ya está corregido).

## Presupuesto de lab: 9 sesiones, TODO el tiempo de robot que queda (no solo julio)

> **Sin acceso al laboratorio en agosto** (confirmado 2026-07-09). Estas 9
> sesiones **no son "julio, con margen en agosto detrás"** — son todo el
> tiempo de robot disponible antes del cierre. Lo que no quede recogido al
> terminar la sesión 9 se documenta como limitación/trabajo futuro en la
> memoria, no se pospone. Agosto queda para analizar lo ya grabado y
> escribir, sin datos nuevos.
>
> **Borrador de reparto (2026-07-09), reordenable.** Es una guía de
> prioridad, no un contrato — la experiencia de este proyecto es que las
> sesiones no siempre van como se planean (encuadre de cámara roto, RPLIDAR
> con timeouts, sklearn roto en el NUC...). Si una sesión se alarga, lo
> normal es recortar alcance (ver notas de "si el tiempo aprieta" en cada
> bloque) y desplazar lo que quede, no intentar comprimir dos sesiones en
> una — pero con el límite duro de la sesión 9, desplazar demasiado tiene
> coste real: significa que algo se queda fuera de la memoria como
> resultado, no solo "para más adelante".

| Sesión | Objetivo principal |
|---|---|
| ~~1~~ | ~~Cámara — re-encuadrar + validar gesto real~~ **✅ hecho 2026-07-09** (no como se planeó — resuelto por software + cambio de cámara improvisado, no reencuadre físico de la C270 — ver abajo) |
| ~~2~~ | ~~FSM oscilando + near_gain aislado + recalibrar cámara~~ **✅ hecho 2026-07-13** (parcial — ver estado heredado abajo: fix de CPU sí cerrado, oscilación/near_gain llevaron a un hallazgo mayor sin resolver, cámara aplazada) |
| ~~3~~ | ~~Corregir desfase de π en tracking_node + retest limpio de `near_gain`/oscilación + recalibrar cámara nueva~~ **✅ hecho 2026-07-15** (el fix de π se sostuvo, pero apareció un fallo mayor no relacionado — signo invertido en el PD angular, causa real de "gira al lado contrario" desde el 13/07 — encontrado y corregido; `near_gain` aislado y sano; cámara evaluada sin necesidad de recalibrar — ver estado heredado abajo) |
| **4 (próxima)** | Estresar el gate de continuidad con mobiliario denso + arreglar confirmación en el fallback de fusión + **el hueco de detección LIDAR+cámara al girar (nuevo, 2026-07-15, mismo tema)** + resolver reproducibilidad de métricas del Capítulo 7 |
| 5 | Repeticiones de validación (2-3 tomas por escenario) para el Capítulo 7 |
| 6 | Nav2 — fase A: solo localización AMCL |
| 7 | Nav2 — fase B: navegación a un punto (si la fase A salió bien) |
| 8 | Colchón + grabar vídeo de demostración del TFM |
| 9 | **Última sesión de lab del TFM.** |

**Recuento de sesiones resuelto 2026-07-15:** confirmado con el usuario que el
presupuesto real es el del 09/07 (9 sesiones totales, contando esa misma sesión
como la nº1) — **quedan 6 sesiones (4 a 9)** a partir de hoy. La mención del
13/07 de "9 o 10 sesiones quedando desde ese día" no era el recuento correcto;
descartar esa cifra. No volver a plantear esta duda en sesiones futuras.

### Calendario estimado (añadido 2026-07-17)

Con 14 días de julio restantes (17→31) para las 6 sesiones que quedan (4-9),
la cadencia máxima admisible es de **~2.3 días entre sesiones**. La cadencia
real hasta ahora (sesión 1→2: 4 días; 2→3: 2 días; media ~3 días) **no llega**
— a ese ritmo la sesión 9 caería en agosto, fuera de plazo (sin acceso al
lab ese mes, ver arriba). Hace falta mantener el ritmo más rápido de los dos
ya vistos (~2 días), no la media.

| Sesión | Fecha estimada* | Nota de riesgo |
|---|---|---|
| 4 | ~19 jul | Sobrecargada — 4 objetivos distintos (verificar sector de obstáculos + fallback de fusión en vivo + hueco al girar + reproducibilidad Cap.7). Si se alarga, primero recortar: convertir la decisión de estrategia del "hueco al girar" en trabajo de escritorio previo (dejar solo la prueba en vivo para la sesión) |
| 5 | ~21 jul | Depende de que la 4 cierre la reproducibilidad de métricas — si no, esta sesión hereda ese trabajo antes de las repeticiones |
| 6 | ~23 jul | Nav2 fase A — bloque oficialmente prescindible (ver nota de abajo) |
| 7 | ~25 jul | Nav2 fase B — condicional a que la 6 saliera bien |
| 8 | ~27 jul | Colchón (recoger lo que quedó atrás) + grabar vídeo de demo del TFM — margen de seguridad real del plan |
| 9 | ~29-31 jul | Última sesión — cierre. Sin margen después de esta: lo que no quede aquí pasa a "limitación/trabajo futuro documentado" en la memoria, no se pospone |

*Fechas ilustrativas calculadas a partir de la cadencia real de las sesiones
1-3, no de días de acceso al lab ya confirmados — ajustar esta tabla en
cuanto se conozcan las fechas reales de las próximas sesiones.

**Después de julio:** agosto sin lab (redactar Cap.7 final con los datos de
la sesión 5, escribir el capítulo de conclusiones/trabajo futuro que
todavía no existe en `01_introduccion.md` §1.5, preparar la defensa) y
septiembre con lab reservado solo al cierre (demo final), no a validación
nueva — ver Fase 5 en `README.md`/`docs/01_introduccion.md` §1.4.

**Si las sesiones 6-7 (Nav2) se retrasan o no salen bien:** es el bloque más
prescindible de la lista — empieza de cero (`docs/decisiones.md`,
2026-07-09) y los objetivos 1/2/4 ya tienen inversión y datos reales detrás.
Mejor recortar Nav2 a "solo localización" o a "trabajo futuro documentado"
que sacrificar tiempo de las sesiones 8-9 por él.

**Trabajo de escritorio en paralelo, sin gastar tiempo de robot (se puede
hacer cualquier día, incluidos los días sin lab):** el objetivo 6 (QR,
exploratorio) y ya redactados los Capítulos 5-6 de la memoria (pendientes
de revisión del autor, no de escritura); revisar `DWA.py`/`C_man.py`/
`cierre_seguro.py`/`UI_man.py` y decidir su limpieza (`docs/06_implementacion.md`
§6.11); corregir la etiqueta "DWA" del diagrama del Capítulo 2, que ahora
contradice al Capítulo 6. Nada de esto compite por tiempo de robot salvo
que sobre alguna sesión de las 9.

## Estado heredado de la sesión 2026-07-13 (no repetir, solo verificar)

- ✅ **Fix de rendimiento cerrado y verificado en vivo:** `detection_node`
  bajó de 93.7% a 27.3% de CPU (vectorizado `apply_median_filter` con
  `scipy.ndimage.median_filter`). No requiere seguimiento — cerrado.
- ⚠️ **`continuity_confirm_frames` investigado y descartado como fix** —
  subir de 1 a 2-3 no cambia nada (verificado sintéticamente). La solución
  real (exigir confirmación siempre en el fallback de fusión) sigue
  pendiente, ver `docs/decisiones.md` (2026-07-13).
- 🔄 **`observation_timeout` de `tracking_node` parametrizado** (antes
  hardcodeado `timeout_s=2.0`) — mismo valor, solo lo hace configurable.
  Sigue sin coordinarse con los otros dos timeouts
  (`detection_loss_frames=8`, `tracking_loss_timeout=1.5s`).
- ✅ **HALLAZGO CORREGIDO Y VERIFICADO en la misma sesión (con tiempo
  extra):** `detection_node._publish_person_position` publicaba
  `/person_position` en el convenio bruto del láser (delante ≈ π, `x`
  negativo con la persona delante), mientras `tracking_node.angle_to =
  atan2(py, px)` asumía el convenio estándar (delante = 0°, `x` positivo).
  Corregido invirtiendo el signo solo en la frontera de publicación de
  `detection_node` (el estado interno de gating sigue en el frame bruto,
  sin tocar) — no hizo falta cambiar `tracking_node`. **Verificado en vivo:**
  persona delante confirmada (~1.3m), `angle_deg` estable en 5.5-6.8° (antes
  pegado a ±180°), `vang` prácticamente 0 (antes saturado 71-76% del
  tiempo). Ver detalle completo en `docs/decisiones.md` (2026-07-13) y
  `PROGRESO.md`. **Ya no es la prioridad de esta sesión** — verificar que
  se sostiene en una prueba más larga y con movimiento real (ver objetivo
  1 de abajo, ahora es un retest de confirmación, no un diagnóstico).
- 🔄 **`near_gain` sin aislar limpiamente todavía** — las dos tomas grabadas
  el 13/07 (`near_gain_20260713`, `near_gain_v2_sin_gesto`) quedaron
  contaminadas por el bug de arriba (ya corregido) — sus métricas
  (saturación 71-76%, MAE de distancia) no son representativas del sistema
  ya corregido. CSVs/figuras en `validation/runs/20260713_near_gain_analysis/`
  y `..._v2_analysis/`, útiles solo como referencia de "antes del fix".
  Repetir con el sistema ya corregido — ver objetivo 2 de abajo.
- 🔄 **Cámara nueva sin recalibrar** — aplazado, no tocado hoy. `dev_deg` en
  los logs de fusión sigue en ~9-10° (vs ~0-6° con la C270 el 25/06).
- 🔄 **Pipeline de validación en el NUC estaba desincronizado** —
  `validation/bag_to_csv.py`/`plot_run.py` no tenían la extracción de
  `position.csv`/`expected_position.csv` de la sesión de escritorio del
  09/07 (`validation/` no está en `sync_nuc.sh`). Sincronizado manualmente
  hoy — si se vuelve a tocar `validation/` en el portátil, recordar
  sincronizarlo a mano al NUC (no lo hace `sync_nuc.sh`).

## Estado heredado de la sesión 2026-07-09, tarde (histórico, ya verificado en sesiones posteriores)

- ✅ **Objetivo específico 1 (gesto) conseguido, pero no como se planeó.**
  En vez de reencuadrar físicamente la C270, se bajó `gesture_min_visibility`
  0.6→0.5 y, a mitad de sesión, el usuario cambió la cámara por una SPCA2650
  AV Camera (reinicio del NUC incluido). Ambos gestos (derecha=inicio,
  izquierda=parada) se dispararon de forma repetida y fiable en varias
  tomas reales. Detalle en `docs/decisiones.md` y `PROGRESO.md`
  (2026-07-09, sesión de lab).
- ✅ **Bug real encontrado y corregido: barrido/deriva del gate de
  continuidad.** Con la persona quieta, la posición detectada podía barrer
  un círculo entero alrededor del robot en 1-2s (cadena de clústeres
  espurios — patas de silla — "caminando" entre sí, cada salto individual
  plausible). Fix: límite de deriva acumulada respecto a la posición
  confirmada de hace `continuity_window_s` (1.0s), en `detection_node.py`.
  Verificado con lógica aislada y confirmado en vivo (sin repetir el
  barrido en la toma siguiente). **No sustituye** el trabajo de estresar el
  fallback con mobiliario denso que ya estaba planeado — sigue pendiente,
  ver Sesión 4.
- ✅ **Arranque suave añadido a `tracking_node`** (`startup_ramp_s=1.5`,
  `startup_max_wz=0.5`): tras diagnosticar con datos reales que el giro
  brusco al activar el seguimiento era la respuesta correcta a un error de
  rumbo grande (~158°, persona casi detrás del robot) y no un bug, se
  limitó igualmente el techo de `wz` los primeros 1.5s tras cada activación
  para que se sienta menos agresivo. Confirmado por el usuario sin fallos.
- 🔄 **`max_speed` bajado a 0.18 m/s** (antes 0.3) para pruebas más suaves —
  valor de sesión, no necesariamente definitivo. Revisar si subirlo de
  nuevo una vez el resto esté estable.
- ⚠️ **Oscilación de la FSM (TRACKING↔IDLE cada pocos segundos)** sigue sin
  resolver — reproducida varias veces hoy con detección intermitente
  (`cam: False` a ratos). No es nueva (documentada desde el 17/06) y no la
  causó nada de lo cambiado hoy. **Nueva prioridad alta** de la próxima
  sesión — no se ha investigado la causa exacta todavía (podría ser
  `tracking_loss_timeout` de `control_node`, o el ritmo de MediaPipe vs. el
  LIDAR).
- 🔄 Pendiente: `camera_hfov_deg=51.0` y `bearing_sign=-1.0` (fusión
  cámara-LiDAR) se calibraron con la C270 — no reverificados con la
  SPCA2650. Revisar si `dev_deg` en los logs de fusión se ve desviado.
- 🔄 Pendiente sin tocar: `OrbbecSDK_ROS2` en `ros2_ws/src` sin compilar.
- 🔄 Bags de hoy en `~/tfm_bags/` del NUC (no copiados al repo):
  `gesto_real_20260709`, `_v2`, `_v3`, `gesto_izq_test`, `gesto_real_v4_fix`,
  `camara_nueva_velred`. Revisar cuáles aportan al Capítulo 7 antes de que
  se acumulen sin criterio.

## Estado heredado de la sesión 2026-07-15 (no repetir, solo verificar)

- ✅ **Puerto USB de kobuki/rplidar intercambiado tras reinicio** — el NUC
  reenumera `ttyUSB0`/`ttyUSB1` de forma no determinista entre arranques.
  Si `rplidar_node` muere con "operation time out" al lanzar, comprobar
  `/dev/serial/by-id/` y relanzar `kobuki_ros_node` con
  `-p device_port:=/dev/serial/by-id/usb-Yujin_Robot_iClebo_Kobuki_kobuki_AH02IGFT-if00-port0`
  en vez de depender del `/dev/ttyUSB0` hardcodeado en
  `kobuki_node_params.yaml`. Ver `PROGRESO.md`, 2026-07-15.
- ✅ **Fix de π confirmado con movimiento real** — se sostiene con la
  persona moviéndose/girando, no solo en el caso fácil ya probado el 13/07.
- ✅ **CORREGIDO — causa raíz real de "gira al lado contrario"**: signo
  invertido en el PD angular de `tracking_node` (`ang_err = -angle_to` era
  incorrecto; corregido a `ang_err = angle_to`). Verificado de forma
  objetiva con `/odom` (sin percepción) y en vivo con dos pruebas de
  seguimiento real. Esto **reemplaza** la conclusión del 13/07 ("este robot
  gira en sentido contrario al estándar ROS") — ver `docs/decisiones.md`,
  2026-07-15, para el detalle completo y por qué la simulación anterior no
  lo detectó. **No tocar este signo de nuevo sin repetir esa verificación
  objetiva con `/odom`.**
- ✅ **`near_gain` aislado y evaluado** (0.49-0.86m): comportamiento acotado
  (-52° a +52°, nunca ±180°) y con el signo correcto; saturación puntual
  esperable a esa distancia tan corta. Candidato a ajuste fino (bajar
  `angular_gain` <0.7m, o `near_gain` más agresivo) pero no bloquea nada —
  ver `PROGRESO.md`.
- ✅ **Cámara SPCA2650 evaluada, no recalibrada** — `dev_deg` con los datos
  de hoy (ya con los fixes aplicados): mediana 3.2°, sin sesgo sistemático.
  Los ~9-10° del 13/07 eran en gran parte arrastre de los bugs de π/signo,
  no una mala calibración de `bearing_sign`/`camera_hfov_deg`. No se tocó
  ningún parámetro de cámara.
- 🔄 **Diagnosticado, no corregido — LIDAR y cámara pierden a la persona a
  la vez al girar** (~2-4s reales sin ninguna detección): el emparejamiento
  de piernas del LiDAR falla cuando una pierna ocluye a la otra durante el
  giro, y la pose de MediaPipe puede fallar un frame puntual por motion
  blur — las dos modalidades comparten el mismo punto ciego (vista frontal
  de la persona), así que el fallback de fusión no cubre el caso. Con el
  signo ya corregido esto ya no causa que el robot "gire mal" (ahora se
  para en vez de extrapolar, gracias a `extrapolation_limit_s=0.6`), pero
  sigue siendo una limitación real de la arquitectura de fusión. Detalle
  completo y opciones de fix a decidir en `docs/decisiones.md`, 2026-07-15
  — ver objetivo de la Sesión 4 de abajo, que ahora incorpora este hallazgo.
- 🔄 **`camera_debounce_count` bajado de 2 a 1** — mitigación parcial del
  punto anterior, sigue siendo válida por sí misma independientemente del
  fix de arquitectura pendiente.

## OBJETIVO de la Sesión 4 (próxima): fallback de fusión robusto durante giros + gate de continuidad + reproducibilidad del Capítulo 7

**Contexto actualizado 2026-07-15:** el hallazgo de hoy (LIDAR y cámara
pierden a la persona a la vez al girar, ver estado heredado arriba) es el
mismo tema que ya estaba planeado para esta sesión (confirmación en el
fallback de fusión) — abordarlos juntos.

**Antes de nada (2026-07-17, barato, prioridad):** verificar el hallazgo
sin confirmar del sector de `_obstacle_avoidance` en `tracking_node` — ver
punto 4 de "Tareas de escritorio" más arriba y `docs/decisiones.md`
(2026-07-17). Es una comprobación de segundos con un obstáculo delante y
otro detrás, y tiene implicación de seguridad si se confirma — hacerlo al
llegar, antes de entrar en el resto de esta sesión.

### Arreglar la pérdida de detección conjunta al girar (fusiona el hallazgo de hoy con el de 13/07)

1. Decidir una estrategia concreta entre las esbozadas en
   `docs/decisiones.md` (2026-07-15): ¿aceptar un clúster de pierna único
   (no emparejado) como candidato de menor confianza cuando no hay par
   válido, gateado por continuidad? ¿ampliar `max_leg_distance` para
   tolerar la oclusión parcial durante el giro? ¿bajar aún más el
   debounce/timeout de cámara? Verificar cada opción con datos sintéticos
   (reproduciendo la secuencia real del log de hoy, epoch
   1784124265-1784124271) antes de probarla en el robot.
2. Una vez implementada, repetir un test de movimiento/giro similar al de
   hoy y comprobar que ya no aparece el hueco de ~2-4s sin detección.

### Gate de continuidad + confirmación en el fallback (pendiente desde 13/07)

El fix de deriva acumulada del 09/07 corrigió el caso concreto observado en
vivo, pero no se ha probado deliberadamente con mobiliario denso ni un
recorrido largo:

1. Probar con mobiliario deliberadamente denso cerca de la trayectoria y un
   recorrido más largo (>2 min) para ver con qué frecuencia se activa el
   fallback (log `"Candidatos ... descartados por el gate de continuidad"`).
2. Si siguen colándose saltos, subir `continuity_confirm_frames` a 2 o 3
   y/o ajustar `continuity_window_s` — comparar métricas antes/después.
   **Nota 2026-07-13: verificado sintéticamente que esto NO basta** para el
   caso de mobiliario a poca distancia (cae dentro del radio "plausible" de
   `max_person_speed` sin pasar por `continuity_confirm_frames`) — ver abajo.

### Arreglar confirmación en el fallback de fusión (2026-07-13)

### Gate de continuidad

El fix de deriva acumulada del 09/07 (ver arriba) corrigió el caso concreto
observado en vivo, pero no se ha probado deliberadamente con mobiliario
denso ni un recorrido largo:

1. Probar con mobiliario deliberadamente denso cerca de la trayectoria y un
   recorrido más largo (>2 min) para ver con qué frecuencia se activa el
   fallback (log `"Candidatos ... descartados por el gate de continuidad"`).
2. Si siguen colándose saltos, subir `continuity_confirm_frames` a 2 o 3
   y/o ajustar `continuity_window_s` — comparar métricas antes/después.
   **Nota 2026-07-13: verificado sintéticamente que esto NO basta** para el
   caso de mobiliario a poca distancia (cae dentro del radio "plausible" de
   `max_person_speed` sin pasar por `continuity_confirm_frames`) — ver abajo.

### Arreglar confirmación en el fallback de fusión (nuevo, 2026-07-13) — ✅ diseño+verificación sintética hechos 2026-07-16, pendiente validar en vivo

Encontrado el 13/07: un candidato del fallback de fusión cámara+LIDAR se
acepta sin confirmación si cae dentro del radio "plausible" de
`max_person_speed` (2.0 m/s × tiempo transcurrido + margen) respecto al
último punto confirmado — y ese radio crece rápido (>2m en ~1s), suficiente
para que mobiliario cercano se cuele como si fuera la persona.
`continuity_confirm_frames` no ayudaba porque solo actuaba sobre candidatos
ya rechazados como implausibles. Ver script de verificación y detalle
completo en `docs/decisiones.md` (2026-07-13, "Subir
continuity_confirm_frames: descartado").

1. ~~Modificar `detect_person`/`_gate_by_continuity` para que los
   candidatos que llegan por el camino de fusión (no por par de piernas)
   exijan confirmación (`continuity_confirm_frames` consecutivos en el
   mismo sitio) **siempre**, no solo cuando fallan el chequeo de velocidad
   plausible.~~ **Hecho 2026-07-16:** nuevo `_confirm_fusion_candidate` +
   `_filter_by_drift` en `detection_node.py`, ver `docs/decisiones.md`
   (2026-07-16).
2. ~~Verificar con el mismo script sintético de hoy (replicar la secuencia
   real observada: mobiliario a 1.34m tras 0.92s de hueco) antes de probar
   en el robot.~~ **Hecho 2026-07-16:** `validation/verify_fusion_confirm.py`,
   seis escenarios en verde, incluida esa secuencia exacta.
3. **Pendiente (Sesión 4):** sincronizar al NUC (`bash sync_nuc.sh`) y
   validar con datos reales — en vivo o contra un rosbag con el escenario
   de mobiliario del 13/07 — antes de dar el fix por cerrado.

### Reproducibilidad de métricas del Capítulo 7

**Ya incorporado al pipeline (2026-07-09, preparado sin robot — ver
`docs/decisiones.md`):** `bag_to_csv.py` extrae `/person_position` a
`position.csv` y `plot_run.py` añade a `metrics.txt` el % de saltos de
posición (`--jump-threshold`, def. 0.8m) y el % de saturación angular con
posición estable (`--stable-radius`/`--stable-window`/`--sat-threshold`).
Verificado solo con CSVs sintéticos (sin ROS ni datos reales) — **pendiente
de esta sesión:** re-ejecutar `bag_to_csv.py` + `plot_run.py` sobre los tres
bags de `validation/runs/20260708_movimiento_*` (requiere una máquina con
ROS 2, no el portátil de escritorio) y comparar las cifras nuevas contra la
tabla 7.4 de `docs/07_resultados.md` — actualizarla si difieren. Si
coinciden razonablemente, dar por cerrada esta limitación de 7.5; si no,
documentar la discrepancia y decidir si ajustar los umbrales por defecto.

## OBJETIVO de la Sesión 5: repeticiones de validación para el Capítulo 7

Con el ruido de fondo (saltos/saturación) ya resuelto y ajustado: repetir
2-3 tomas por escenario de `validation/README.md` (recta, curva, parada,
corto, oclusión, obstáculo) para tener varianza, no solo un valor por
condición (`docs/07_resultados.md` §7.5).

## OBJETIVO de las Sesiones 6-7: Nav2 — demo mínima (objetivo 3, alcance decidido 2026-07-09)

**Ya preparado sin robot (ver `docs/decisiones.md`, entrada 2026-07-09):**
`person_follower/launch/nav2_localization_demo.launch.py` (nuevo) y
`scripts/nav2_send_goal.py`. **Nada de esto se ha ejecutado nunca** —
tratar como si fuera código nuevo sin probar, no como algo ya validado.

**Sesión 6 — fase A, solo localización:**
1. Verificar los strings de plugin de `nav2_params.yaml` contra la versión
   de Nav2 instalada en el NUC (`ros2 pkg prefix nav2_bringup`) — su propia
   cabecera avisa de que pueden cambiar entre distros.
2. Lanzar **solo el bloque de localización** (comentar el bloque de
   navegación en el launch file). En RViz: cargar el mapa, dar una pose
   inicial aproximada con "2D Pose Estimate", mover el robot un poco y
   confirmar que AMCL converge y la pose se mantiene estable.
3. Si el tiempo aprieta, quedarse aquí (localización validada) y dejar la
   fase B para la Sesión 7 — el launch file ya está pensado para poder
   cortar el alcance así sin tirar el trabajo.

**Sesión 7 — fase B, navegación (solo si la fase A salió bien):**
1. Activar el bloque de navegación completo y usar
   `scripts/nav2_send_goal.py <x> <y>` con un punto leído en RViz sobre el
   mapa real (las coordenadas no se pueden adivinar sin el robot).
2. **No lanzar este launch a la vez que `start_person_follower.launch.py`**
   — ambos publican en `/commands/velocity`.

## Si sobra tiempo (cualquier sesión)

- Investigar por qué `ros2 topic pub --once /gesture_command` no queda
  grabado en el rosbag pese a que `control_node` sí lo recibe (visto dos
  veces el 08/07) — no bloquea nada, pero hace `gestures.csv` poco fiable.

## Pasos para empezar

```bash
# 1. Sincronizar si hubo cambios locales
cd ~/ros2_ws/src/TFM_JUAN && git pull

# 2. Lanzar el robot (cada bloque con nohup+disown, sin tmux)
sshpass -p 'qwerty' ssh user@10.48.0.1
source /opt/ros/jazzy/setup.bash && source ~/kobuki_ws/install/setup.bash && source ~/ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=24

nohup ros2 launch kobuki_node kobuki_node-launch.py > /tmp/kobuki.log 2>&1 & disown
nohup ros2 launch rplidar_ros rplidar_a2m8_launch.py serial_port:=/dev/rplidar > /tmp/lidar.log 2>&1 & disown
nohup ros2 launch person_follower start_person_follower.launch.py > /tmp/follower.log 2>&1 & disown

# 3. Verificar
ros2 node list
timeout 5 ros2 topic hz /scan
grep GESTO-DBG /tmp/follower.log | tail -5   # visibilidad de muñeca al levantar el brazo
```

> **Si `rplidar_node` muere con "operation time out":** el puerto USB se ha
> reenumerado (ver estado heredado 2026-07-15) — comprobar
> `ls -la /dev/serial/by-id/` y relanzar `kobuki_ros_node` apuntando
> explícitamente a la ruta `by-id` de la Kobuki en vez de depender del
> `/dev/ttyUSB0` por defecto del launch file.

## Checklist de cierre de sesión

- [ ] Actualizar `PROGRESO.md` con lo avanzado/encontrado.
- [ ] Si se completa un objetivo del TFM, marcarlo en `docs/01_introduccion.md`.
- [ ] Si hay una decisión de diseño relevante, añadirla a `docs/decisiones.md`.
- [ ] Añadir entrada con fecha en `docs/04_diario_desarrollo.md` (estilo prosa, para la memoria).
- [ ] Actualizar la tabla "Presupuesto de julio" de arriba: tachar la sesión
  que se acaba de completar, y si algo se quedó a medias o se alargó,
  reajustar qué toca en la sesión siguiente (no dar por hecho que el reparto
  original sigue siendo realista).
- [ ] Dejar el bloque "OBJETIVO de la Sesión N" correspondiente a la
  **próxima** sesión como el primero del documento (mover/reescribir según
  hiciera falta), igual que este archivo ya traía preparado para la Sesión 1.
- [ ] `git add` + commit + push (proyecto principal y, si aplica, Claude-Project-OS).
