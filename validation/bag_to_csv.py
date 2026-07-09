#!/usr/bin/env python3
# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# bag_to_csv.py — Extrae un rosbag2 de validación a CSV/TUM para análisis.
#
#   Lee el bag con la API de rosbag2_py (requiere entorno ROS 2 sourceado, pero
#   NO necesita internet → se puede ejecutar en el propio NUC). Solo usa stdlib
#   (json, csv) además de ROS, así que no depende de pandas/matplotlib.
#
#   Genera, dentro del bag o en --out:
#     telemetry.csv   columnas de /follower/telemetry (dist, angulo, vel, Kalman)
#     odom.csv        pose y velocidad de /odom (frame odom)
#     odom.tum        trayectoria en formato TUM (para evo)
#     cmd_vel.csv     /commands/velocity (comando real a la base)
#     detection.csv   /person_detected y /control/mode (perdidas / FSM)
#     position.csv    /person_position (posicion cruda observada, frame robot)
#     expected_position.csv  /expected_person_position (salida del Kalman)
#
# Uso:
#   python3 bag_to_csv.py <ruta_al_bag> [--out DIR] [--storage mcap|sqlite3]
#
# Luego, en el portatil con matplotlib:
#   python3 validation/plot_run.py <DIR>

import argparse
import csv
import json
import os
import sys

try:
    from rosbag2_py import SequentialReader, StorageOptions, ConverterOptions
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
except ImportError as e:
    sys.exit(
        f"[error] No se pudo importar la API de rosbag2/rclpy: {e}\n"
        "        Sourcea el entorno ROS 2 antes de ejecutar:\n"
        "          source /opt/ros/jazzy/setup.bash && source ~/ros2_ws/install/setup.bash"
    )


def stamp_to_s(stamp) -> float:
    """Convierte un builtin_interfaces/Time a segundos float."""
    return stamp.sec + stamp.nanosec * 1e-9


def open_reader(path: str, storage_id: str) -> SequentialReader:
    reader = SequentialReader()
    # storage_id vacio => autodeteccion (rosbag2 reciente). Si falla, reintenta
    # con los formatos habituales.
    for sid in ([storage_id] if storage_id else ['', 'mcap', 'sqlite3']):
        try:
            reader = SequentialReader()
            reader.open(
                StorageOptions(uri=path, storage_id=sid),
                ConverterOptions(input_serialization_format='cdr',
                                 output_serialization_format='cdr'),
            )
            return reader
        except Exception:
            continue
    raise RuntimeError(f"No se pudo abrir el bag '{path}' con storage mcap/sqlite3.")


def main():
    ap = argparse.ArgumentParser(description="rosbag2 -> CSV/TUM para validacion TFM")
    ap.add_argument('bag', help="carpeta del bag (la que contiene metadata.yaml)")
    ap.add_argument('--out', default=None, help="carpeta de salida (def: dentro del bag)")
    ap.add_argument('--storage', default='', help="mcap | sqlite3 (def: autodetectar)")
    args = ap.parse_args()

    bag_path = os.path.abspath(args.bag)
    if not os.path.isdir(bag_path):
        sys.exit(f"[error] No existe la carpeta del bag: {bag_path}")

    out_dir = os.path.abspath(args.out) if args.out else os.path.join(bag_path, 'analysis')
    os.makedirs(out_dir, exist_ok=True)

    reader = open_reader(bag_path, args.storage)
    type_map = {t.name: t.type for t in reader.get_all_topics_and_types()}

    # ── Acumuladores por topic ───────────────────────────────────────────────
    telem_rows, odom_rows, tum_rows, cmd_rows, det_rows = [], [], [], [], []
    gesture_rows, fsm_rows = [], []
    pos_rows, exp_pos_rows = [], []
    # Claves de telemetria en orden (ver tracking_node._publish_telemetry)
    TELEM_KEYS = ['t', 'dist', 'angle_deg', 'vlin', 'vang', 'lin_factor',
                  'obs_age', 'kf_vx', 'kf_vy', 'kf_ax', 'kf_ay']

    counts = {}
    while reader.has_next():
        topic, data, t_ns = reader.read_next()
        counts[topic] = counts.get(topic, 0) + 1
        t_bag = t_ns * 1e-9  # tiempo de recepcion del bag (s)

        if topic == '/follower/telemetry':
            try:
                d = json.loads(deserialize_message(data, get_message('std_msgs/msg/String')).data)
            except (json.JSONDecodeError, AttributeError):
                continue
            telem_rows.append([d.get(k, '') for k in TELEM_KEYS] + [round(t_bag, 6)])

        elif topic == '/odom':
            m = deserialize_message(data, get_message('nav_msgs/msg/Odometry'))
            p, o = m.pose.pose.position, m.pose.pose.orientation
            v = m.twist.twist
            ts = stamp_to_s(m.header.stamp)
            odom_rows.append([round(ts, 6), p.x, p.y, p.z,
                              v.linear.x, v.angular.z])
            # TUM: timestamp tx ty tz qx qy qz qw
            tum_rows.append([f"{ts:.6f}", p.x, p.y, p.z, o.x, o.y, o.z, o.w])

        elif topic == '/commands/velocity':
            m = deserialize_message(data, get_message('geometry_msgs/msg/Twist'))
            cmd_rows.append([round(t_bag, 6), m.linear.x, m.angular.z])

        elif topic == '/person_detected':
            m = deserialize_message(data, get_message('std_msgs/msg/Bool'))
            det_rows.append([round(t_bag, 6), 'detected', int(m.data)])

        elif topic == '/control/mode':
            m = deserialize_message(data, get_message('std_msgs/msg/String'))
            det_rows.append([round(t_bag, 6), 'mode', m.data])

        elif topic == '/person_position':
            m = deserialize_message(data, get_message('geometry_msgs/msg/Point'))
            pos_rows.append([round(t_bag, 6), m.x, m.y])

        elif topic == '/expected_person_position':
            m = deserialize_message(data, get_message('geometry_msgs/msg/Point'))
            exp_pos_rows.append([round(t_bag, 6), m.x, m.y])

        elif topic == '/gesture_command':
            m = deserialize_message(data, get_message('std_msgs/msg/String'))
            gesture_rows.append([round(t_bag, 6), m.data])

        elif topic == '/control/state':
            m = deserialize_message(data, get_message('std_msgs/msg/String'))
            fsm_rows.append([round(t_bag, 6), m.data])

    # ── Escritura ─────────────────────────────────────────────────────────────
    def write_csv(name, header, rows):
        path = os.path.join(out_dir, name)
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        return path, len(rows)

    written = []
    written.append(write_csv('telemetry.csv', TELEM_KEYS + ['t_bag'], telem_rows))
    written.append(write_csv('odom.csv',
                             ['t', 'x', 'y', 'z', 'v_lin', 'v_ang'], odom_rows))
    written.append(write_csv('cmd_vel.csv', ['t_bag', 'v_lin', 'v_ang'], cmd_rows))
    written.append(write_csv('detection.csv', ['t_bag', 'kind', 'value'], det_rows))
    written.append(write_csv('gestures.csv', ['t_bag', 'gesture'], gesture_rows))
    written.append(write_csv('fsm_states.csv', ['t_bag', 'state'], fsm_rows))
    written.append(write_csv('position.csv', ['t_bag', 'x', 'y'], pos_rows))
    written.append(write_csv('expected_position.csv', ['t_bag', 'x', 'y'], exp_pos_rows))

    # TUM como texto separado por espacios (formato que espera evo)
    tum_path = os.path.join(out_dir, 'odom.tum')
    with open(tum_path, 'w') as f:
        for row in tum_rows:
            f.write(' '.join(str(x) for x in row) + '\n')
    written.append((tum_path, len(tum_rows)))

    # ── Resumen ─────────────────────────────────────────────────────────────
    print(f"[ok] Mensajes leidos por topic:")
    for tp in sorted(counts):
        print(f"       {counts[tp]:>7}  {tp}")
    print(f"[ok] Archivos generados en {out_dir}:")
    for path, n in written:
        print(f"       {n:>7} filas  {os.path.basename(path)}")
    print("\nSiguiente paso (portatil con matplotlib):")
    print(f"  python3 validation/plot_run.py {out_dir}")
    print("evo (trayectoria):")
    print(f"  evo_traj tum {tum_path} -p --plot_mode xy")


if __name__ == '__main__':
    main()
