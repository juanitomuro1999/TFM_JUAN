# Capítulo 7 — Resultados y evaluación (borrador)

> **Estado: borrador en progreso**, generado el 2026-07-09 a partir de las
> tomas ya recogidas en `validation/runs/`. Preparado sin acceso al robot —
> pendiente de completar con las tomas que faltan (ver 7.6) antes de darlo
> por cerrado. La metodología completa de captura/análisis está en
> [`validation/README.md`](../validation/README.md).

## 7.1 Metodología de validación

Cada toma se graba en el NUC como rosbag2 (`validation/record_run.sh`), se
convierte a CSV/TUM (`validation/bag_to_csv.py`) y se analiza en el portátil
(`validation/plot_run.py`), que genera `metrics.txt` y cuatro figuras:
`dist_vs_t.png`, `angle_vs_t.png`, `vel_vs_t.png`, `trayectoria.png`. Las
métricas estándar por toma son: error de distancia al objetivo (MAE y RMS),
error angular medio, velocidades máximas, % de tiempo con persona detectada
y número de pérdidas de detección.

Como se explica en 7.5, algunas cifras citadas en `PROGRESO.md` (% de saltos
de posición, % de saturación angular) se calcularon con un script *ad-hoc*
de la sesión 2026-07-08 que no forma parte de este pipeline — se citan aquí
con esa salvedad.

## 7.2 Configuración experimental

- **Robot:** TurtleBot 2 / base Kobuki, NUC `nuc-224`, ROS 2 Jazzy.
- **Sensores:** RPLIDAR A2M8 + cámara Logitech C270.
- **Entorno:** laboratorio de robótica UJI (interior, suelo de baldosas).
- **Distancia objetivo (`target_distance`):** 1.50 m en la toma del 25/06;
  1.00 m en las tomas del 08/07 (parámetro ajustado entre sesiones).
- **Activación del seguimiento:** gesto por cámara en condiciones normales;
  en las tomas del 08/07 se usó un workaround manual por SSH porque el
  gesto no era fiable con el encuadre de cámara de ese día (ver
  `docs/sesion_siguiente.md`, objetivo 1).

## 7.3 Resultado 1 — Fusión sensorial sin movimiento (2026-06-25)

Primera validación del fallback de fusión LiDAR-cámara (`docs/decisiones.md`,
entrada 2026-06-25), con la base inhibida (`/cmd_vel` redirigido, el robot no
se mueve) para poder probar el mecanismo de detección con seguridad antes de
validarlo en movimiento.

| Métrica | Valor |
|---|---|
| Duración | 23.5 s (285 muestras) |
| Distancia objetivo | 1.50 m |
| Error distancia MAE / RMS | 0.627 m / 0.733 m |
| Distancia mín. / máx. | 1.27 m / 3.41 m |
| % tiempo persona detectada | **100.0 %** |
| Nº pérdidas de detección | **0** |
| Desviación rumbo cámara vs. clúster elegido | ~6° (`bearing_sign=-1.0` confirmado) |

**Lectura:** con el fallback de fusión activo, la detección fue continua
durante toda la toma pese a que el LiDAR por sí solo no distinguía piernas
de forma fiable (motivación original del fallback, ver `docs/02_arquitectura.md`
§2.3.1). El error angular medio (172.3°, no tabulado arriba) no es
representativo del rumbo real: al estar la base inhibida, `wz` nunca corrige
la orientación hacia la persona, así que esa cifra mide la falta de
movimiento, no un fallo de detección — se excluye de la lectura de esta
toma por ese motivo.

![Distancia vs. tiempo — fusión sin movimiento](../validation/runs/fusion_track_20260625/figs/dist_vs_t.png)
![Trayectoria — fusión sin movimiento](../validation/runs/fusion_track_20260625/figs/trayectoria.png)

## 7.4 Resultado 2 — Progresión de fixes de continuidad en movimiento (2026-07-08)

Primera prueba de seguimiento con el robot moviéndose de verdad. La toma
inicial reveló saltos de detección y saturación angular casi permanente
(motivación de los tres fixes de `docs/decisiones.md`, entrada
2026-07-08); las dos tomas siguientes verifican cada fix por separado.

| Toma | Duración | % detección | Pérdidas detec. | MAE dist. | RMS dist. | Saltos >0.8m* | Saturación `wz`* |
|---|---|---|---|---|---|---|---|
| Original (sin fix) | 759.8 s | 32.3 %†  | 79 | 0.519 m | 0.935 m | 3.5 % | 95.7 % |
| + fix 1 (gate continuidad) | 249.0 s | 71.7 % | 43 | 0.534 m | 0.725 m | 2.2 % | 99.3 % |
| + fix 2 y 3 (Mahalanobis + rate-limit `wz`) | 53.1 s | **82.6 %** | **13** | 0.491 m | **0.609 m** | **0.7 %** | 86.9 % |

\* Saltos de posición >0.8m y % de saturación angular con posición
localmente estable (ventana 1.0s, radio 0.15m — ver `validation/plot_run.py`).
**Reproducido 2026-07-21 (Sesión 4 de lab)** con el pipeline committeado
(`bag_to_csv.py` ejecutado en el NUC + `plot_run.py` en el portátil) sobre
los tres bags originales — ver `docs/decisiones.md` (2026-07-21) para el
detalle completo, incluida la comparación con las cifras *ad-hoc* de
`PROGRESO.md` (2026-07-08) que se citaban aquí hasta hoy: el % de saltos
reprodujo con exactitud en las tomas fix1/fix2 (2.2% y 0.7%) pero salió
bastante más bajo en la toma original (3.5% frente al 12.1% ad-hoc);
la saturación **no** reprodujo la tendencia decreciente del cálculo
ad-hoc — se mantiene alta en las tres tomas, ver lectura revisada abajo.

† El 32.3% corresponde al bag completo (759.8s, incluye el tiempo de
depuración del gesto antes de que empezara el seguimiento real).
`PROGRESO.md` reporta 56.9% para la ventana de ~130s de seguimiento real
tras filtrar ese tramo inicial — **cifra más representativa del
comportamiento en TRACKING**, pero no recalculada aquí porque el filtrado se
hizo a mano, no con un script committeado.

**Lectura (revisada 2026-07-21):** los tres fixes encadenados sí redujeron
de forma clara los saltos de posición implausibles (3.5%→2.2%→0.7%) y, como
efecto colateral, subieron la detección (71.7%→82.6%): menos saltos → Kalman
más estable → la FSM pierde menos el track. **La saturación de velocidad
angular, en cambio, no mejora de forma sostenida con estos tres fixes** —
se mantiene muy alta en las tres tomas (95.7%, 99.3%, 86.9% con posición
estable; 96.9%, 99.4%, 80.6% en global), sin la tendencia decreciente que
sugerían las cifras *ad-hoc* del 08/07. Los tres fixes de esta tabla atacan
la *continuidad de la detección* (gate de continuidad, Mahalanobis,
rate-limit de `wz`), no la *ganancia* del controlador angular — el ajuste
que sí reduce la saturación a corta distancia (`near_gain`, zona muerta
angular) se añadió después, el 2026-07-15 (ver `docs/decisiones.md`), y no
está reflejado en estos tres bags del 08/07. Queda como limitación abierta,
no como logro de esta serie de fixes — ver 7.5. Los tres bags decrecen en
duración porque las pruebas se fueron acotando a medida que el
comportamiento se estabilizaba, no por una razón experimental — ver 7.5.

![Distancia vs. tiempo — fix 2+3](../validation/runs/20260708_movimiento_fix2_kalman_wz/analysis/figs/dist_vs_t.png)
![Velocidad vs. tiempo — fix 2+3](../validation/runs/20260708_movimiento_fix2_kalman_wz/analysis/figs/vel_vs_t.png)
![Trayectoria — fix 2+3](../validation/runs/20260708_movimiento_fix2_kalman_wz/analysis/figs/trayectoria.png)

*(Figuras equivalentes de las tomas "original" y "fix 1" disponibles en
`validation/runs/20260708_movimiento_original/analysis/figs/` y
`validation/runs/20260708_movimiento_fix1_gating/analysis/figs/` para la
comparación visual completa cuando se redacte la versión final.)*

## 7.5 Limitaciones de los resultados actuales

- **Reproducibilidad de "saltos"/"saturación" — resuelta 2026-07-21, con
  matices:** las cifras originales de la tabla 7.4 se habían calculado con
  un script que no estaba en el repo (`bag_to_csv_direct.py`, sesión
  2026-07-08). Desde el 2026-07-09 ese cálculo forma parte del pipeline
  estándar (`bag_to_csv.py`/`plot_run.py`), y el 2026-07-21 (Sesión 4 de
  lab) se re-ejecutó sobre los tres bags originales del 08/07 en el NUC
  (que sí tiene ROS 2). El % de saltos de posición reprodujo con
  exactitud en dos de las tres tomas y quedó más bajo en la tercera — se
  considera una limitación menor, esperable de una metodología
  reconstruida y no una recuperación literal del script perdido. **La
  saturación angular, en cambio, no reprodujo la tendencia decreciente
  original en absoluto** — con el pipeline reproducible se mantiene alta
  (86-99%) en las tres tomas, sin la mejora de 94.5%→12.4% que sugerían
  las cifras ad-hoc. Tabla y lectura de 7.4 ya actualizadas con las cifras
  reproducibles. Ver `docs/decisiones.md` (2026-07-21) para el detalle
  completo de la comparación y la hipótesis de por qué diverge (denominador
  pequeño de muestras "estables" en las tomas cortas de fix1/fix2, y
  posible efecto de acercamiento a corta distancia sin `near_gain`, que no
  existía todavía el 08/07) — hipótesis sin confirmar, no verificada hoy.
- **N=1 por condición:** cada fila de la tabla 7.4 es una única toma, no una
  media de repeticiones — no hay todavía medida de varianza entre pruebas
  equivalentes. `validation/README.md` recomienda 2-3 repeticiones por
  escenario para el capítulo final.
- **Duraciones no comparables directamente:** las tres tomas de la tabla
  7.4 tienen duraciones muy distintas (759.8s / 249.0s / 53.1s), así que las
  cifras son proporciones dentro de cada toma, no valores normalizados a un
  mismo tiempo o misma distancia recorrida.
- **`near_gain` sin aislar:** ninguna toma actual aísla específicamente el
  caso que motivó ese parámetro (giro a corta distancia, 0.5-0.7m) — las
  tomas de movimiento mezclan alejarse/acercarse/lateral/giro.
- **Gate de continuidad reforzado (2026-07-09) sin validar:** el cambio de
  `docs/decisiones.md` (confirmación por consistencia,
  `continuity_confirm_frames`) se preparó sin robot y solo se verificó con
  pruebas de lógica aisladas — la tabla 7.4 es anterior a ese cambio y no lo
  refleja.
- **Gesto de activación no utilizado:** las tomas de movimiento se activaron
  con un workaround manual por SSH, no con el gesto real (encuadre de
  cámara pendiente de corregir) — el objetivo específico 1 del TFM no está
  representado en estos resultados todavía.

## 7.6 Pendiente para completar este capítulo

- [ ] Validar `near_gain` de forma aislada (giro a corta distancia).
- [ ] Repetir tomas con `continuity_confirm_frames` ajustado y comparar
  contra la tabla 7.4 (mismo formato).
- [ ] Re-ejecutar `bag_to_csv.py`/`plot_run.py` (ya actualizados, 2026-07-09)
  sobre los tres bags de la tabla 7.4 en una máquina con ROS 2, y comparar
  las cifras nuevas de saltos/saturación contra las de la tabla — actualizar
  la tabla si difieren.
- [ ] Repeticiones (2-3 tomas por escenario) para poder hablar de varianza,
  no solo de un único valor por condición.
- [ ] Grabar al menos una toma con el gesto real funcionando (tras
  re-encuadrar la cámara), no con el workaround manual.
- [ ] Incorporar resultados de Nav2 si se decide abordarlo (objetivo 3,
  sigue pendiente de decidir alcance).
- [ ] Sustituir este borrador por prosa de memoria una vez el conjunto de
  datos esté completo — este archivo está pensado como andamiaje de
  trabajo, no como texto final de la memoria.
