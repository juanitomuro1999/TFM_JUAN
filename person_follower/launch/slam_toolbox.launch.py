# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# Launch: SLAM Toolbox online_async para TurtleBot2/Kobuki — ROS 2 Jazzy (slam_toolbox 2.8.x)
# Requisito: /scan, /odom, TF base_footprint->laser activos antes de lanzar.
#
# NOTA: async_slam_toolbox_node es un lifecycle node. El LifecycleManager lo
# configura y activa automáticamente (autostart: true) para que /map se publique
# sin intervención manual.

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('person_follower')
    slam_params_file = os.path.join(pkg_share, 'config', 'slam_toolbox_params.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Usar reloj de simulación'
        ),

        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[
                slam_params_file,
                {'use_sim_time': use_sim_time}
            ],
        ),

        # Lifecycle manager: configura y activa slam_toolbox automáticamente.
        # bond_timeout=0 deshabilita el heartbeat (slam_toolbox no lo implementa).
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_slam',
            output='screen',
            parameters=[
                {'use_sim_time': use_sim_time},
                {'autostart': True},
                {'node_names': ['slam_toolbox']},
                {'bond_timeout': 0.0},
            ],
        ),
    ])
