#!/bin/bash
# Script de lanzamiento completo del robot TFM — TurtleBot2/Kobuki
# Ejecutar en el NUC del robot (ssh user@10.48.0.1)
# ROS 2 Jazzy | ROS_DOMAIN_ID=25

set -e

SOURCE_ROS="/opt/ros/jazzy/setup.bash"
KOBUKI_WS="$HOME/kobuki_ws/install/setup.bash"
ROS2_WS="$HOME/ros2_ws/install/setup.bash"

source "$SOURCE_ROS"
source "$KOBUKI_WS"
source "$ROS2_WS"
export ROS_DOMAIN_ID=25

STEP=$1

case "$STEP" in
  kobuki)
    echo "[1/5] Lanzando base Kobuki en /dev/kobuki..."
    ros2 launch kobuki_node kobuki_node-launch.py
    ;;
  lidar)
    echo "[2/5] Lanzando RPLIDAR en /dev/rplidar..."
    ros2 launch rplidar_ros rplidar_a2m8_launch.py serial_port:=/dev/rplidar
    ;;
  tf)
    echo "[3/5] Publicando TF estática base_footprint -> laser..."
    ros2 run tf2_ros static_transform_publisher 0 0 0 3.141592 0 0 base_footprint laser
    ;;
  camera)
    echo "[4/6] Lanzando cámara USB (Logitech C270)..."
    ros2 run usb_cam usb_cam_node_exe --ros-args \
      --param image_width:=640 \
      --param image_height:=480 \
      --param framerate:=30.0 \
      --param pixel_format:="mjpeg2rgb"
    ;;
  slam)
    echo "[5/6] Lanzando SLAM Toolbox (online async)..."
    ros2 launch person_follower slam_toolbox.launch.py
    ;;
  follower)
    echo "[6/6] Lanzando sistema person_follower completo..."
    ros2 launch person_follower bringup_full.launch.py slam_enabled:=false
    ;;
  full)
    echo "[ALL] Lanzando sistema completo (SLAM + person_follower)..."
    ros2 launch person_follower bringup_full.launch.py
    ;;
  save_map)
    echo "Guardando mapa actual..."
    ros2 run nav2_map_server map_saver_cli -f ~/maps/mapa_laboratorio
    ;;
  status)
    echo "=== Nodos activos ==="
    ros2 node list
    echo ""
    echo "=== Topics activos ==="
    ros2 topic list
    echo ""
    echo "=== /scan Hz ==="
    timeout 5 ros2 topic hz /scan 2>/dev/null || echo "Sin datos en /scan"
    echo ""
    echo "=== /odom Hz ==="
    timeout 5 ros2 topic hz /odom 2>/dev/null || echo "Sin datos en /odom"
    ;;
  *)
    echo "Uso: $0 {kobuki|lidar|tf|camera|slam|follower|full|save_map|status}"
    echo ""
    echo "Orden recomendado (una terminal por paso):"
    echo "  Terminal 1: $0 kobuki"
    echo "  Terminal 2: $0 lidar"
    echo "  Terminal 3: $0 tf"
    echo "  Terminal 4: $0 camera"
    echo "  Terminal 5: $0 slam        (Fase 2: SLAM Toolbox)"
    echo "  Terminal 6: $0 follower    (person_follower sin SLAM)"
    echo "  -- o --"
    echo "  Terminal 5: $0 full        (SLAM + follower en uno)"
    echo "  Terminal X: $0 save_map    (guardar mapa al terminar)"
    echo "  Terminal X: $0 status      (diagnóstico)"
    ;;
esac
