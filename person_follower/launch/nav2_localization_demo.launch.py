# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# Launch: demo minima de Nav2 (objetivo especifico 3 del TFM) — AMCL sobre
# el mapa guardado + pila de navegacion (planner/controller/BT) para mandar
# UN objetivo predefinido con scripts/nav2_send_goal.py.
#
#   ⚠️  ANDAMIAJE ESCRITO SIN ACCESO AL ROBOT (2026-07-09), NUNCA EJECUTADO.
#       Usa person_follower/config/nav2_params.yaml, que tiene el mismo aviso
#       (los strings de plugin cambian entre distros de ROS 2 — verificar
#       contra la version de nav2 instalada en el NUC antes de fiarse).
#
#   RECOMENDADO PARA LA PRIMERA PRUEBA: comentar el bloque "NAVEGACION" de
#   abajo y lanzar solo "LOCALIZACION" primero. Confirmar en RViz que la
#   pose de AMCL se estabiliza sobre el mapa (pose inicial aproximada con
#   "2D Pose Estimate") antes de anadir la pila de navegacion completa.
#
#   El cmd_vel final de controller_server se remapea DIRECTAMENTE a
#   /commands/velocity (igual que el resto del stack) — SIN velocity_smoother
#   (esta configurado en nav2_params.yaml pero se deja fuera de este demo
#   minimo a proposito, para reducir piezas moviles sin probar; anadirlo
#   despues si el bringup basico funciona bien).
#
#   Corre INDEPENDIENTE de person_follower (control_node/tracking_node) — no
#   hay integracion "seguir a la persona -> navegar a destino" todavia, eso
#   es el objetivo especifico 5, fuera de alcance de este demo. No lanzar
#   este launch a la vez que start_person_follower.launch.py: ambos
#   publicarian en /commands/velocity y se pisarian.

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('person_follower')
    nav2_params_default = os.path.join(pkg_share, 'config', 'nav2_params.yaml')
    map_yaml_default = os.path.join(pkg_share, 'maps', 'mapa_laboratorio.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    map_yaml = LaunchConfiguration('map', default=map_yaml_default)
    params_file = LaunchConfiguration('params_file', default=nav2_params_default)
    launch_navigation = LaunchConfiguration('launch_navigation', default='false')

    lifecycle_nodes_localization = ['map_server', 'amcl']
    lifecycle_nodes_navigation = [
        'controller_server', 'planner_server', 'behavior_server', 'bt_navigator'
    ]

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Usar reloj de simulación'),
        DeclareLaunchArgument(
            'map', default_value=map_yaml_default,
            description='Ruta al .yaml del mapa guardado'),
        DeclareLaunchArgument(
            'params_file', default_value=nav2_params_default,
            description='Ruta a nav2_params.yaml'),
        DeclareLaunchArgument(
            'launch_navigation', default_value='false',
            description='Si es "true", además de localización lanza planner/'
                        'controller/BT (Sesión 7 — fase B). Por defecto solo '
                        'localización (Sesión 6 — fase A).'),

        # ── LOCALIZACION: map_server + AMCL ──────────────────────────────
        Node(
            package='nav2_map_server',
            executable='map_server',
            name='map_server',
            output='screen',
            parameters=[params_file, {
                'use_sim_time': use_sim_time,
                'yaml_filename': map_yaml,
            }],
        ),
        Node(
            package='nav2_amcl',
            executable='amcl',
            name='amcl',
            output='screen',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_localization',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': True,
                'node_names': lifecycle_nodes_localization,
                'bond_timeout': 0.0,
            }],
        ),

        # ── NAVEGACION: planificador + controlador + comportamientos + BT ──
        # Solo si launch_navigation:=true (Sesión 7 — fase B). Por defecto
        # apagado: la Sesión 6 valida únicamente el bloque de localización.
        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
            remappings=[('cmd_vel', '/commands/velocity')],
            condition=IfCondition(launch_navigation),
        ),
        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
            condition=IfCondition(launch_navigation),
        ),
        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output='screen',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
            condition=IfCondition(launch_navigation),
        ),
        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
            condition=IfCondition(launch_navigation),
        ),
        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': True,
                'node_names': lifecycle_nodes_navigation,
                'bond_timeout': 0.0,
            }],
            condition=IfCondition(launch_navigation),
        ),
    ])
