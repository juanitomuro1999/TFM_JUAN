#!/bin/bash
# Ejecuta validation/verify_reacquire_sector.py con ROS 2 Jazzy (Docker).
# Uso, desde la raíz del repo: bash validation/run_reacquire_docker.sh
set -e
docker run --rm -v "$(cd "$(dirname "$0")/.." && pwd)":/repo -w /repo ros:jazzy-ros-base \
  bash -c "apt-get update -qq >/dev/null && \
           apt-get install -y -qq python3-scipy python3-sklearn >/dev/null && \
           source /opt/ros/jazzy/setup.bash && \
           python3 validation/verify_reacquire_sector.py"
