# Copyright 2026 Juan Muñoz Rovira
# SPDX-License-Identifier: Apache-2.0
#
# Launch: seguimiento de persona + Nav2 a la vez, para el gesto "casa"
# (go_home, tejado → estado HOMING de control_node).
#
#   - start_person_follower.launch.py tal cual (5 nodos del seguimiento).
#   - nav2_localization_demo.launch.py con launch_navigation:=true y el
#     cmd_vel de Nav2 remapeado a /nav2/cmd_vel. Nav2 NUNCA publica directo
#     en /commands/velocity: control_node lo reenvía solo en HOMING, igual
#     que /tracking/velocity_cmd solo en TRACKING.
#   - TF estática base_footprint→laser (Sesión 6: sin ella AMCL descarta
#     todos los /scan). Desactivable con static_tf:=false si ya se lanzó a
#     mano o con scripts/launch_robot.bash tf.
#
# Requisitos previos (igual que siempre): kobuki y rplidar en marcha. Tras
# lanzar: "2D Pose Estimate" en RViz (Fixed Frame = map) y confirmar que AMCL
# converge ANTES de usar el gesto casa.
#
# Uso: ros2 launch person_follower bringup_home.launch.py

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    launch_dir = os.path.join(
        get_package_share_directory('person_follower'), 'launch')
    static_tf = LaunchConfiguration('static_tf')

    return LaunchDescription([
        DeclareLaunchArgument(
            'static_tf', default_value='true',
            description='Lanzar la TF estática base_footprint→laser'),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='laser_static_tf',
            arguments=['--x', '0', '--y', '0', '--z', '0',
                       '--yaw', '3.141592', '--pitch', '0', '--roll', '0',
                       '--frame-id', 'base_footprint',
                       '--child-frame-id', 'laser'],
            condition=IfCondition(static_tf),
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'start_person_follower.launch.py')),
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(launch_dir, 'nav2_localization_demo.launch.py')),
            launch_arguments={
                'launch_navigation': 'true',
                'cmd_vel_topic': '/nav2/cmd_vel',
            }.items(),
        ),
    ])
