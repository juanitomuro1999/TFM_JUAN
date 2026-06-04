#!/bin/bash
NUC="user@10.48.0.1"
SRC="/home/usuario/ros2_ws/src/TFM_JUAN/person_follower"
DST="/home/user/ros2_ws/src/person_follower/person_follower"

scp "$SRC/tracking_node/tracking_node.py" "$NUC:$DST/tracking_node/tracking_node.py"
scp "$SRC/detection_node/detection_node.py" "$NUC:$DST/detection_node/detection_node.py"
scp "$SRC/config/config.yaml" "$NUC:$DST/config/config.yaml"
scp "$SRC/config/config.yaml" "$NUC:/home/user/ros2_ws/src/person_follower/config/config.yaml"

echo "Sync completado."
