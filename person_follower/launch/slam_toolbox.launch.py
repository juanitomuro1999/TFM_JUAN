# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# Launch: SLAM Toolbox en modo online_async para TurtleBot2/Kobuki
# Requisito: /scan y /odom publicándose, TF base_footprint->laser activa
#
# Uso:
#   ros2 launch person_follower slam_toolbox.launch.py
#   ros2 launch person_follower slam_toolbox.launch.py mode:=localization

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
    slam_params = LaunchConfiguration('slam_params_file', default=slam_params_file)

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Usar reloj de simulación (true para Gazebo/Webots)'
        ),
        DeclareLaunchArgument(
            'slam_params_file',
            default_value=slam_params_file,
            description='Ruta al archivo de parámetros de SLAM Toolbox'
        ),

        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox',
            output='screen',
            parameters=[slam_params, {'use_sim_time': use_sim_time}],
            remappings=[
                ('/scan', '/scan'),
            ]
        ),
    ])
