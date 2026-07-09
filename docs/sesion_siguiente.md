# Prompt — Próxima sesión

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
| **2 (próxima)** | FSM oscilando (nuevo, prioridad alta) + `near_gain` aislado + recalibrar cámara nueva |
| 3 | Estresar el gate de continuidad con mobiliario denso + resolver reproducibilidad de métricas del Capítulo 7 |
| 4 | Repeticiones de validación (2-3 tomas por escenario) para el Capítulo 7 |
| 5 | Nav2 — fase A: solo localización AMCL |
| 6 | Nav2 — fase B: navegación a un punto (si la fase A salió bien) |
| 7 | Colchón + grabar vídeo de demostración del TFM |
| 8 | Objetivo 5 (guiado a destino) si hay margen; si no, más repeticiones/pulido del Cap. 7 |
| 9 | **Última sesión de lab del TFM.** Cerrar cabos sueltos y decidir, con lo que haya, qué se documenta como completado y qué como trabajo futuro — no queda una sesión 10 a la que aplazar. |

**Si sesiones 5-6 (Nav2) se retrasan o no salen bien:** es el bloque más
prescindible de la lista — empieza de cero (`docs/decisiones.md`,
2026-07-09) y objetivos 1/2/4 ya tienen inversión y datos reales detrás.
Mejor recortar Nav2 a "solo localización" o a "trabajo futuro documentado"
que sacrificar tiempo de las sesiones 2-4 por él.

**Objetivo 6 (QR, exploratorio) y la redacción de los Capítulos 5-6 de la
memoria no tienen sesión de lab asignada** — son trabajo de escritorio
(bibliografía, prosa) o exploratorio de baja prioridad; no compiten por
tiempo de robot salvo que sobre alguna sesión de las 9.

## Estado heredado de la sesión 2026-07-09, tarde (no repetir, solo verificar)

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
  ver Sesión 3.
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

## OBJETIVO de la Sesión 2 (próxima): FSM oscilando + `near_gain` aislado + recalibrar cámara

### FSM oscilando (nueva prioridad alta)

1. Lanzar el stack, activar TRACKING con el gesto (ya funciona), y con la
   persona quieta y bien detectada, observar cuántas veces por minuto
   oscila `>> TRACKING`/`>> IDLE` sin que medie un gesto.
2. Mirar `control_node.py` (`tracking_loss_timeout`) y la frecuencia real de
   `/person_detected_visual` vs. `/scan` — hipótesis de hoy: MediaPipe corre
   mucho más lento que el LIDAR (10Hz) en la CPU del NUC, así que
   `camera_timeout`/`camera_debounce_count` podrían estar peleando con un
   ritmo de cámara más bajo de lo asumido. Medir antes de tocar parámetros.
3. Si se confirma, ajustar `camera_timeout`/`tracking_loss_timeout` con
   datos, no a ciegas.

### `near_gain` de forma aislada

Sigue sin aislarse específicamente (todas las tomas de movimiento hasta
ahora mezclan acercarse/alejarse/lateral/giro):

1. Activar TRACKING con el gesto.
2. Grabar con `validation/record_run.sh corto_near_gain` (o el comando
   `ros2 bag record` equivalente si `record_run.sh` no está sincronizado al
   NUC — ver nota más abajo) mientras la persona se acerca deliberadamente a
   0.5-0.7m del robot y cambia de dirección ahí.
3. Mirar `vang`: debe variar suave, sin picos, y sin saturación permanente.

### Recalibrar cámara nueva

Repetir la comprobación de `bearing_sign`/`camera_hfov_deg` (como se hizo el
25/06 con la C270: mirar `dev_deg` en los logs de fusión y confirmar que el
rumbo de cámara coincide con el clúster LiDAR elegido) ahora con la
SPCA2650 — el FOV real puede ser distinto al de la C270.

**Nota operativa:** `validation/record_run.sh` no estaba sincronizado al NUC
hoy (solo el paquete ROS, no el repo completo) — se lanzó `ros2 bag record`
a mano con la misma lista de topics. Sincronizar el repo completo o al menos
`validation/` al NUC si se quiere usar el script tal cual.

## OBJETIVO de la Sesión 3: estresar el gate de continuidad + reproducibilidad del Capítulo 7

### Gate de continuidad

El fix de deriva acumulada del 09/07 (ver arriba) corrigió el caso concreto
observado en vivo, pero no se ha probado deliberadamente con mobiliario
denso ni un recorrido largo:

1. Probar con mobiliario deliberadamente denso cerca de la trayectoria y un
   recorrido más largo (>2 min) para ver con qué frecuencia se activa el
   fallback (log `"Candidatos ... descartados por el gate de continuidad"`).
2. Si siguen colándose saltos, subir `continuity_confirm_frames` a 2 o 3
   y/o ajustar `continuity_window_s` — comparar métricas antes/después.

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

## OBJETIVO de la Sesión 4: repeticiones de validación para el Capítulo 7

Con el ruido de fondo (saltos/saturación) ya resuelto y ajustado: repetir
2-3 tomas por escenario de `validation/README.md` (recta, curva, parada,
corto, oclusión, obstáculo) para tener varianza, no solo un valor por
condición (`docs/07_resultados.md` §7.5).

## OBJETIVO de las Sesiones 5-6: Nav2 — demo mínima (objetivo 3, alcance decidido 2026-07-09)

**Ya preparado sin robot (ver `docs/decisiones.md`, entrada 2026-07-09):**
`person_follower/launch/nav2_localization_demo.launch.py` (nuevo) y
`scripts/nav2_send_goal.py`. **Nada de esto se ha ejecutado nunca** —
tratar como si fuera código nuevo sin probar, no como algo ya validado.

**Sesión 5 — fase A, solo localización:**
1. Verificar los strings de plugin de `nav2_params.yaml` contra la versión
   de Nav2 instalada en el NUC (`ros2 pkg prefix nav2_bringup`) — su propia
   cabecera avisa de que pueden cambiar entre distros.
2. Lanzar **solo el bloque de localización** (comentar el bloque de
   navegación en el launch file). En RViz: cargar el mapa, dar una pose
   inicial aproximada con "2D Pose Estimate", mover el robot un poco y
   confirmar que AMCL converge y la pose se mantiene estable.
3. Si el tiempo aprieta, quedarse aquí (localización validada) y dejar la
   fase B para la Sesión 6 — el launch file ya está pensado para poder
   cortar el alcance así sin tirar el trabajo.

**Sesión 6 — fase B, navegación (solo si la fase A salió bien):**
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
