# TFM — Desarrollo e implementación de un sistema de seguimiento de personas sobre un robot móvil (Parte 2 – Extensión)

**Autor:** Juan Muriel Rovira  
**Tutor:** Enric Cervera  
**Universidad:** Universitat Jaume I (UJI)  
**Curso:** 2025–2026  
**Versión actual:** 0.3.0 | Fase 2 completada (interacción por gestos + SLAM) — Fase 3 (Nav2) siguiente

---

## Descripción general

Este repositorio contiene el desarrollo del Trabajo de Fin de Máster (TFM) titulado:

> *"Development and Implementation of a Person-Following System on a Mobile Robot – Part 2 Extension"*

El proyecto extiende un sistema previo de seguimiento de personas sobre un TurtleBot 2 (base Kobuki) añadiendo:

- Módulo de interacción humano-robot basado en gestos (MediaPipe)
- Cartografía autónoma del entorno mediante SLAM (SLAM Toolbox + LiDAR RPLIDAR)
- Navegación autónoma completa con Nav2 (localización, planificación de rutas, navegación a objetivos)
- Fusión sensorial LiDAR + cámara para detección de personas
- Arquitectura ROS 2 modular, extensible y documentada

---

## Plataforma hardware

| Componente | Modelo | Conexión |
|---|---|---|
| Base móvil | Kobuki (TurtleBot 2) | `/dev/kobuki` → USB |
| Ordenador a bordo | Intel NUC | — |
| LiDAR | RPLIDAR A2M8 | `/dev/rplidar` → USB |
| Cámara RGB | Logitech C270 | USB |
| Cámara RGBD | Orbbec Astra | USB (pendiente integración) |

---

## Software

| Capa | Tecnología |
|---|---|
| Sistema operativo (robot) | Ubuntu 24.04 LTS |
| Middleware | ROS 2 Jazzy |
| Detección visual | MediaPipe Pose + Hands |
| Detección LiDAR | DBSCAN (scikit-learn) |
| SLAM | SLAM Toolbox (online async) |
| Navegación | Nav2 |
| Visualización | RViz 2 |

---

## Arquitectura del sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        SENSORES                                 │
│   RPLIDAR A2M8          Cámara USB           Base Kobuki        │
│   /scan                 /image_raw            /odom  /tf        │
└────────┬───────────────────────┬──────────────────┬────────────┘
         │                       │                  │
         ▼                       ▼                  │
┌──────────────┐       ┌──────────────────┐         │
│detection_node│       │visual_detection_ │         │
│  (DBSCAN +   │       │node (MediaPipe   │         │
│  clustering) │       │ Pose + Hands)    │         │
└──────┬───────┘       └────────┬─────────┘         │
       │/person_position        │/person_detected_   │
       │/person_detected        │visual              │
       │                        │/gesture_command    │
       └──────────┬─────────────┘                   │
                  ▼                                  │
         ┌──────────────┐                            │
         │ control_node │◄───────────────────────────┘
         │    (FSM)     │  /odom
         │IDLE/TRACKING │
         │MANUAL/SHTDWN │
         └──────┬───────┘
                │enable_tracking (srv)
                ▼
         ┌──────────────┐      ┌─────────────────┐
         │ tracking_node│      │collision_handling│
         │ (Kalman +    │      │_node (/scan)     │
         │  DWA + avoid)│      └─────────────────┘
         └──────┬───────┘
                │/tracking/velocity_cmd
                ▼
         ┌──────────────┐
         │  /commands/  │ → Kobuki base
         │  velocity    │
         └──────────────┘
                │
         ┌──────┴───────┐
         │SLAM Toolbox  │  ← FASE 2
         │  /map /pose  │
         └──────┬───────┘
                │
         ┌──────┴───────┐
         │    Nav2      │  ← FASE 3
         │(planificador)│
         └──────────────┘
```

---

## Nodos ROS 2

| Nodo | Función | Topics entrada | Topics salida |
|---|---|---|---|
| `detection_node` | Detección por LiDAR (DBSCAN) + fusión cámara | `/scan`, `/person_detected_visual` | `/person_detected`, `/person_position` |
| `visual_detection_node` | Detección por cámara (MediaPipe) + gestos | `/image_raw` | `/person_detected_visual`, `/gesture_command` |
| `tracking_node` | Seguimiento con filtro Kalman + evasión obstáculos | `/person_position`, `/scan` | `/tracking/velocity_cmd` |
| `control_node` | FSM central de estados | `/person_detected`, `/gesture_command` | `/commands/velocity` |
| `user_interface_node` | Diagnóstico, RViz markers, HUD | múltiples status | `/visualization/*`, `/diagnostics` |
| `collision_handling_node` | Detección de colisión por LiDAR | `/scan` | `/collision_detected` |
| `slam_node` | SLAM básico propio (desactivado por defecto) | `/scan` | `/map` |

---

## Instalación y puesta en marcha

### Requisitos

```bash
# En el PC (Ubuntu 22.04 + ROS 2 Humble o Ubuntu 24.04 + ROS 2 Jazzy)
sudo apt install ros-$ROS_DISTRO-slam-toolbox ros-$ROS_DISTRO-nav2-bringup
pip install mediapipe
```

### Clonar y compilar

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/juanitomuro1999/TFM_JUAN.git person_follower
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash    # o humble
colcon build --symlink-install
source install/setup.bash
```

### Conexión al robot

```bash
# Red WiFi: conectar a PIROBOTNET6 o PIROBOTNET6_5G
ssh user@10.48.0.1   # contraseña: qwerty
```

### Lanzar el robot (en el NUC, con Terminator)

```bash
# Terminal 1 — Base Kobuki
source /opt/ros/jazzy/setup.bash && source ~/kobuki_ws/install/setup.bash
export ROS_DOMAIN_ID=24
ros2 launch kobuki_node kobuki_node-launch.py

# Terminal 2 — RPLIDAR
source /opt/ros/jazzy/setup.bash && source ~/kobuki_ws/install/setup.bash
export ROS_DOMAIN_ID=24
ros2 launch rplidar_ros rplidar_a2m8_launch.py serial_port:=/dev/rplidar

# Terminal 3 — TF estática lidar→base
source /opt/ros/jazzy/setup.bash && export ROS_DOMAIN_ID=24
ros2 run tf2_ros static_transform_publisher 0 0 0 3.141592 0 0 base_footprint laser

# Terminal 4 — Cámara
source /opt/ros/jazzy/setup.bash && export ROS_DOMAIN_ID=24
ros2 run usb_cam usb_cam_node_exe --ros-args -p image_width:=640 -p image_height:=480 -p framerate:=30.0

# Terminal 5 — SLAM Toolbox (Fase 2)
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=24
ros2 launch person_follower slam_toolbox.launch.py

# Terminal 6 — Sistema de seguimiento
source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash
export ROS_DOMAIN_ID=24
ros2 launch person_follower start_person_follower.launch.py
```

### O usando el script unificado

```bash
# Script en el robot
bash ~/ros2_ws/src/person_follower/scripts/launch_robot.bash {kobuki|lidar|tf|camera|slam|follower|status}
```

---

## Estado del desarrollo

| Fase | Período | Estado |
|---|---|---|
| Fase 1 – Base y definición | Hasta mayo 2026 | ✅ Completada |
| Fase 2 – Módulo de interacción + SLAM | Junio 2026 | 🔄 En curso |
| Fase 3 – Navegación autónoma (Nav2) | Julio 2026 | ⏳ Pendiente |
| Fase 4 – Validación experimental | Agosto 2026 | ⏳ Pendiente |
| Fase 5 – Cierre y defensa | Septiembre 2026 | ⏳ Pendiente |

---

## Estructura del repositorio

```
TFM_JUAN/
├── docs/                              # Documentación del TFM
│   ├── 01_introduccion.md
│   ├── 02_arquitectura.md
│   ├── 03_herramientas_ia.md
│   └── 04_diario_desarrollo.md
├── person_follower/
│   ├── collision_handling_node/
│   ├── control_node/
│   ├── detection_node/
│   ├── tracking_node/
│   ├── visual_detection_node/
│   ├── user_interface_node/
│   ├── SLAM_node/
│   ├── config/
│   │   ├── config.yaml
│   │   ├── slam_toolbox_params.yaml   # Fase 2
│   │   └── kobuki_params.yaml
│   └── launch/
│       ├── start_person_follower.launch.py
│       ├── slam_toolbox.launch.py     # Fase 2
│       └── bringup_full.launch.py    # Fase 2
├── scripts/
│   └── launch_robot.bash
├── rviz/
│   └── config.rviz
├── webots/                            # Simulación alternativa
├── package.xml
└── setup.py
```

---

## Uso del entorno Docker (laboratorio UJI)

```bash
# Descargar script del Aula Virtual y ejecutar
chmod +x run_ros2_jazzy.sh
./run_ros2_jazzy.sh
# Dentro del contenedor, abrir Terminator:
terminator &
```

---

## Uso de herramientas de inteligencia artificial

Ver [`docs/03_herramientas_ia.md`](docs/03_herramientas_ia.md) para la declaración detallada del uso de herramientas de IA en este proyecto.

---

## Licencia

Apache-2.0. Ver [`LICENSE`](LICENSE) y [`NOTICE`](NOTICE).
