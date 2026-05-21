# Copyright 2026 omixxxer
# Author: omixxxer
# SPDX-License-Identifier: Apache-2.0

from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'person_follower'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('person_follower/launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('person_follower/config/*.yaml')),
        (os.path.join('share', package_name, 'config'), glob('person_follower/config/*.rviz')),
        (os.path.join('share', package_name, 'rviz'), glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Juan Muriel Rovira',
    maintainer_email='juanitomuro1999@gmail.com',
    description='TFM: Person-following and autonomous navigation system for TurtleBot2/Kobuki (ROS 2)',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'control_node = person_follower.control_node.control_node:main',
            'visual_detection_node = person_follower.visual_detection_node.visual_detection_node:main',
            'detection_node = person_follower.detection_node.detection_node:main',
            'tracking_node = person_follower.tracking_node.tracking_node:main',
            'user_interface_node = person_follower.user_interface_node.user_interface_node:main',
            'collision_handling_node = person_follower.collision_handling_node.collision_handling_node:main',
            'slam_node = person_follower.SLAM_node.SLAM_node:main',
        ],
    },
)
