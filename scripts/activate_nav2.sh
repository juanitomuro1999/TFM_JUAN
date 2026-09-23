#!/bin/bash
# Activa la pila de navegación de Nav2 cuando bringup_home.launch.py (o
# nav2_localization_demo.launch.py con launch_navigation:=true) se lanzó
# ANTES de dar la pose inicial a AMCL.
#
# Sin pose inicial no existe la TF map→base_footprint, planner_server no
# puede activar su global_costmap y lifecycle_manager_navigation aborta el
# arranque a los 60 s (visto en el lab 2026-09-23). "manage_nodes STARTUP"
# tampoco sirve después, porque intenta reconfigurar controller_server, que
# ya está activo. Este script activa uno a uno los nodos que se quedaron
# inactivos.
#
# Uso (en el NUC, tras "2D Pose Estimate" en RViz):
#   bash scripts/activate_nav2.sh
source /opt/ros/jazzy/setup.bash
export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-24}

for n in controller_server planner_server behavior_server bt_navigator; do
  state=$(timeout 15 ros2 lifecycle get /$n 2>/dev/null | awk '{print $1}')
  case "$state" in
    active)   echo "$n: ya activo" ;;
    inactive) echo -n "$n: activando... "; timeout 60 ros2 lifecycle set /$n activate | tail -1 ;;
    unconfigured)
      echo -n "$n: configurando... "; timeout 60 ros2 lifecycle set /$n configure | tail -1
      echo -n "$n: activando... ";    timeout 60 ros2 lifecycle set /$n activate  | tail -1 ;;
    *) echo "$n: estado desconocido ('$state') — ¿está lanzado Nav2?" ;;
  esac
done
timeout 15 ros2 action list | grep -q navigate_to_pose && echo "OK: /navigate_to_pose disponible"
