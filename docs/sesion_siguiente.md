# Prompt — Próxima sesión

## OBJETIVO de la Sesión 5 (próxima): repeticiones de validación para el Capítulo 7

Con el ruido de fondo de continuidad ya resuelto y ajustado en la Sesión 4
(saltos de posición, saturación angular, hueco de detección al girar, sector
de obstáculos — ver `docs/decisiones.md` 2026-07-21 y estado heredado más
abajo): repetir **2-3 tomas por escenario** de `validation/README.md` para
tener varianza, no solo un valor por condición (limitación N=1 documentada
en `docs/07_resultados.md` §7.5).

**Escenarios a repetir** (`bash validation/record_run.sh <etiqueta> [duración_s]`):

| Escenario | Qué valida |
|---|---|
| `recta` | Persona camina en línea recta alejándose |
| `curva` | Persona describe una curva / cambio de dirección — **ahora también ejercita el fallback de pierna única nuevo (Sesión 4)** |
| `parada` | Persona se detiene → standoff a `target_distance` (1 m) |
| `corto` | Persona se acerca a <1 m → valida `near_gain`/giro brusco a corta distancia |
| `oclusion` | Persona pasa tras un obstáculo → predicción Kalman + recuperación |
| `obstaculo` | Obstáculo en la trayectoria → evasión — **⚠️ 2026-07-21: primera repetición terminó en colisión real con una silla, ver aviso de seguridad justo abajo antes de repetir este escenario** |

> **⚠️ AVISO DE SEGURIDAD (2026-07-21):** la primera repetición del
> escenario `obstaculo` en la Sesión 5 terminó en una colisión real (sin
> daños) — el robot detectó la silla, se paró, pero no la rodeó, y al
> moverse la persona chocó contra ella. Analizado en `docs/decisiones.md`
> (2026-07-21): `lin_factor` nunca bajó de 1.0 en toda la toma — el objeto
> real estaba a 0.75m del LIDAR (por encima del `obstacle_threshold` de
> 0.35m), consistente con que el LIDAR 2D veía las patas de la silla pero
> no el asiento/reposabrazos, que sobresale más hacia el robot a otra
> altura. **No es un bug de sector ni de umbral** (el sector ya está
> corregido y verificado) — es un límite físico del sensor. Antes de
> repetir este escenario: mantener distancia de seguridad manual con
> mobiliario real hasta decidir alguna mitigación (conectar
> `collision_handling_node`, bajar velocidad cerca del target, o aceptar
> como limitación documentada — ver mitigaciones en `docs/decisiones.md`).

**Antes de repetir cada escenario, comprobar que sigue vigente:**
- `continuity_confirm_frames=3` (subido en la Sesión 4) — no bajarlo sin
  repetir la prueba de mobiliario denso que motivó el cambio.
- El fallback de pierna única (`_confirm_single_leg_candidate`) sigue en
  `detection_node.py` — debería reducir huecos de detección en `curva` y
  `oclusion` respecto a tomas anteriores a la Sesión 4.

**Al terminar cada toma:** `bag_to_csv.py` (en el NUC) + `plot_run.py` (en
el portátil) + comparar contra las tomas equivalentes ya existentes en
`validation/runs/` (si las hay) para ver si el fallback de pierna única y
`continuity_confirm_frames=3` mejoran las cifras en escenarios reales
distintos al de mobiliario denso de la Sesión 4.

**Pendientes menores heredados de la Sesión 4** (hacer si sobra tiempo,
ninguno bloquea el objetivo principal — ver `docs/decisiones.md`
2026-07-21 para el detalle completo de cada uno):
- Confirmar que `lin_factor` de la evasión de obstáculos frena de verdad
  la marcha con el robot en movimiento real (hoy solo se confirmó el
  sector correcto y el disparo del log, sin movimiento).
- Repetir el giro con tracking activo (robot moviéndose de verdad tras la
  persona), no solo con el robot parado, para el fallback de pierna única.
- Cruzar `position.csv` con `distance` en los instantes "estables" de los
  bags `20260708_movimiento_fix1/fix2` para confirmar o descartar el
  efecto de acercamiento sin `near_gain` como causa de la saturación alta
  de la tabla 7.4.

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
4. ~~**Verificar el sector de la evasión de obstáculos de
   `tracking_node`**~~ — **✅ CONFIRMADO Y CORREGIDO 2026-07-21 (Sesión 4,
   en vivo).** Era real: con una silla a 25cm delante, el mínimo del láser
   caía en ángulo crudo ≈-174° (cerca de ±180°); con la misma silla detrás,
   ≈0-2°. `_obstacle_avoidance` vigilaba el sector trasero, no el frontal.
   Corregido aplicando el mismo desfase de π que `detection_node` ya tenía.
   Validado en vivo (sin movimiento real: tracking activado por servicio,
   log `"Obstáculo frontal"` disparándose correctamente con la silla
   delante, y dejando de dispararse al desactivar tracking). Ver
   `docs/decisiones.md` (2026-07-21). **Pendiente menor:** repetir con el
   robot en movimiento real para confirmar que `lin_factor` frena la
   marcha, no solo que el log dispara.

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
| ~~4~~ | ~~Estresar el gate de continuidad con mobiliario denso + arreglar confirmación en el fallback de fusión + el hueco de detección LIDAR+cámara al girar + resolver reproducibilidad de métricas del Capítulo 7~~ **✅ hecho 2026-07-21** (los cuatro objetivos completados en una sola sesión — ver estado heredado abajo y `docs/decisiones.md`) |
| **5 (próxima)** | Repeticiones de validación (2-3 tomas por escenario) para el Capítulo 7 |
| 6 | Nav2 — fase A: solo localización AMCL |
| 7 | Nav2 — fase B: navegación a un punto (si la fase A salió bien) |
| 8 | Colchón + grabar vídeo de demostración del TFM |
| 9 | **Última sesión de lab del TFM.** |

**Recuento de sesiones resuelto 2026-07-15:** confirmado con el usuario que el
presupuesto real es el del 09/07 (9 sesiones totales, contando esa misma sesión
como la nº1). Tras completar la Sesión 4 (2026-07-21) — **quedan 5 sesiones
(5 a 9)**. La mención del 13/07 de "9 o 10 sesiones quedando desde ese día" no
era el recuento correcto; descartar esa cifra. No volver a plantear esta duda
en sesiones futuras.

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

## Estado heredado de la sesión 2026-07-21 (Sesión 4 — no repetir, solo verificar)

**Contexto actualizado 2026-07-15:** el hallazgo de hoy (LIDAR y cámara
pierden a la persona a la vez al girar, ver estado heredado arriba) es el
mismo tema que ya estaba planeado para esta sesión (confirmación en el
fallback de fusión) — abordarlos juntos.

~~**Antes de nada (2026-07-17, barato, prioridad):** verificar el hallazgo
sin confirmar del sector de `_obstacle_avoidance` en `tracking_node`~~ —
**✅ hecho al principio de esta misma sesión (2026-07-21)**, ver punto 4 de
"Tareas de escritorio" más arriba y `docs/decisiones.md` (2026-07-21).
Confirmado y corregido. Sigue el resto del objetivo de la Sesión 4 abajo.

### Arreglar la pérdida de detección conjunta al girar — ✅ implementado y validado 2026-07-21 (Sesión 4)

~~Decidir una estrategia concreta... verificar con datos sintéticos...
repetir un test de movimiento/giro~~ — hecho hoy. Implementado el fallback
de pierna única (`_confirm_single_leg_candidate` en `detection_node.py`,
ver `docs/decisiones.md` 2026-07-21): cuando no hay par de piernas válido
pero sí un clúster único ya clasificado como pierna, se acepta como
candidato gateado por consistencia, antes del fallback de cámara.
Verificado sintéticamente (`validation/verify_single_leg_fallback.py`) y en
vivo con una persona girando delante del robot: 630 detecciones vía el
nuevo fallback, 315 vía par normal (sin regresión), 0 errores, y el único
hueco observado bajó a ~1.6s (antes 2-4s). **Pendiente, no bloqueante:**
repetir con el robot realmente siguiendo (tracking activo, moviéndose de
verdad) en vez de solo con el robot parado, y acumular más repeticiones
para ver si el hueco residual de ~1.6s es sistemático.

### Gate de continuidad + confirmación en el fallback — ✅ hecho 2026-07-21 (Sesión 4)

~~Probar con mobiliario deliberadamente denso... si siguen colándose
saltos, subir continuity_confirm_frames~~ — hecho hoy: dos tomas reales de
~2 min con mobiliario denso, tracking activo (robot moviéndose de
verdad). Con `continuity_confirm_frames=1`: 12.9% de saltos >0.8m (máx
3.40m). Subido a 3: saltos bajan a 4.6% (máx similar, 3.49m — no elimina
el peor caso, solo lo hace menos frecuente), saturación baja a 0.0%, a
cambio de detección algo menor (100%→97.8%) y MAE de distancia peor
(0.633m→0.854m, posible ruido de muestra N=1, no confirmado). Se mantiene
`continuity_confirm_frames=3` como nuevo valor por defecto en
`config.yaml`. Detalle completo en `docs/decisiones.md` (2026-07-21).
**Pendiente, no bloqueante:** repetir con más tomas para separar el efecto
real del parámetro del ruido de la muestra (en particular el MAE); valorar
en el futuro un chequeo de salto inmediato (no solo deriva acumulada)
también para fusión/pierna única, análogo al que ya tiene
`_gate_by_continuity` para pares.

### Arreglar confirmación en el fallback de fusión (nuevo, 2026-07-13) — ✅ diseño+verificación sintética hechos 2026-07-16, validado en vivo 2026-07-21

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
3. ~~Sincronizar al NUC y validar con datos reales~~ — **✅ hecho
   2026-07-21:** validado en vivo con mobiliario denso real (ver entrada
   de arriba y `docs/decisiones.md` 2026-07-21) — 0 detecciones vía fusión
   de cámara en ambas tomas (el fallback de pierna única, nuevo hoy, cubrió
   todos los casos sin par), así que este camino concreto no se ejerció
   hoy, pero el mecanismo de confirmación en sí (mismo código que pierna
   única) sí quedó validado indirectamente.

### Reproducibilidad de métricas del Capítulo 7 — ✅ hecho 2026-07-21 (Sesión 4)

~~Re-ejecutar `bag_to_csv.py` + `plot_run.py` sobre los tres bags de
`validation/runs/20260708_movimiento_*`~~ — hecho hoy aprovechando la
conectividad SSH al NUC (tiene ROS 2). Resultado mixto: el % de saltos de
posición reprodujo bien (exacto en fix1/fix2, algo más bajo en la toma
original); la saturación angular **no** reprodujo la mejora del script
perdido — se mantiene alta (86-99%) en las tres tomas, no baja a 12.4%.
Tabla 7.4 y su lectura ya actualizadas en `docs/07_resultados.md` con las
cifras reproducibles y una conclusión honesta (mejora en saltos, no en
saturación, con estos tres fixes concretos). Detalle completo y dos
hipótesis sin confirmar sobre la causa en `docs/decisiones.md`
(2026-07-21). **Pendiente menor, no bloqueante:** cruzar `position.csv`
con `distance` en los instantes "estables" de fix1/fix2 para confirmar o
descartar el efecto de acercamiento a corta distancia sin `near_gain`
(que no existía todavía el 08/07) como causa de la saturación alta.

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
