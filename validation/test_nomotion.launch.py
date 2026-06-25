# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# test_nomotion.launch.py — Lanza el stack seguidor IGUAL que
#   start_person_follower.launch.py PERO redirige la salida de velocidad del
#   control_node (/cmd_vel) a un topic muerto (/cmd_vel_inhibited) en lugar de
#   /commands/velocity. Resultado: todos los nodos funcionan, se detectan gestos,
#   la FSM transiciona y se publica /control/state, pero la base NUNCA recibe
#   ordenes de motor → el robot NO se mueve. /odom sigue publicandose.
#
#   Uso (en el NUC, con sensores ya lanzados):
#     ros2 launch /home/user/ros2_ws/src/person_follower/validation/test_nomotion.launch.py
#   o por ruta directa a este archivo.
#
#   Solo para la validacion de logging (gestos + FSM) sin riesgo de movimiento.

from launch import LaunchDescription
from launch_ros.actions import Node
import os
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    package_share_directory = get_package_share_directory('person_follower')
    config_path = os.path.join(package_share_directory, 'config', 'config.yaml')

    return LaunchDescription([
        Node(
            package='person_follower',
            executable='control_node',
            name='control_node',
            output='screen',
            parameters=[config_path],
            # ⚠️ INHIBIDO: la velocidad NO va a la base, va a un topic sin suscriptor.
            remappings=[('/cmd_vel', '/cmd_vel_inhibited')]
        ),
        Node(
            package='person_follower',
            executable='tracking_node',
            name='tracking_node',
            output='screen',
            parameters=[config_path],
            remappings=[('/cmd_vel', '/cmd_vel_inhibited')]
        ),
        Node(
            package='person_follower',
            executable='visual_detection_node',
            name='visual_detection_node',
            output='screen',
            parameters=[config_path]
        ),
        Node(
            package='person_follower',
            executable='detection_node',
            name='detection_node',
            output='screen',
            parameters=[config_path]
        ),
        Node(
            package='person_follower',
            executable='user_interface_node',
            name='user_interface_node',
            output='screen',
            parameters=[config_path]
        )
    ])
