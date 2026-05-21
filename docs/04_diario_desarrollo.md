# Capítulo 4 — Diario de desarrollo

Registro cronológico del progreso técnico del TFM.

---

## Mayo 2026

### 21 de mayo — Puesta en marcha del robot (Fase 1 completa)

**Contexto:** primera sesión de trabajo con el robot real (nuc-225, 10.48.0.1).

**Trabajo realizado:**

1. **Revisión del repositorio:** se analizó la estructura completa del paquete `person_follower` heredado, identificando los siguientes problemas:
   - `setup.py` usaba `packages=[package_name]` en lugar de `find_packages()`, impidiendo que colcon encontrara los sub-paquetes.
   - `package.xml` declaraba `ament_cmake` como buildtool en lugar de `ament_python`.
   - Dependencias faltantes: `visualization_msgs`, `diagnostic_msgs`, `std_srvs`, `tf2_ros`, `numpy`, `sklearn`.
   - `collision_handling_node` y `slam_node` no registrados en `entry_points` de `setup.py`.
   - Doble suscripción a `/system_shutdown` en `tracking_node.py`.
   - Ruta hardcodeada de RViz en `user_interface_node.py`.

2. **Correcciones aplicadas:** todos los bugs anteriores fueron corregidos y compilados correctamente con `colcon build --symlink-install`.

3. **Conexión SSH al robot:** se accedió al NUC (nuc-225, Ubuntu 24.04, ROS 2 Jazzy) y se realizó un diagnóstico completo del entorno:
   - Dispositivos detectados: `/dev/kobuki` (ttyUSB1, FT232), `/dev/rplidar` (ttyUSB0, CP210x), cámara Logitech C270, cámara Orbbec Astra.
   - Workspaces existentes: `kobuki_ws` (Kobuki + RPLIDAR compilados), `ros2_ws` (person_follower versión anterior).

4. **Identificación de bugs en el robot:**
   - El `kobuki_node_params.yaml` apuntaba a `/dev/ttyUSB0` en lugar de `/dev/kobuki`.
   - El `launch_lidar.bash` usaba `ros2_ws/install` que no tenía `rplidar_ros` compilado; se corrigió a `kobuki_ws/install`.
   - Se detectaron dos instancias de `kobuki_ros_node` ejecutándose simultáneamente, con el proceso antiguo bloqueando el puerto del RPLIDAR.

5. **Lanzamiento exitoso de sensores:**
   - Kobuki: `Version info - Hardware: 1.0.4. Firmware: 1.2.0` — conectado.
   - RPLIDAR: `S/N: BAA2EDF9, Firmware 1.31, status OK, 10 Hz` — escaneando.
   - Topics activos verificados: `/scan`, `/odom`, `/commands/velocity`, `/tf`.

6. **Test de movimiento:** se publicó una velocidad de 0.1 m/s en `/commands/velocity` durante ~1 segundo. **El robot se movió correctamente.**

7. **Despliegue de la nueva versión:** el paquete `person_follower` (arquitectura multi-nodo, TFM_JUAN) fue copiado al robot y compilado exitosamente. Los 7 ejecutables fueron verificados con `ros2 pkg executables`.

**Estado al cierre de la sesión:**
- ✅ Fase 1 completada
- ✅ Robot operativo (Kobuki + RPLIDAR)
- ✅ Paquete person_follower v0.0.1 desplegado en el robot
- 🔄 Fase 2 iniciada: SLAM Toolbox en desarrollo

---

### 21 de mayo (continuación) — SLAM Toolbox operativo

**Diagnóstico del problema:**

El nodo `async_slam_toolbox_node` arrancaba pero no publicaba `/map`. Diagnóstico en el robot:
```
ros2 lifecycle list /slam_toolbox
```
El nodo se encontraba en estado `unconfigured` — es un **lifecycle node** de ROS 2 que requiere transiciones explícitas `configure → active` antes de operar.

**Causa raíz:** el `slam_toolbox.launch.py` original lanzaba el nodo sin gestión de ciclo de vida. El nodo esperaba ser configurado externamente.

**Solución aplicada:**

1. **Verificación manual:** se configuró y activó el nodo manualmente con:
   ```bash
   ros2 lifecycle set /slam_toolbox configure
   ros2 lifecycle set /slam_toolbox activate
   ```
   Confirmando que `/map` y `/map_metadata` empezaron a publicarse inmediatamente.

2. **Corrección del launch file:** se añadió un nodo `lifecycle_manager` (de `nav2_lifecycle_manager`) con `autostart: true` y `bond_timeout: 0.0`:
   - `autostart: true` — configura y activa `slam_toolbox` automáticamente al arrancar.
   - `bond_timeout: 0.0` — deshabilita el heartbeat de monitorización que `slam_toolbox` no implementa y que causaba un error de bond en los logs.

3. **Resultado:** log de lanzamiento limpio:
   ```
   [lifecycle_manager]: Configuring slam_toolbox
   [slam_toolbox]: Configuring
   [slam_toolbox]: Using solver plugin solver_plugins::CeresSolver
   [lifecycle_manager]: Activating slam_toolbox
   [slam_toolbox]: Activating
   [lifecycle_manager]: Managed nodes are active
   [slam_toolbox]: Registering sensor: [Custom Described Lidar]
   ```
   Topics publicados: `/map`, `/map_metadata`, `/slam_toolbox/feedback`, `/slam_toolbox/scan_visualization`, `/slam_toolbox/graph_visualization`.

**Estado al cierre:**
- ✅ SLAM Toolbox operativo: nodo activo, `/map` publicando
- ✅ `slam_toolbox.launch.py` corregido con lifecycle manager
- ✅ Mapa del laboratorio generado y guardado (ver sección siguiente)

---

### 21 de mayo (continuación) — Test del sistema person_follower completo

**Contexto:** con SLAM activo en el robot, se lanzó `bringup_full.launch.py slam_enabled:=false` para probar los 6 nodos del sistema de seguimiento.

**Bugs encontrados y corregidos:**

| Nodo | Bug | Corrección |
|------|-----|-----------|
| `visual_detection_node` | `import mediapipe` falla si no está instalado → crash | `try/except ImportError` + auto-desactivación con log de aviso |
| `visual_detection_node` | `publish_status()` llamado antes de crear el publisher (cuando `enabled=False`) | Publisher creado antes del check de `enabled` |
| `collision_handling_node` | Mismo bug: `publish_status()` antes del publisher | Igual que arriba |

**mediapipe no disponible en el robot:** el NUC-225 no tiene acceso a internet (pip y apt fallan). El `visual_detection_node` se desactiva automáticamente con un aviso y el sistema continúa en modo solo-LiDAR.

**sklearn no disponible:** igual, sin internet. Se descargaron los wheels en el PC local y se transfirieron vía SCP:
```bash
pip3 download scikit-learn --python-version 312 --platform manylinux2014_x86_64 --only-binary=:all: -d /tmp/sklearn_wheels/
sshpass -p 'qwerty' scp /tmp/sklearn_wheels/*.whl user@10.48.0.1:/tmp/
pip3 install /tmp/*.whl --break-system-packages  # en el robot
```

**Resultado del lanzamiento:**

| Nodo | Estado |
|------|--------|
| `detection_node` | ✅ Activo, detectando persona a 0.7–1.1m |
| `visual_detection_node` | ⚠️ Desactivado automáticamente (sin mediapipe) |
| `tracking_node` | ✅ Activo, publicando velocity_cmd |
| `control_node` | ✅ Activo, FSM IDLE→TRACKING |
| `collision_handling_node` | ✅ Activo, obstacle a 0.57m detectado |
| `user_interface_node` | ✅ Activo (RViz no carga en headless, no fatal) |

**Pipeline completo verificado:**
```
/scan → detection_node (DBSCAN) → /person_detected
→ control_node (FSM) → /tracking/velocity_cmd
→ /commands/velocity (Kobuki) @ ~10 Hz
```

**Ajustes en config.yaml:**
- `camera_enabled: False` — FSM entra en TRACKING automáticamente sin gesto (modo headless)
- `dbscan_min_samples: 5`, `min_leg_cluster_size: 5` — parámetros reducidos para detectar piernas a 0.5–2m con RPLIDAR A2M8 (57 pts/m de arco → ~5 pts por pierna a 1m)

**Estado:**
- ✅ Sistema person_follower completo probado en el robot real
- ✅ Detección LiDAR funcionando (DBSCAN con sklearn)
- ✅ FSM IDLE↔TRACKING funcionando
- ✅ Robot recibe velocidades de seguimiento (~10 Hz)
- 🔄 Pendiente: instalar mediapipe (necesita conexión o paquete offline)

---

### 21 de mayo (continuación) — Mapa del laboratorio

**Movimiento de exploración:**

Con SLAM activo, se ejecutó una secuencia de movimiento autónoma desde el PC vía `/commands/velocity`:

| Paso | Movimiento | Duración | Distancia |
|------|-----------|----------|-----------|
| 1 | Adelante (0.2 m/s) | 3 s | ~0.6 m |
| 2 | Giro izquierda (0.4 rad/s) | 2 s | — |
| 3 | Adelante (0.2 m/s) | 3 s | ~0.6 m |
| 4 | Giro derecha (−0.4 rad/s) | 3 s | — |
| 5 | Adelante (0.2 m/s) | 2 s | ~0.4 m |

**Resultado del mapa (`/map_metadata`):**
- Resolución: 0.05 m/celda (5 cm)
- Tamaño: 261 × 338 celdas ≈ 13 × 17 metros
- Origen: (−8.32, −11.35) m

**Guardado con `map_saver_cli`:**
```
[map_io]: Received a 261 X 338 map @ 0.05 m/pix
[map_io]: Writing map occupancy data to mapa_laboratorio.pgm
[map_saver]: Map saved successfully
```

Archivos generados en `maps/`:
- `mapa_laboratorio.pgm` — imagen de ocupación (87 KB)
- `mapa_laboratorio.yaml` — metadatos (resolución, origen, umbrales)

**Estado:**
- ✅ Fase 2 completada: SLAM operativo + mapa del laboratorio guardado

---

## Junio 2026 (planificado)

### Semana 1–2 — Integración de SLAM Toolbox

**Objetivos:**
- [ ] Probar `slam_toolbox.launch.py` en el robot con el RPLIDAR activo.
- [ ] Mapear una zona del laboratorio y guardar el mapa.
- [ ] Verificar la TF `map → odom → base_footprint → laser`.

### Semana 3–4 — Módulo de interacción mejorado

**Objetivos:**
- [ ] Probar detección de gestos con cámara Logitech C270.
- [ ] Calibrar umbrales de `gesture_threshold` con el robot real.
- [ ] Evaluar latencia del bucle visual (camera → gesture → tracking enable).

---

## Julio 2026 (planificado)

### Fase 3 — Navegación autónoma (Nav2)

**Objetivos:**
- [ ] Configurar Nav2 con el mapa generado por SLAM Toolbox.
- [ ] Probar navegación a waypoints predefinidos en el laboratorio.
- [ ] Implementar comportamiento de guiado: seguir persona → navegar a destino.
- [ ] Evaluar planificador (NavFn vs Smac).

---

## Agosto 2026 (planificado)

### Fase 4 — Validación experimental

**Objetivos:**
- [ ] Diseñar escenario de evaluación en las instalaciones de la UJI.
- [ ] Métricas: tasa de detección, tiempo de respuesta, trayectoria real vs planificada.
- [ ] Evaluar robustez ante oclusiones y cambios de iluminación.
- [ ] Redactar sección de resultados.

---

## Septiembre 2026 (planificado)

### Fase 5 — Cierre

**Objetivos:**
- [ ] Revisión final del documento de TFM.
- [ ] Preparación de la presentación y defensa.
- [ ] Repositorio con tag `v1.0.0`.
