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
