# Validación experimental (Capítulo 7)

Pipeline para grabar tomas de seguimiento, extraer telemetría y generar las
gráficas y métricas de resultados de la memoria. Diseñado para la restricción
del NUC: **grabar solo necesita ROS 2** (el NUC no tiene internet ni `tmux`); el
**análisis y las gráficas se hacen en el portátil** (con `matplotlib`/`evo`).

```
NUC (nuc-224)                      Portátil (labrob01, con internet)
─────────────                      ──────────────────────────────────
record_run.sh   ──(scp bag)──▶     bag_to_csv.py ─▶ plot_run.py ─▶ figs/ + metrics.txt
                                                  └▶ evo (trayectoria)
```

## 1. Grabar una toma (en el NUC)

Con el sistema ya lanzado y el robot **siguiendo** a la persona (estado TRACKING):

```bash
cd ~/ros2_ws/src/TFM_JUAN
bash validation/record_run.sh recta_3m 60     # etiqueta + duración(s) opcional
# o, hasta Ctrl-C:
bash validation/record_run.sh curva
```

Graba en `~/tfm_bags/<fecha>_<etiqueta>/` (fuera del repo). Topics incluidos:
telemetría, `/odom`, comando real a la base, posición de la persona,
`/person_detected`, `/control/mode`, `/scan` y `/tf`.

**Tomas sugeridas para el Capítulo 7** (repetir cada una 2-3 veces):

| Etiqueta      | Escenario                                                        |
|---------------|------------------------------------------------------------------|
| `recta`       | Persona camina en línea recta alejándose                         |
| `curva`       | Persona describe una curva / cambio de dirección                 |
| `parada`      | Persona se detiene → comprobar standoff a `target_distance` (1 m) |
| `corto`       | Persona se acerca a <1 m → **valida el fix del giro brusco**     |
| `oclusion`    | Persona pasa tras un obstáculo → predicción Kalman + recuperación |
| `obstaculo`   | Obstáculo en la trayectoria → evasión                            |

Copia los bags al portátil al terminar la sesión:

```bash
scp -r user@10.48.0.1:~/tfm_bags/<carpeta> .
```

## 2. Extraer a CSV (NUC o portátil, requiere ROS)

```bash
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
python3 validation/bag_to_csv.py <carpeta_bag>
```

Genera en `<carpeta_bag>/analysis/`: `telemetry.csv`, `odom.csv`, `odom.tum`,
`cmd_vel.csv`, `detection.csv`. Solo usa la librería estándar + ROS (sin internet).

## 3. Gráficas y métricas (portátil, requiere matplotlib)

```bash
python3 validation/plot_run.py <carpeta_bag>/analysis --target 1.0
```

Produce en `analysis/figs/`: `dist_vs_t.png`, `angle_vs_t.png`, `vel_vs_t.png`,
`trayectoria.png`, y un `metrics.txt` con: error de distancia (MAE y RMS)
respecto al objetivo, error angular medio, velocidades máximas, % de tiempo con
persona detectada y nº de pérdidas de detección.

## 4. Métricas de trayectoria con evo (opcional)

`odom.tum` está en formato TUM. Para visualizar la trayectoria:

```bash
pip install evo --upgrade          # solo una vez, en el portátil con internet
evo_traj tum <carpeta_bag>/analysis/odom.tum -p --plot_mode xy
```

> **Nota sobre evo y *ground truth*:** sin sistema de captura de movimiento no
> hay trayectoria de referencia "real", así que las métricas APE/RPE de evo no
> aplican directamente al seguimiento. Su uso aquí es (a) **graficar** la
> trayectoria estimada y (b) si grabas también la pose corregida por SLAM,
> comparar SLAM vs `/odom` para cuantificar la **deriva odométrica**:
>
> ```bash
> evo_ape tum slam_pose.tum odom.tum -va --plot     # deriva odom respecto a SLAM
> ```
>
> Para el seguimiento en sí, las métricas que de verdad importan para el
> Capítulo 7 son las de `metrics.txt` (error de distancia y angular, pérdidas),
> derivadas de la telemetría — no de evo.

## Checklist de una sesión de validación

- [ ] Lanzar robot + person_follower y confirmar TRACKING estable.
- [ ] Grabar las tomas de la tabla (2-3 repeticiones c/u), anotando etiqueta y qué pasó.
- [ ] `scp` de los bags al portátil al acabar (el NUC tiene espacio limitado).
- [ ] `bag_to_csv.py` + `plot_run.py` por cada toma.
- [ ] Guardar `figs/` y `metrics.txt` para el Capítulo 7.
