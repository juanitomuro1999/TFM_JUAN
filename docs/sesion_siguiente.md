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
| **1 (próxima)** | Cámara — re-encuadrar + validar gesto real (bloquea objetivo 1) |
| 2 | `near_gain` aislado + empezar a estresar el gate de continuidad |
| 3 | Terminar el gate de continuidad + resolver reproducibilidad de métricas del Capítulo 7 |
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

## Estado heredado de la sesión 2026-07-08 (no repetir, solo verificar)

- ✅ **Filtro de continuidad + gate de Mahalanobis corregido + rate-limit de
  `wz`**: los saltos de posición implausibles (2-4m en <300ms) y la
  saturación angular casi permanente (94.5% del tiempo incluso con posición
  estable) están mayormente resueltos. Progresión medida: saltos >0.8m
  12.1%→0.7%, saturación con posición estable 94.5%→12.4%. Detalle completo
  y causa raíz en `docs/decisiones.md` (entrada 2026-07-08) y
  `PROGRESO.md`.
- ⚠️ **El gesto de mano derecha NO es utilizable todavía** — la cámara C270,
  en su encuadre/inclinación actual, pierde de vista la muñeca (o su
  visibilidad MediaPipe cae por debajo de 0.6) justo cuando se levanta el
  brazo. Se activó TRACKING manualmente por SSH (`ros2 topic pub
  /gesture_command ...`) como workaround para poder probar. Objetivo
  específico 1 del TFM (interacción por gestos) depende de que esto funcione
  de verdad — es la prioridad más alta de la próxima sesión.
- 🔄 Pendiente sin tocar: `OrbbecSDK_ROS2` en `ros2_ws/src` sin compilar —
  explorar si la cámara RGBD Orbbec Astra resuelve tanto el encuadre del
  gesto como la detección de persona (cambio de arquitectura mayor).

## OBJETIVO de la Sesión 1 (próxima): re-encuadrar la cámara y validar el gesto real

Único objetivo de esta sesión — no meter `near_gain`/continuidad/Nav2 aquí
aunque sobre tiempo (ver "si sobra tiempo" al final de este bloque).

- Revisar físicamente la altura/inclinación de la C270 en el robot. El
  síntoma exacto: con la persona a distancia normal de interacción,
  `landmarks_visibles` cae de 25 a 13 y la muñeca/hombro se estiman con `y`
  fuera de rango [0,1] al levantar el brazo — sugiere que el encuadre
  vertical no cubre "persona de pie con brazo levantado" a esa distancia.
- Tras el ajuste físico, repetir el gesto y mirar
  `visual_detection_node`'s log `[GESTO-DBG]` (visibilidad de muñeca/hombro,
  ¿supera 0.6 de forma sostenida al levantar el brazo?).
- Si el reencuadre no basta, considerar bajar `gesture_min_visibility` (0.6 →
  ~0.45-0.5) en `config.yaml` como mitigación adicional — pero probar primero
  el ajuste físico, que es la causa real identificada el 08/07.

**Si sobra tiempo en esta sesión:** grabar una toma corta con
`validation/record_run.sh` usando el gesto real ya funcionando (no el
workaround manual por SSH) — es un dato que le falta al Capítulo 7
(`docs/07_resultados.md` §7.5, "gesto de activación no utilizado").

## OBJETIVO de la Sesión 2: `near_gain` aislado + empezar el gate de continuidad

### `near_gain` de forma aislada

La toma del 08/07 mezcló movimiento general (alejarse/acercarse/lateral/giro)
y no aisló el caso que motivó `near_gain` (giro brusco a corta distancia):

1. Activar TRACKING (gesto si ya funciona tras la Sesión 1, si no
   manualmente por SSH).
2. Grabar con `validation/record_run.sh corto_near_gain` mientras la persona
   se acerca deliberadamente a 0.5-0.7m del robot y cambia de dirección ahí.
3. Mirar `vang` en `analysis/figs/vel_vs_t.png`: debe variar suave, sin
   picos, y sin la saturación casi permanente que había antes del fix.

### Empezar a estresar el fallback del filtro de continuidad

**Ya implementado (2026-07-09, preparado sin robot — ver `docs/decisiones.md`):**
`_gate_by_continuity` ahora exige `continuity_confirm_frames` scans
consecutivos con un candidato *consistente* (mismo punto, no cualquier salto)
antes de aceptar un reanclaje, en vez de rendirse al primer intento. Por
defecto `continuity_confirm_frames: 1` en `config.yaml` — **sin cambiar el
comportamiento actual todavía**. Verificado solo con pruebas de lógica
aisladas (sin ROS ni datos reales).

Si queda tiempo tras `near_gain`: repetir una toma tal cual (con
`continuity_confirm_frames: 1`) para confirmar que el comportamiento no
cambió respecto al fix del 08/07 (mismo % de saltos/saturación) — el resto
(estresar con mobiliario denso, ajustar el parámetro) se deja para la
Sesión 3 si no da tiempo.

## OBJETIVO de la Sesión 3: terminar el gate de continuidad + reproducibilidad del Capítulo 7

### Gate de continuidad

1. Probar con mobiliario deliberadamente denso cerca de la trayectoria y un
   recorrido más largo (>2 min) para ver con qué frecuencia se activa el
   fallback (log `"Candidatos ... descartados por el gate de continuidad"`).
2. Si se activa con frecuencia y los saltos siguen colándose, subir
   `continuity_confirm_frames` a 2 o 3 y repetir la toma — comparar métricas
   antes/después igual que se hizo con los fixes 1/2/3 del 08/07.

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
