#!/usr/bin/env python3
# Copyright 2026 Juan Muñoz Rovira
# SPDX-License-Identifier: Apache-2.0
#
# extract_casa_bags.py — Extrae a CSV lo necesario para analizar las tomas del
# gesto "casa" (sesión de lab 2026-09-23). Necesita ROS 2 (rosbag2_py); las
# gráficas se hacen después sin ROS con validation/plot_casa_session.py.
#
# Por cada bag genera en <out>/<nombre_bag>/:
#   pose_map.csv     t,x,y,yaw   pose del robot en el frame map (map→odom de
#                                 /tf compuesto con /odom)
#   state.csv        t,state     /control/state
#   gesture.csv      t,gesture   /gesture_command
#   person.csv       t,x,y       /person_position (frame robot, +x delante)
#   cmd.csv          t,vx,wz     /commands/velocity
#   nav_cmd.csv      t,vx,wz     /nav2/cmd_vel
#   track_cmd.csv    t,vx,wz     /tracking/velocity_cmd
#
# Uso: python3 validation/extract_casa_bags.py <dir_bags> <dir_salida>

import csv
import math
import os
import sys

import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


def yaw_of(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))


WANTED = {'/tf', '/odom', '/control/state', '/gesture_command', '/person_position',
          '/commands/velocity', '/nav2/cmd_vel', '/tracking/velocity_cmd'}


def extract(bag, out):
    r = rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=bag, storage_id=''),
           rosbag2_py.ConverterOptions('', ''))
    types = {t.name: t.type for t in r.get_all_topics_and_types()}
    os.makedirs(out, exist_ok=True)
    files = {k: open(os.path.join(out, k + '.csv'), 'w', newline='') for k in
             ('pose_map', 'state', 'gesture', 'person', 'cmd', 'nav_cmd', 'track_cmd')}
    w = {k: csv.writer(f) for k, f in files.items()}
    w['pose_map'].writerow(['t', 'x', 'y', 'yaw'])
    w['state'].writerow(['t', 'state'])
    w['gesture'].writerow(['t', 'gesture'])
    w['person'].writerow(['t', 'x', 'y'])
    for k in ('cmd', 'nav_cmd', 'track_cmd'):
        w[k].writerow(['t', 'vx', 'wz'])
    twist_topics = {'/commands/velocity': 'cmd', '/nav2/cmd_vel': 'nav_cmd',
                    '/tracking/velocity_cmd': 'track_cmd'}
    map_odom = None                    # (x, y, yaw)
    while r.has_next():
        topic, data, t_ns = r.read_next()
        t = t_ns * 1e-9
        if topic not in types or topic not in WANTED:
            continue
        msg = deserialize_message(data, get_message(types[topic]))
        if topic == '/tf':
            for tr in msg.transforms:
                if tr.header.frame_id == 'map' and tr.child_frame_id == 'odom':
                    q = tr.transform.rotation
                    map_odom = (tr.transform.translation.x, tr.transform.translation.y, yaw_of(q))
        elif topic == '/odom' and map_odom is not None:
            p = msg.pose.pose
            ox, oy, oyaw = p.position.x, p.position.y, yaw_of(p.orientation)
            mx, my, myaw = map_odom
            x = mx + math.cos(myaw) * ox - math.sin(myaw) * oy
            y = my + math.sin(myaw) * ox + math.cos(myaw) * oy
            w['pose_map'].writerow([f'{t:.3f}', f'{x:.4f}', f'{y:.4f}', f'{oyaw + myaw:.4f}'])
        elif topic == '/control/state':
            w['state'].writerow([f'{t:.3f}', msg.data])
        elif topic == '/gesture_command':
            w['gesture'].writerow([f'{t:.3f}', msg.data])
        elif topic == '/person_position':
            w['person'].writerow([f'{t:.3f}', f'{msg.x:.4f}', f'{msg.y:.4f}'])
        elif topic in twist_topics:
            w[twist_topics[topic]].writerow([f'{t:.3f}', f'{msg.linear.x:.4f}', f'{msg.angular.z:.4f}'])
    for f in files.values():
        f.close()


def main():
    src, dst = sys.argv[1], sys.argv[2]
    for name in sorted(os.listdir(src)):
        bag = os.path.join(src, name)
        if os.path.isdir(bag) and any(f.endswith(('.db3', '.mcap')) for f in os.listdir(bag)):
            print('extrayendo', name, flush=True)
            extract(bag, os.path.join(dst, name))


if __name__ == '__main__':
    main()
