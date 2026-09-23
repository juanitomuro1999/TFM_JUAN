#!/bin/bash
NUC="user@10.48.0.1"
SRC="$(cd "$(dirname "$0")" && pwd)"
DST="/home/user/ros2_ws/src/person_follower"

scp "$SRC/person_follower/tracking_node/tracking_node.py" "$NUC:$DST/person_follower/tracking_node/tracking_node.py"
scp "$SRC/person_follower/detection_node/detection_node.py" "$NUC:$DST/person_follower/detection_node/detection_node.py"
scp "$SRC/person_follower/config/config.yaml" "$NUC:$DST/person_follower/config/config.yaml"
# Gesto "casa" (2026-09)
scp "$SRC/person_follower/control_node/control_node.py" "$NUC:$DST/person_follower/control_node/control_node.py"
scp "$SRC/person_follower/visual_detection_node/visual_detection_node.py" \
    "$SRC/person_follower/visual_detection_node/gestures.py" "$NUC:$DST/person_follower/visual_detection_node/"
scp "$SRC/person_follower/launch/bringup_home.launch.py" \
    "$SRC/person_follower/launch/nav2_localization_demo.launch.py" "$NUC:$DST/person_follower/launch/"
scp "$SRC/scripts/print_home_pose.py" "$SRC/scripts/activate_nav2.sh" "$SRC/scripts/launch_robot.bash" "$NUC:$DST/scripts/"
scp "$SRC/package.xml" "$NUC:$DST/package.xml"

echo "Sync completado."
echo "Launch nuevo (bringup_home.launch.py): hace falta 'colcon build --symlink-install' una vez en el NUC para registrarlo."
