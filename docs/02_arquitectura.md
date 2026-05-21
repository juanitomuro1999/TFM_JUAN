# Capítulo 2 — Arquitectura del sistema

## 2.1 Visión general

El sistema se organiza como un conjunto de nodos ROS 2 independientes que se comunican exclusivamente a través del bus de mensajes de ROS 2 (DDS). Esta arquitectura desacoplada permite:

- Activar o desactivar nodos individuales sin afectar al resto.
- Sustituir módulos (p. ej., cambiar el detector de personas) sin reescribir el sistema.
- Ejecutar subconjuntos de nodos durante el desarrollo y las pruebas.

Todo el sistema se empaqueta bajo el paquete ROS 2 `person_follower` (`ament_python`).

## 2.2 Diagrama de nodos y topics

```
[RPLIDAR A2M8]──/scan──────────►[detection_node]────/person_detected──────►┐
                │                      │                                     │
                │                      └──/person_position──────────────────►│
                │                                                             │
[Cámara USB]──/image_raw──►[visual_detection_node]──/person_detected_visual►│
                                        │                                     │
                                        └──/gesture_command──────────────────►│
                                                                              ▼
[Base Kobuki]──/odom──────────────────────────────────────────────►[control_node (FSM)]
               /tf                                                        │
                                                              enable_tracking (svc)
                                                                          │
               /scan──────────────────────────────────────────►[tracking_node]
                                                                    (Kalman + DWA)
                                                                          │
                                                               /tracking/velocity_cmd
                                                                          │
                                                                          ▼
                                                              [control_node]──/commands/velocity──►[Kobuki]

[SLAM Toolbox]◄──/scan, /odom, /tf─────────────────────────────────────────
               └──/map, /pose──────────────────────────────────────────────►[Nav2] (Fase 3)

[user_interface_node]◄──todos los /status, /clusters, /visualization──────►[RViz 2]
```

## 2.3 Descripción de cada nodo

### 2.3.1 `detection_node`

**Función:** detección de personas usando el LiDAR.

**Algoritmo:**
1. Se aplica un filtro de mediana a las medidas del LiDAR para reducir ruido.
2. Se interpolan los puntos para aumentar la resolución angular.
3. Los puntos 2D se clusterizán con DBSCAN (eps=0.1 m, min_samples=15).
4. Se filtran clusters con características de pierna humana (tamaño, radio, forma).
5. Se buscan pares de clusters (dos piernas) dentro de una distancia coherente.
6. La posición estimada de la persona se fusiona con la detección visual (debounce + timeout).

**Parámetros configurables (config.yaml):**
- `max_detection_distance`: 6.0 m
- `dbscan_eps`: 0.1 m
- `min/max_leg_cluster_size`: 30–80 puntos
- `camera_timeout`: 1.0 s

**Topics suscritos:** `/scan`, `/person_detected_visual`  
**Topics publicados:** `/person_detected`, `/person_position`, `/clusters/general`, `/clusters/legs`

---

### 2.3.2 `visual_detection_node`

**Función:** detección de personas y reconocimiento de gestos por cámara.

**Algoritmo:**
1. Se suscribe a `/image_raw` (Logitech C270, 640×480@30fps).
2. Procesa cada frame con **MediaPipe Pose** para detectar el esqueleto humano.
3. Procesa simultáneamente con **MediaPipe Hands** para detectar gestos.
4. Gestos reconocidos:
   - `start_tracking`: pulgar arriba (índice y meñique bajos).
   - `stop_tracking`: mano abierta (pulgar + índice + meñique por encima de la muñeca).
5. Publica imagen anotada en `/camera/image_processed`.

**Topics suscritos:** `/image_raw`  
**Topics publicados:** `/person_detected_visual`, `/gesture_command`, `/pose/keypoints`, `/camera/image_processed`

---

### 2.3.3 `tracking_node`

**Función:** estimar la posición de la persona y calcular comandos de velocidad.

**Algoritmo:**
1. Aplica un **filtro de Kalman** (estado: [x, y, vx, vy]) sobre `/person_position`.
2. Calcula distancia y ángulo hacia la persona.
3. Aplica **evasión de obstáculos**: analiza el sector frontal ±45° del LiDAR. Si hay obstáculos a <0.6 m, genera una fuerza de repulsión angular y reduce la velocidad lineal.
4. Publica `/tracking/velocity_cmd` (Twist).
5. Si la persona desaparece más de 2 segundos, detiene el robot.

**Servicio:** `enable_tracking` (SetBool) — activado/desactivado por `control_node`.

---

### 2.3.4 `control_node`

**Función:** máquina de estados finitos (FSM) central del sistema.

**Estados:**
```
INIT → IDLE ←→ TRACKING
               ↕
             MANUAL
               ↓
            SHUTDOWN
```

- **IDLE:** esperando persona autorizada.
- **TRACKING:** persona detectada + usuario autorizado → retransmite velocidades.
- **MANUAL:** modo teleoperación por teclado (w/s/a/d/x, q para alternar, p para apagar).
- **SHUTDOWN:** secuencia de apagado coordinado de todos los nodos.

**Control de autorización:** si `camera_enabled=True`, se requiere gesto `start_tracking` para comenzar seguimiento. Si `camera_enabled=False`, se inicia automáticamente.

---

### 2.3.5 `collision_handling_node`

**Función:** monitorización de distancia mínima al obstáculo más cercano.

Publica `/collision_detected` (Bool) si algún punto del scan está a menos de 0.4 m. Actualmente el `control_node` no reacciona a este topic (previsto para Fase 3 con Nav2).

---

### 2.3.6 `user_interface_node`

**Función:** visualización en tiempo real del estado del sistema.

- Lanza RViz 2 automáticamente con la configuración del paquete.
- Publica markers de visualización: posición estimada de persona (esfera verde), clusters LiDAR (puntos azul/rojo), marker del robot (cilindro amarillo).
- Muestra HUD de texto en RViz con estado de cada nodo.
- Publica `/diagnostics` (DiagnosticArray) con el modo de control.
- Refresca estado en consola cada 5 segundos.

---

### 2.3.7 `slam_node` (experimental, desactivado por defecto)

Implementación básica propia de SLAM 2D basada en datos del LiDAR. Publica un `OccupancyGrid` en `/map` y una TF estática `map→odom`. **Sustituido en Fase 2 por SLAM Toolbox**, que ofrece mayor robustez, cierre de bucles y serialización del mapa.

---

## 2.4 Gestión del apagado coordinado

El sistema implementa un protocolo de apagado coordinado para evitar que el robot quede con velocidades activas:

1. `control_node` publica `True` en `/system_shutdown`.
2. Todos los nodos suscritos a `/system_shutdown` detienen su actividad y responden en `/shutdown_confirmation`.
3. `control_node` espera confirmaciones antes de destruir el nodo.

---

## 2.5 Árbol de transformaciones (TF)

```
map (Fase 2 – SLAM Toolbox)
 └── odom  (publicado por kobuki_ros_node)
      └── base_footprint
           └── laser  (TF estática: rotación π sobre Z, RPLIDAR invertido)
```

La TF `base_footprint → laser` se publica estáticamente con `tf2_ros static_transform_publisher` con una rotación de 180° (π rad) en Z, ya que el RPLIDAR está montado invertido en el robot.

---

## 2.6 Parámetros de configuración

Todos los parámetros ajustables se centralizan en `person_follower/config/config.yaml`. Esto permite cambiar umbrales de detección, distancias de seguridad y comportamientos sin recompilar.

Los parámetros de SLAM Toolbox se encuentran en `person_follower/config/slam_toolbox_params.yaml`.

---

## 2.7 Diagrama de paquetes y dependencias ROS 2

```
person_follower
├── rclpy
├── sensor_msgs        (LaserScan, Image)
├── geometry_msgs      (Twist, Point)
├── nav_msgs           (OccupancyGrid, Odometry)
├── std_msgs / std_srvs
├── visualization_msgs (Marker)
├── diagnostic_msgs
├── cv_bridge
├── tf2_ros
├── [Python] numpy, scikit-learn, mediapipe, opencv
└── [externo] kobuki_ros, rplidar_ros, slam_toolbox, nav2_bringup
```
