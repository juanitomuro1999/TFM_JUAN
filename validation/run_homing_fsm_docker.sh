#!/bin/bash
# Ejecuta validation/verify_homing_fsm.py dentro de ROS 2 Jazzy (Docker), para
# máquinas sin ROS instalado. Uso, desde la raíz del repo:
#   bash validation/run_homing_fsm_docker.sh
set -e
docker run --rm -v "$(cd "$(dirname "$0")/.." && pwd)":/repo -w /repo ros:jazzy-ros-base \
  bash -c "apt-get update -qq >/dev/null && \
           apt-get install -y -qq ros-jazzy-nav2-msgs >/dev/null && \
           source /opt/ros/jazzy/setup.bash && \
           python3 validation/verify_homing_fsm.py"
