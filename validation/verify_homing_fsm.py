#!/usr/bin/env python3
# Copyright 2026 Juan Muñoz Rovira
# SPDX-License-Identifier: Apache-2.0
#
# verify_homing_fsm.py — Prueba de integración del estado HOMING de
# control_node (gesto "casa") SIN robot: el control_node real corre como
# proceso aparte y este script hace de todo lo demás.
#
#   - Falso tracking_node: servicio enable_tracking + Twist() a cero a 10 Hz
#     en /tracking/velocity_cmd (igual que el real cuando está desactivado).
#   - Falso Nav2: servidor de la acción navigate_to_pose que publica
#     vx=0.15 en /nav2/cmd_vel mientras "navega". Su comportamiento se elige
#     por caso: succeed / abort / reject / hang (hasta cancelación).
#   - Publica /gesture_command y /person_detected, y observa /control/state
#     y /commands/velocity.
#
# Uso (necesita ROS 2 Jazzy + nav2_msgs; en el portátil sin ROS, con Docker):
#   bash validation/run_homing_fsm_docker.sh
# o en una máquina con ROS:
#   python3 validation/verify_homing_fsm.py

import os
import subprocess
import sys
import threading
import time

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav2_msgs.action import NavigateToPose
from std_msgs.msg import Bool, String
from std_srvs.srv import SetBool

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')


class Harness(Node):
    def __init__(self):
        super().__init__('homing_harness')
        cb = ReentrantCallbackGroup()
        self.mode = 'succeed'
        self.goals = []           # (x, y) recibidos por el falso Nav2
        self.cancels = 0
        self.states = []
        self.cmds = []            # (t, vx) en /commands/velocity
        self.tracking_enabled = []

        self.create_service(SetBool, 'enable_tracking', self._on_enable, callback_group=cb)
        self.track_pub = self.create_publisher(Twist, '/tracking/velocity_cmd', 10)
        self.create_timer(0.1, lambda: self.track_pub.publish(Twist()), callback_group=cb)

        self.nav_pub = self.create_publisher(Twist, '/nav2/cmd_vel', 10)
        ActionServer(self, NavigateToPose, 'navigate_to_pose', self._execute,
                     goal_callback=self._goal_cb, cancel_callback=self._cancel_cb,
                     callback_group=cb)

        self.gesture_pub = self.create_publisher(String, '/gesture_command', 10)
        self.detected_pub = self.create_publisher(Bool, '/person_detected', 10)
        self.create_subscription(String, '/control/state',
                                 lambda m: self.states.append(m.data), 10, callback_group=cb)
        self.create_subscription(Twist, '/commands/velocity',
                                 lambda m: self.cmds.append((time.monotonic(), m.linear.x)),
                                 10, callback_group=cb)

    def _on_enable(self, req, resp):
        self.tracking_enabled.append(req.data)
        resp.success = True
        return resp

    def _goal_cb(self, goal):
        self.goals.append((goal.pose.pose.position.x, goal.pose.pose.position.y))
        return GoalResponse.REJECT if self.mode == 'reject' else GoalResponse.ACCEPT

    def _cancel_cb(self, _):
        self.cancels += 1
        return CancelResponse.ACCEPT

    def _execute(self, gh):
        dur = 30.0 if self.mode == 'hang' else 2.0
        t0 = time.monotonic()
        cmd = Twist()
        cmd.linear.x = 0.15
        while time.monotonic() - t0 < dur:
            if gh.is_cancel_requested:
                gh.canceled()
                return NavigateToPose.Result()
            self.nav_pub.publish(cmd)
            time.sleep(0.05)
        if self.mode == 'abort':
            gh.abort()
        else:
            gh.succeed()
        return NavigateToPose.Result()

    # helpers
    def gesture(self, g):
        self.gesture_pub.publish(String(data=g))

    def detected(self, v):
        self.detected_pub.publish(Bool(data=v))

    def state(self):
        return self.states[-1] if self.states else None


def wait_for(pred, timeout):
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        if pred():
            return True
        time.sleep(0.05)
    return False


def main():
    rclpy.init()
    h = Harness()
    ex = MultiThreadedExecutor(num_threads=4)
    ex.add_node(h)
    threading.Thread(target=ex.spin, daemon=True).start()

    env = dict(os.environ, PYTHONPATH=REPO + os.pathsep + os.environ.get('PYTHONPATH', ''))
    ctrl = subprocess.Popen(
        [sys.executable, '-m', 'person_follower.control_node.control_node', '--ros-args',
         '--params-file', os.path.join(REPO, 'person_follower/config/config.yaml'),
         '-p', 'home_x:=1.5', '-p', 'home_y:=-2.0',
         '-r', '/cmd_vel:=/commands/velocity'],
        env=env, stdin=subprocess.DEVNULL)

    results = []

    def check(name, cond):
        results.append((name, bool(cond)))
        print(f"[{'OK ' if cond else 'FALLO'}] {name}", flush=True)

    try:
        check("control_node arranca en IDLE", wait_for(lambda: h.state() == 'IDLE', 20))
        time.sleep(3.0)   # descubrimiento DDS del action client

        # ── 1. IDLE → casa → llega → IDLE, sin volver a seguir solo ──────────
        h.mode = 'succeed'
        h.gesture('go_home')
        check("1. go_home desde IDLE → HOMING", wait_for(lambda: h.state() == 'HOMING', 3))
        check("1. objetivo con la pose de config (1.5, -2.0)",
              wait_for(lambda: h.goals and h.goals[-1] == (1.5, -2.0), 3))
        t_mid = time.monotonic()
        time.sleep(1.0)
        window = [vx for t, vx in h.cmds if t_mid <= t <= t_mid + 1.0]
        check(f"1. en HOMING solo llega la velocidad de Nav2 "
              f"({len(window)} msgs, ceros={sum(v == 0.0 for v in window)})",
              window and all(v == 0.15 for v in window))
        h.gesture('go_home')   # repetido (tejado mantenido) → ignorado
        check("1. llega a casa → IDLE", wait_for(lambda: h.state() == 'IDLE', 5))
        check("1. go_home repetido no lanza un segundo objetivo", len(h.goals) == 1)
        for _ in range(5):
            h.detected(True)
            time.sleep(0.1)
        check("1. persona delante tras llegar: sigue en IDLE (hace falta gesto)",
              h.state() == 'IDLE')

        # ── 2. TRACKING → casa → mano izquierda cancela ─────────────────────
        h.mode = 'hang'
        h.gesture('start_tracking')
        h.detected(True)
        check("2. start_tracking → TRACKING", wait_for(lambda: h.state() == 'TRACKING', 3))
        h.gesture('go_home')
        check("2. go_home desde TRACKING → HOMING", wait_for(lambda: h.state() == 'HOMING', 3))
        check("2. tracking_node desactivado al entrar en HOMING",
              wait_for(lambda: h.tracking_enabled[-1] is False, 2))
        time.sleep(1.0)
        h.gesture('stop_tracking')
        check("2. stop_tracking en HOMING → IDLE", wait_for(lambda: h.state() == 'IDLE', 3))
        check("2. objetivo de Nav2 cancelado", wait_for(lambda: h.cancels >= 1, 3))
        time.sleep(0.5)
        t_after = time.monotonic()
        time.sleep(1.0)
        check("2. tras cancelar no se reenvía nada de Nav2",
              all(vx == 0.0 for t, vx in h.cmds if t >= t_after))

        # ── 3. Nav2 aborta (p. ej. sin ruta) → IDLE ─────────────────────────
        h.mode = 'abort'
        h.gesture('go_home')
        check("3. go_home → HOMING", wait_for(lambda: h.state() == 'HOMING', 3))
        check("3. Nav2 aborta → IDLE", wait_for(lambda: h.state() == 'IDLE', 5))

        # ── 4. Nav2 rechaza el objetivo → IDLE ──────────────────────────────
        time.sleep(2.1)   # sin cooldown en control_node, pero separar casos
        h.mode = 'reject'
        n = len(h.states)
        h.gesture('go_home')
        check("4. objetivo rechazado → HOMING → IDLE",
              wait_for(lambda: h.states[n:] == ['HOMING', 'IDLE'], 3))
    finally:
        ctrl.terminate()
        try:
            ctrl.wait(5)
        except subprocess.TimeoutExpired:
            ctrl.kill()

    # ── 5. Sin servidor Nav2 → HOMING → IDLE inmediato ──────────────────────
    n = len(h.states)
    ctrl = subprocess.Popen(
        [sys.executable, '-m', 'person_follower.control_node.control_node', '--ros-args',
         '--params-file', os.path.join(REPO, 'person_follower/config/config.yaml'),
         '-p', 'nav_action_name:=no_existe', '-r', '/cmd_vel:=/commands/velocity'],
        env=env, stdin=subprocess.DEVNULL)
    try:
        wait_for(lambda: 'IDLE' in h.states[n:], 20)
        time.sleep(2.0)
        h.gesture('go_home')
        check("5. sin servidor Nav2 → HOMING → IDLE",
              wait_for(lambda: h.states[n:][-2:] == ['HOMING', 'IDLE'], 3))
    finally:
        ctrl.terminate()
        ctrl.wait(5)

    ok = sum(r for _, r in results)
    print(f"\n{ok}/{len(results)} comprobaciones correctas", flush=True)
    ex.shutdown()
    rclpy.shutdown()
    sys.exit(0 if ok == len(results) else 1)


if __name__ == '__main__':
    main()
