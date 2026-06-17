# Prompt — Próxima sesión

> Repo: `juanitomuro1999/TFM_JUAN` (rama `main`). Código local en `~/ros2_ws/src/TFM_JUAN` en
> `labrob01`. Robot: NUC **nuc-224**, `ssh user@10.48.0.1` (password `qwerty`),
> `ROS_DOMAIN_ID=24`, ROS 2 Jazzy. Para sincronizar código: `bash sync_nuc.sh` (revisar que las
> rutas siguen siendo correctas — `person_follower` dentro de `ros2_ws/src` en el NUC).
>
> **Importante:** en el NUC **no hay `tmux`** ni acceso a internet. Para procesos persistentes,
> usar `nohup ... > /tmp/algo.log 2>&1 & disown` por SSH (patrón usado toda la sesión anterior).

## Estado heredado de la sesión 2026-06-17 (no repetir este trabajo, solo verificar)

- ✅ Cámara funcionando: causa real era encuadre/distancia (no umbral). HOG necesita cuerpo
  entero en cuadro (~2m+); a la distancia real de seguimiento (~1m) usar MediaPipe.
- ✅ MediaPipe Pose instalado offline en el NUC (`~/.local/lib/python3.12/site-packages/mediapipe`,
  incluye `pose_landmark_lite.tflite`). Persiste tras reinicio del NUC.
- ✅ Bug de `ros2_ws` con copia duplicada de `kobuki_node`/`rplidar_ros` — eliminado. Si
  `kobuki_node` vuelve a fallar con `failed to create guard condition: context argument is null`,
  comprobar primero `ls ~/ros2_ws/install/` — no debe contener `kobuki_node` ni `rplidar_ros`,
  solo `person_follower`.
- ✅ Módulo de interacción por gestos implementado y validado: mano derecha levantada por encima
  del hombro → `start_tracking`; mano izquierda → `stop_tracking`. Requiere MediaPipe (no
  funciona en modo HOG). **Para que el gesto se vea, ponerse a ~2-2.5m de la cámara** (igual que
  para que HOG detectara cuerpo entero).
- ⚠️ RPLIDAR puede dar `SL_RESULT_OPERATION_TIMEOUT` si el cable USB hace mal contacto —
  desconectar y reconectar el cable lo arregló la última vez.
- 🔄 Pendiente sin tocar (ver detalle y razonamiento en `PROGRESO.md` y
  `docs/04_diario_desarrollo.md`, sesión 17 de junio):
  - `tracking_node` satura el giro (±1.0 rad/s) combinado con avance casi a velocidad máxima
    cuando la persona está muy cerca — da la sensación de que el robot "da vueltas sobre sí
    mismo". Sospecha: el ángulo de rumbo se vuelve muy sensible a corta distancia.
  - FSM TRACKING↔IDLE oscila en algunos tramos incluso con detección estable.
  - `OrbbecSDK_ROS2` está en `ros2_ws/src` sin compilar — explorar si la cámara RGBD Orbbec
    Astra puede sustituir/complementar al LIDAR 2D para detección (cambio de arquitectura mayor).

## Objetivo de hoy — propuesta (ajustar si lo ves necesario)

Quedan **2-3 sesiones antes de cerrar a final de junio**. Con cámara, gestos, SLAM y fusión
sensorial ya completados (objetivos 1, 2 y 4 del TFM en `docs/01_introduccion.md`), lo que más
valor aporta ahora es:

1. **Arreglo acotado del giro a corta distancia en `tracking_node`** (bloquea cualquier grabación
   de demo limpia o sesión de validación). No es una reescritura — probablemente baste con
   limitar la velocidad angular o lineal cuando la distancia a la persona cae por debajo de un
   umbral, o revisar cómo se calcula el ángulo de rumbo cuando la persona está muy cerca.
2. **Sesión de validación experimental formal** (grabar rosbag + CSV de telemetría + gráficas +
   métricas con `evo`) — esto genera los resultados que necesita el Capítulo 7 (pendiente) de la
   memoria. Es la pieza que más falta para poder cerrar el TFM con contenido demostrable, más
   allá de seguir añadiendo funcionalidades nuevas.
3. **Decisión sobre Nav2 (objetivo 3):** dado el tiempo restante, valorar si abordarlo como una
   demo mínima (localización AMCL sobre el mapa ya guardado + un solo punto de navegación) o
   dejarlo documentado como trabajo futuro en la memoria. Tomar esta decisión pronto para no
   quedarse sin tiempo a medias.

## Pasos para empezar

```bash
# 1. Sincronizar si hubo cambios locales
cd ~/ros2_ws/src/TFM_JUAN && git pull
bash sync_nuc.sh

# 2. Lanzar el robot (cada bloque en su propia sesión SSH o con nohup)
sshpass -p 'qwerty' ssh user@10.48.0.1
source /opt/ros/jazzy/setup.bash && source ~/kobuki_ws/install/setup.bash && source ~/ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=24

# Kobuki
nohup ros2 launch kobuki_node kobuki_node-launch.py > /tmp/kobuki.log 2>&1 & disown

# RPLIDAR
nohup ros2 launch rplidar_ros rplidar_a2m8_launch.py serial_port:=/dev/rplidar > /tmp/lidar.log 2>&1 & disown

# Sistema person_follower completo (incluye gestos; camera_enabled=True)
nohup ros2 launch person_follower start_person_follower.launch.py > /tmp/follower.log 2>&1 & disown

# 3. Verificar
ros2 node list
timeout 5 ros2 topic hz /scan
timeout 5 ros2 topic hz /person_detected_visual
```

## Checklist de cierre de sesión (igual que hoy)

- [ ] Actualizar `PROGRESO.md` con lo avanzado/encontrado.
- [ ] Si se completa un objetivo del TFM, marcarlo en `docs/01_introduccion.md`.
- [ ] Añadir entrada con fecha en `docs/04_diario_desarrollo.md` (estilo prosa, para la memoria).
- [ ] `git add` + commit + push (remoto ya configurado por SSH, no debería pedir credenciales).
