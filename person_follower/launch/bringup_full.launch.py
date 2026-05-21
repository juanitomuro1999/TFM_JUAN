# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# Launch completo del sistema TFM en el robot (nuc-225).
# Lanza en un único comando: SLAM Toolbox + person_follower (todos los nodos).
# Los sensores (Kobuki, RPLIDAR, cámara, TF) deben lanzarse por separado
# usando scripts/launch_robot.bash o los launch scripts del kobuki_ws.
#
# Uso:
#   ros2 launch person_follower bringup_full.launch.py
#   ros2 launch person_follower bringup_full.launch.py slam_enabled:=false

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('person_follower')
    config_file = os.path.join(pkg_share, 'config', 'config.yaml')
    slam_launch = os.path.join(pkg_share, 'launch', 'slam_toolbox.launch.py')

    slam_enabled = LaunchConfiguration('slam_enabled', default='true')
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    return LaunchDescription([
        DeclareLaunchArgument('slam_enabled', default_value='true',
                              description='Lanzar SLAM Toolbox junto al sistema'),
        DeclareLaunchArgument('use_sim_time', default_value='false',
                              description='Reloj de simulación'),

        # ── SLAM Toolbox (opcional) ──────────────────────────────────────
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
            condition=IfCondition(slam_enabled),
        ),

        # ── Nodo de detección LiDAR ──────────────────────────────────────
        Node(
            package='person_follower',
            executable='detection_node',
            name='detection_node',
            output='screen',
            parameters=[config_file],
        ),

        # ── Nodo de detección visual (cámara + MediaPipe) ────────────────
        Node(
            package='person_follower',
            executable='visual_detection_node',
            name='visual_detection_node',
            output='screen',
            parameters=[config_file],
        ),

        # ── Nodo de seguimiento (Kalman + evasión) ───────────────────────
        Node(
            package='person_follower',
            executable='tracking_node',
            name='tracking_node',
            output='screen',
            parameters=[config_file],
        ),

        # ── Nodo de control (FSM) ────────────────────────────────────────
        Node(
            package='person_follower',
            executable='control_node',
            name='control_node',
            output='screen',
            parameters=[config_file],
            remappings=[('/cmd_vel', '/commands/velocity')],
        ),

        # ── Nodo de gestión de colisiones ────────────────────────────────
        Node(
            package='person_follower',
            executable='collision_handling_node',
            name='collision_handling_node',
            output='screen',
            parameters=[config_file],
        ),

        # ── Interfaz de usuario (RViz + marcadores) ──────────────────────
        Node(
            package='person_follower',
            executable='user_interface_node',
            name='user_interface_node',
            output='screen',
            parameters=[config_file],
        ),
    ])
