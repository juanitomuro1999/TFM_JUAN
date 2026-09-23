#!/usr/bin/env python3
# Copyright 2026 Juan Muñoz Rovira
# SPDX-License-Identifier: Apache-2.0
#
# plot_casa_session.py — Figuras y métricas de la sesión de lab del gesto
# "casa" (2026-09-23) a partir de los CSV de extract_casa_bags.py. Sin ROS,
# solo matplotlib/numpy.
#
# Uso:
#   python3 validation/plot_casa_session.py <dir_csv> <dir_figuras>
#
# Genera en <dir_figuras>:
#   mapa_vueltas_casa.png        trayectorias de cada HOMING sobre el mapa
#   metricas_homing.png          duración y error de llegada de cada vuelta
#   reenganche_antes_despues.png ángulo de la persona publicada, antes/después
#   cronologia_giros.png         estados + ángulo persona + giro de búsqueda
#   gestos_esquema.png           los tres gestos (landmarks MediaPipe)
#   arbitraje_velocidad.png      quién manda en /commands/velocity
#   metricas_homing.csv          una fila por vuelta a casa

import csv
import math
import os
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
HOME = (5.100, -7.758, math.radians(-140.6))
STATE_COLORS = {'IDLE': '#9aa0a6', 'TRACKING': '#1a73e8', 'HOMING': '#e8710a',
                'MANUAL': '#9334e6', 'INIT': '#dadce0', 'SHUTDOWN': '#000000'}
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                     'figure.dpi': 150, 'savefig.bbox': 'tight'})


def read(path, cols):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        rows = list(csv.DictReader(f))
    return [tuple(r[c] if c in ('state', 'gesture') else float(r[c]) for c in cols) for r in rows]


def load_run(d):
    return {
        'pose': read(os.path.join(d, 'pose_map.csv'), ('t', 'x', 'y', 'yaw')),
        'state': read(os.path.join(d, 'state.csv'), ('t', 'state')),
        'gesture': read(os.path.join(d, 'gesture.csv'), ('t', 'gesture')),
        'person': read(os.path.join(d, 'person.csv'), ('t', 'x', 'y')),
        'cmd': read(os.path.join(d, 'cmd.csv'), ('t', 'vx', 'wz')),
        'track': read(os.path.join(d, 'track_cmd.csv'), ('t', 'vx', 'wz')),
    }


def segments(states, t_end):
    out = []
    for i, (t, s) in enumerate(states):
        t1 = states[i + 1][0] if i + 1 < len(states) else t_end
        out.append((t, t1, s))
    return out


def pose_at(pose, t):
    ts = [p[0] for p in pose]
    i = int(np.searchsorted(ts, t))
    i = min(max(i, 0), len(pose) - 1)
    return pose[i]


def load_map():
    y = open(os.path.join(REPO, 'maps', 'mapa_laboratorio.yaml')).read()
    res = float(y.split('resolution:')[1].split()[0])
    org = [float(v) for v in y.split('origin:')[1].split('[')[1].split(']')[0].split(',')]
    d = open(os.path.join(REPO, 'maps', 'mapa_laboratorio.pgm'), 'rb').read()
    tok, i = [], 0
    while len(tok) < 4:
        while d[i:i + 1].isspace():
            i += 1
        if d[i:i + 1] == b'#':
            while d[i:i + 1] != b'\n':
                i += 1
            continue
        j = i
        while not d[j:j + 1].isspace():
            j += 1
        tok.append(d[i:j])
        i = j
    w, h = int(tok[1]), int(tok[2])
    img = np.frombuffer(d[i + 1:i + 1 + w * h], dtype=np.uint8).reshape(h, w)
    ext = (org[0], org[0] + w * res, org[1], org[1] + h * res)
    return img, ext


def homing_runs(runs):
    """Una entrada por cada tramo HOMING completo dentro de un bag."""
    out = []
    for name, r in runs.items():
        if not r['pose']:
            continue
        t_end = r['pose'][-1][0]
        for t0, t1, s in segments(r['state'], t_end):
            if s != 'HOMING' or t1 >= t_end:
                continue
            nxt = [st for tt, st in r['state'] if tt >= t1]
            p0, p1 = pose_at(r['pose'], t0), pose_at(r['pose'], t1 + 0.5)
            err = math.hypot(p1[1] - HOME[0], p1[2] - HOME[1])
            yaw_err = abs(math.degrees(math.atan2(math.sin(p1[3] - HOME[2]), math.cos(p1[3] - HOME[2]))))
            traj = [(p[1], p[2]) for p in r['pose'] if t0 <= p[0] <= t1]
            # Cancelado con la mano izquierda si hubo stop_tracking justo antes de salir
            cancelled = any(g == 'stop_tracking' and t1 - 1.0 <= tg <= t1 + 0.2 for tg, g in r['gesture'])
            ok = err < 0.5 and not cancelled
            prev = [st for tt, st in r['state'] if tt < t0]
            out.append({'bag': name, 't0': t0, 'dur': t1 - t0, 'start': (p0[1], p0[2]),
                        'from': prev[-1] if prev else '?', 'err': err, 'yaw_err': yaw_err,
                        'result': 'cancelado' if cancelled else ('éxito' if ok else 'fallo'),
                        'traj': traj, 'next': nxt[0] if nxt else '?'})
    return sorted(out, key=lambda h: h['t0'])


def fig_map(homings, out):
    img, ext = load_map()
    fig, ax = plt.subplots(figsize=(7.5, 7))
    ax.imshow(img, cmap='gray', extent=ext, origin='upper', vmin=0, vmax=255)
    colors = {'éxito': '#1e8e3e', 'fallo': '#d93025', 'cancelado': '#f9ab00'}
    labeled = set()
    for h in homings:
        if not h['traj']:
            continue
        xs, ys = zip(*h['traj'])
        lab = h['result'] if h['result'] not in labeled else None
        labeled.add(h['result'])
        ax.plot(xs, ys, '-', color=colors[h['result']], lw=2, alpha=0.9, label=lab)
        ax.plot(xs[0], ys[0], 'o', color=colors[h['result']], ms=5)
    ax.plot(HOME[0], HOME[1], marker='*', color='#1a73e8', ms=20, mec='white', label='casa')
    ax.annotate('', xy=(HOME[0] + 0.5 * math.cos(HOME[2]), HOME[1] + 0.5 * math.sin(HOME[2])),
                xytext=(HOME[0], HOME[1]), arrowprops=dict(arrowstyle='->', color='#1a73e8', lw=2))
    allx = [x for h in homings for x, _ in h['traj']] + [HOME[0]]
    ally = [y for h in homings for _, y in h['traj']] + [HOME[1]]
    ax.set_xlim(min(allx) - 1.5, max(allx) + 1.5)
    ax.set_ylim(min(ally) - 1.5, max(ally) + 1.5)
    ax.set_xlabel('x mapa (m)')
    ax.set_ylabel('y mapa (m)')
    n = {k: sum(h['result'] == k for h in homings) for k in ('éxito', 'cancelado', 'fallo')}
    ax.set_title(f'Vueltas a casa con el gesto "tejado" (lab 23/09, bags)\n'
                 f"{n['éxito']} completadas · {n['cancelado']} cancelada a propósito · "
                 f"{n['fallo']} fallo (localización junto a obstáculo)", fontsize=11)
    ax.legend(loc='upper right', framealpha=0.9)
    fig.savefig(os.path.join(out, 'mapa_vueltas_casa.png'))
    plt.close(fig)


def fig_metrics(homings, out):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8))
    labels = [f"{i + 1}\n{'TRK' if h['from'] == 'TRACKING' else h['from']}" for i, h in enumerate(homings)]
    col = ['#1e8e3e' if h['result'] == 'éxito' else ('#f9ab00' if h['result'] == 'cancelado' else '#d93025')
           for h in homings]
    a1.bar(labels, [h['dur'] for h in homings], color=col)
    a1.set_ylabel('duración HOMING (s)')
    a1.set_title('Tiempo desde el gesto hasta IDLE')
    succ = [h for h in homings if h['result'] == 'éxito']
    a2.bar([labels[homings.index(h)] for h in succ], [h['err'] for h in succ], color='#1e8e3e')
    a2.axhline(0.25, ls='--', color='#5f6368', lw=1)
    a2.text(0.02, 0.26, 'xy_goal_tolerance de Nav2 (0.25 m)', transform=a2.get_yaxis_transform(),
            fontsize=9, color='#5f6368')
    a2.set_ylabel('error de llegada (m)')
    a2.set_title('Distancia final a la pose casa (éxitos)')
    for a in (a1, a2):
        a.set_xlabel('vuelta nº / estado de partida')
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'metricas_homing.png'))
    plt.close(fig)


def person_angles(runs, names):
    angs = []
    for n in names:
        for _, x, y in runs.get(n, {}).get('person', []):
            angs.append(math.degrees(math.atan2(y, x)))
    return np.array(angs)


def fig_reacquire(runs, out):
    before = [n for n in runs if 'casa_C1' in n or n.endswith('casa_C2')]
    after = [n for n in runs if 'C5_reacquire' in n or 'giros_busqueda' in n]
    b, a = person_angles(runs, before), person_angles(runs, after)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
    bins = np.arange(-180, 181, 10)
    for ax, data, title, c in ((axes[0], b, 'Antes (reenganche en cualquier dirección)', '#d93025'),
                               (axes[1], a, 'Después (reenganche solo delante, ±90°)', '#1e8e3e')):
        ax.hist(data, bins=bins, color=c, alpha=0.85)
        ax.axvspan(-90, 90, color='#e6f4ea', zorder=0)
        ax.set_yscale('log')
        ax.set_xlim(-180, 180)
        ax.set_xticks(range(-180, 181, 45))
        ax.set_xlabel('ángulo de la "persona" publicada (°, 0 = delante)')
        far = np.mean(np.abs(data) > 90) * 100 if len(data) else 0
        ax.set_title(f'{title}\n{len(data)} posiciones, {far:.1f}% detrás del robot', fontsize=10)
    axes[0].set_ylabel('nº de posiciones (log)')
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'reenganche_antes_despues.png'))
    plt.close(fig)
    return b, a


def fig_timeline(runs, out):
    name = next((n for n in runs if 'giros_busqueda' in n), None)
    if not name:
        return
    r = runs[name]
    t0 = r['pose'][0][0]
    t_end = r['pose'][-1][0]
    fig, (a0, a1, a2) = plt.subplots(3, 1, figsize=(10, 6), sharex=True,
                                      gridspec_kw={'height_ratios': [0.6, 2, 2]})
    for s0, s1, s in segments(r['state'], t_end):
        a0.axvspan(s0 - t0, s1 - t0, color=STATE_COLORS.get(s, '#ccc'))
        if s1 - s0 > 9:
            a0.text((s0 + s1) / 2 - t0, 0.5, s, ha='center', va='center', color='white', fontsize=8)
    a0.set_yticks([])
    a0.set_ylabel('estado')
    for tg, g in r['gesture']:
        if g == 'go_home':
            a0.annotate('tejado', xy=(tg - t0, 1.0), xytext=(tg - t0, 1.35), ha='center', fontsize=8,
                        arrowprops=dict(arrowstyle='->', lw=0.8))
    pt = np.array([p[0] - t0 for p in r['person']])
    pa = np.array([math.degrees(math.atan2(p[2], p[1])) for p in r['person']])
    a1.plot(pt, pa, '.', ms=2, color='#1a73e8')
    a1.axhspan(-90, 90, color='#e6f4ea', zorder=0)
    a1.set_ylabel('persona (°)')
    a1.set_ylim(-180, 180)
    tt = np.array([c[0] - t0 for c in r['track']])
    tw = np.array([c[2] for c in r['track']])
    tv = np.array([c[1] for c in r['track']])
    a2.plot(tt, tw, color='#5f6368', lw=1, label='wz seguimiento')
    search = (tv == 0) & (np.abs(np.abs(tw) - 0.5) < 0.02)
    a2.plot(tt[search], tw[search], 'o', ms=3, color='#e8710a', label='giro de búsqueda (0.5 rad/s)')
    a2.set_ylabel('wz (rad/s)')
    a2.set_xlabel('tiempo (s)')
    a2.legend(loc='upper right', fontsize=9)
    a0.set_title('Toma con giros: pérdidas, giro de búsqueda y reenganche; tejado → HOMING')
    fig.tight_layout()
    fig.savefig(os.path.join(out, 'cronologia_giros.png'))
    plt.close(fig)


def fig_gestures(out):
    sys.path.insert(0, os.path.join(REPO, 'validation'))
    import verify_home_gesture as v
    from person_follower.visual_detection_node.gestures import classify_gesture
    poses = [('Mano derecha arriba', v.pose(v.UP_R, v.DOWN_L), 'seguir'),
             ('Mano izquierda arriba', v.pose(v.DOWN_R, v.UP_L), 'parar / cancelar'),
             ('"Tejado"', v.pose(v.ROOF_R, v.ROOF_L), 'volver a casa')]
    bones = [(11, 12), (11, 23), (12, 24), (23, 24), (11, 15), (12, 16)]
    fig, axes = plt.subplots(1, 3, figsize=(10, 4))
    for ax, (title, lm, action) in zip(axes, poses):
        g, _ = classify_gesture(lm, 0.5, 0.15, 0.6)
        for a, b in bones:
            ax.plot([lm[a].x, lm[b].x], [lm[a].y, lm[b].y], '-', color='#3c4043', lw=3)
        ax.add_patch(plt.Circle((lm[0].x, lm[0].y - 0.02), 0.06, fill=False, color='#3c4043', lw=3))
        for i in (15, 16):
            ax.plot(lm[i].x, lm[i].y, 'o', color='#e8710a' if g == 'go_home' else '#1a73e8', ms=10)
        ax.axhline(lm[11].y, ls=':', color='#9aa0a6', lw=1)
        ax.set_xlim(0.2, 0.8)
        ax.set_ylim(0.75, -0.05)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f'{title}\n→ {g}\n({action})', fontsize=11)
    fig.suptitle('Gestos reconocidos (vista de la cámara; MediaPipe Pose)', y=1.10)
    fig.savefig(os.path.join(out, 'gestos_esquema.png'))
    plt.close(fig)


def fig_arbitration(out):
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.axis('off')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.2)

    def box(x, y, w, h, text, c):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.05', fc=c, ec='#3c4043'))
        ax.text(x + w / 2, y + h / 2, text, ha='center', va='center', fontsize=10)

    def arrow(x0, y0, x1, y1, text='', dy=0.12):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle='-|>', mutation_scale=14,
                                     color='#3c4043', lw=1.4))
        if text:
            ax.text((x0 + x1) / 2, (y0 + y1) / 2 + dy, text, ha='center', fontsize=8.5, color='#3c4043')

    box(0.1, 3.0, 2.4, 0.9, 'visual_detection_node\n(MediaPipe: 3 gestos)', '#e8f0fe')
    box(0.1, 1.7, 2.4, 0.9, 'tracking_node\n(Kalman + PD + evasión)', '#e8f0fe')
    box(0.1, 0.3, 2.4, 0.9, 'Nav2\n(controller + behaviors)', '#fef7e0')
    box(4.0, 1.4, 2.4, 1.5, 'control_node\nFSM: IDLE / TRACKING /\nHOMING / MANUAL', '#e6f4ea')
    box(7.6, 1.7, 2.2, 0.9, 'Base Kobuki', '#f1f3f4')
    arrow(2.5, 3.45, 4.0, 2.7, '/gesture_command')
    arrow(2.5, 2.15, 4.0, 2.15, '/tracking/velocity_cmd')
    arrow(2.5, 0.55, 5.0, 1.4, '/nav2/cmd_vel', dy=-0.32)
    arrow(6.4, 2.15, 7.6, 2.15, '/commands/velocity')
    arrow(4.3, 1.4, 2.5, 1.0, 'NavigateToPose (casa)', dy=0.15)
    ax.text(5.2, 3.95, 'Solo la fuente del estado activo llega a la base:\n'
            'TRACKING → seguimiento · HOMING → Nav2 · IDLE → parada',
            ha='center', fontsize=9.5, style='italic', color='#3c4043')
    fig.savefig(os.path.join(out, 'arbitraje_velocidad.png'))
    plt.close(fig)


def main():
    src, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    sys.path.insert(0, REPO)
    runs = {n: load_run(os.path.join(src, n)) for n in sorted(os.listdir(src))
            if os.path.isdir(os.path.join(src, n))}
    homings = homing_runs(runs)
    with open(os.path.join(out, 'metricas_homing.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['n', 'bag', 'desde', 'duracion_s', 'inicio_x', 'inicio_y', 'resultado',
                    'error_llegada_m', 'error_yaw_deg'])
        for i, h in enumerate(homings):
            w.writerow([i + 1, h['bag'], h['from'], f"{h['dur']:.1f}", f"{h['start'][0]:.2f}",
                        f"{h['start'][1]:.2f}", h['result'], f"{h['err']:.2f}", f"{h['yaw_err']:.1f}"])
            print(f"{i + 1:2d} {h['bag'][16:]:22s} desde {h['from']:9s} {h['dur']:5.1f}s "
                  f"inicio=({h['start'][0]:.2f},{h['start'][1]:.2f}) {h['result']:9s} "
                  f"err={h['err']:.2f}m yaw={h['yaw_err']:.1f}°")
    fig_map(homings, out)
    fig_metrics(homings, out)
    b, a = fig_reacquire(runs, out)
    print(f"reenganche: antes {len(b)} pos, {np.mean(np.abs(b) > 90) * 100:.1f}% detrás; "
          f"después {len(a)} pos, {np.mean(np.abs(a) > 90) * 100:.1f}% detrás")
    fig_timeline(runs, out)
    fig_gestures(out)
    fig_arbitration(out)
    print('figuras en', out)


if __name__ == '__main__':
    main()
