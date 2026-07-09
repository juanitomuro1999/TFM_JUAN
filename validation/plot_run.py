#!/usr/bin/env python3
# Copyright 2026 Juan Muriel Rovira
# SPDX-License-Identifier: Apache-2.0
#
# plot_run.py — Genera las graficas de una toma de validacion a partir de los
#   CSV producidos por bag_to_csv.py. Pensado para ejecutarse en el portatil
#   (necesita matplotlib; NO necesita ROS).
#
#   Produce en <dir>/figs/:
#     dist_vs_t.png        distancia a la persona vs tiempo (+ linea objetivo)
#     angle_vs_t.png       error angular (rumbo) vs tiempo
#     vel_vs_t.png         velocidad lineal y angular comandadas vs tiempo
#     trayectoria.png      trayectoria del robot en el plano (odom)
#   Y un resumen de metricas por consola y en metrics.txt:
#     error medio/RMS de distancia respecto al objetivo, % tiempo detectado,
#     nº de perdidas de deteccion, velocidades max, etc.
#     Si position.csv existe (requiere bag_to_csv.py actualizado 2026-07,
#     que extrae /person_position): % de saltos de posicion > umbral y % de
#     saturacion angular con posicion estable (ver docs/07_resultados.md
#     §7.5 y docs/decisiones.md, entrada 2026-07-09, sobre la metodologia
#     y sus limites frente a las cifras del script ad-hoc original).
#
# Uso:
#   python3 plot_run.py <dir_analysis>           # carpeta con telemetry.csv, etc.
#   python3 plot_run.py <dir_analysis> --target 1.0

import argparse
import bisect
import csv
import math
import os
import sys

try:
    import matplotlib
    matplotlib.use('Agg')  # backend sin pantalla → guarda PNG directamente
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit("[error] Falta matplotlib. Instala con: pip install matplotlib")


def load_csv(path):
    if not os.path.isfile(path):
        return []
    with open(path, newline='') as f:
        return list(csv.DictReader(f))


def to_float(rows, key):
    out = []
    for r in rows:
        try:
            out.append(float(r[key]))
        except (ValueError, KeyError, TypeError):
            out.append(float('nan'))
    return out


def rel_time(ts):
    """Tiempos relativos al primer instante (s)."""
    if not ts:
        return []
    t0 = ts[0]
    return [t - t0 for t in ts]


def load_xy(rows):
    """(t_bag, x, y) ordenados por tiempo, descartando filas invalidas."""
    pts = []
    for r in rows:
        try:
            pts.append((float(r['t_bag']), float(r['x']), float(r['y'])))
        except (ValueError, KeyError, TypeError):
            continue
    pts.sort(key=lambda p: p[0])
    return pts


def position_jumps(pos_pts, threshold):
    """% de saltos entre muestras consecutivas de posicion cruda > threshold (m)."""
    if len(pos_pts) < 2:
        return float('nan'), float('nan'), 0
    jumps = [math.hypot(x1 - x0, y1 - y0)
              for (_, x0, y0), (_, x1, y1) in zip(pos_pts, pos_pts[1:])]
    frac = sum(1 for d in jumps if d > threshold) / len(jumps)
    return frac, max(jumps), len(jumps)


def stable_mask(pos_pts, query_ts, window_s, radius):
    """Para cada instante en query_ts: ¿la posicion cruda estuvo 'estable'
    (todas las muestras en [t-window_s, t] caben en un circulo de radio
    `radius`)? Requiere >=2 muestras de posicion en la ventana; si no hay
    datos suficientes se considera "no estable" (no se afirma sin evidencia).
    """
    times = [p[0] for p in pos_pts]
    mask = []
    for qt in query_ts:
        lo = bisect.bisect_left(times, qt - window_s)
        hi = bisect.bisect_right(times, qt)
        window = pos_pts[lo:hi]
        if len(window) < 2:
            mask.append(False)
            continue
        xs = [p[1] for p in window]
        ys = [p[2] for p in window]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        max_dev = max(math.hypot(x - cx, y - cy) for x, y in zip(xs, ys))
        mask.append(max_dev <= radius)
    return mask


def saturation_with_stability(vang, t_abs, pos_pts, sat_threshold, window_s, radius):
    """% de muestras de vang saturadas (overall) y restringido a instantes
    con posicion cruda localmente estable (ver stable_mask)."""
    idx = [i for i, v in enumerate(vang) if not math.isnan(v)]
    if not idx:
        return float('nan'), float('nan'), 0
    sat = [abs(vang[i]) >= sat_threshold for i in idx]
    overall_frac = sum(sat) / len(sat)
    if not pos_pts:
        return overall_frac, float('nan'), 0
    query_ts = [t_abs[i] for i in idx]
    stable = stable_mask(pos_pts, query_ts, window_s, radius)
    stable_sat = [s for s, is_stable in zip(sat, stable) if is_stable]
    stable_frac = (sum(stable_sat) / len(stable_sat)) if stable_sat else float('nan')
    return overall_frac, stable_frac, len(stable_sat)


def main():
    ap = argparse.ArgumentParser(description="Graficas de validacion TFM")
    ap.add_argument('dir', help="carpeta con telemetry.csv / odom.csv / ...")
    ap.add_argument('--target', type=float, default=None,
                    help="distancia objetivo (m) para la linea de referencia "
                         "(def: tomar de config, 1.0)")
    ap.add_argument('--jump-threshold', type=float, default=0.8,
                    help="umbral (m) para contar un salto de posicion cruda entre "
                         "muestras consecutivas (def: 0.8, igual que PROGRESO.md)")
    ap.add_argument('--stable-radius', type=float, default=0.15,
                    help="radio (m) por debajo del cual la posicion cruda en la "
                         "ventana se considera 'estable' (def: 0.15)")
    ap.add_argument('--stable-window', type=float, default=1.0,
                    help="ventana temporal (s) hacia atras para evaluar estabilidad "
                         "de la posicion cruda (def: 1.0)")
    ap.add_argument('--sat-threshold', type=float, default=0.95,
                    help="|vang| a partir del cual se considera 'saturado' "
                         "(def: 0.95; el clamp de tracking_node es a ±1.0 rad/s)")
    args = ap.parse_args()

    d = os.path.abspath(args.dir)
    figs = os.path.join(d, 'figs')
    os.makedirs(figs, exist_ok=True)
    target = args.target if args.target is not None else 1.0

    telem = load_csv(os.path.join(d, 'telemetry.csv'))
    odom = load_csv(os.path.join(d, 'odom.csv'))
    det = load_csv(os.path.join(d, 'detection.csv'))
    gestures = load_csv(os.path.join(d, 'gestures.csv'))
    fsm = load_csv(os.path.join(d, 'fsm_states.csv'))
    position = load_csv(os.path.join(d, 'position.csv'))

    if not telem:
        sys.exit(f"[error] No hay telemetry.csv en {d} (¿ejecutaste bag_to_csv.py?)")

    # ── Series de telemetria ──────────────────────────────────────────────────
    t_abs = to_float(telem, 't')
    t0_abs = t_abs[0] if t_abs else 0.0
    t = rel_time(t_abs)
    dist = to_float(telem, 'dist')
    angle = to_float(telem, 'angle_deg')
    vlin = to_float(telem, 'vlin')
    vang = to_float(telem, 'vang')

    # ── Eventos de gestos / estado FSM, en tiempo relativo al inicio de telemetria
    # (telemetry "t" y "t_bag" comparten escala epoch → restamos el mismo t0).
    def events(rows, key, t0):
        out = []
        for r in rows:
            try:
                out.append((float(r['t_bag']) - t0, r[key]))
            except (ValueError, KeyError, TypeError):
                continue
        return out

    gesture_ev = events(gestures, 'gesture', t0_abs)
    fsm_ev = events(fsm, 'state', t0_abs)

    def overlay_events(ax):
        seen_labels = set()
        for te, g in gesture_ev:
            color = 'green' if 'start' in g else ('red' if 'stop' in g else 'gray')
            lab = g if g not in seen_labels else None
            seen_labels.add(g)
            ax.axvline(te, color=color, ls=':', lw=1.2, alpha=0.8, label=lab)
        for te, s in fsm_ev:
            if s == 'TRACKING':
                lab = 'TRACKING' if 'TRACKING' not in seen_labels else None
                seen_labels.add('TRACKING')
                ax.axvline(te, color='tab:green', ls='--', lw=0.8, alpha=0.5, label=lab)
            elif s == 'IDLE':
                lab = 'IDLE' if 'IDLE' not in seen_labels else None
                seen_labels.add('IDLE')
                ax.axvline(te, color='tab:red', ls='--', lw=0.8, alpha=0.5, label=lab)

    # ── 1) Distancia vs tiempo (con eventos de gesto/estado) ───────────────────
    plt.figure(figsize=(9, 4))
    ax = plt.gca()
    ax.plot(t, dist, lw=1.2, label='distancia medida')
    ax.axhline(target, color='r', ls='--', lw=1, label=f'objetivo {target:.2f} m')
    overlay_events(ax)
    ax.set_xlabel('tiempo (s)'); ax.set_ylabel('distancia (m)')
    ax.set_title('Distancia robot-persona'); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(figs, 'dist_vs_t.png'), dpi=140)
    plt.close()

    # ── 2) Error angular vs tiempo ─────────────────────────────────────────────
    plt.figure(figsize=(9, 4))
    plt.plot(t, angle, lw=1.2, color='tab:orange')
    plt.axhline(0, color='k', lw=0.6)
    plt.xlabel('tiempo (s)'); plt.ylabel('rumbo a la persona (deg)')
    plt.title('Error angular'); plt.grid(alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(figs, 'angle_vs_t.png'), dpi=140)
    plt.close()

    # ── 3) Velocidades comandadas vs tiempo ────────────────────────────────────
    fig, ax1 = plt.subplots(figsize=(9, 4))
    ax1.plot(t, vlin, lw=1.2, color='tab:blue', label='v lineal (m/s)')
    ax1.set_xlabel('tiempo (s)'); ax1.set_ylabel('v lineal (m/s)', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue'); ax1.grid(alpha=0.3)
    ax2 = ax1.twinx()
    ax2.plot(t, vang, lw=1.0, color='tab:green', label='v angular (rad/s)')
    ax2.set_ylabel('v angular (rad/s)', color='tab:green')
    ax2.tick_params(axis='y', labelcolor='tab:green')
    plt.title('Velocidades comandadas')
    fig.tight_layout(); plt.savefig(os.path.join(figs, 'vel_vs_t.png'), dpi=140)
    plt.close()

    # ── 4) Trayectoria del robot (odom) ────────────────────────────────────────
    if odom:
        x = to_float(odom, 'x'); y = to_float(odom, 'y')
        plt.figure(figsize=(6, 6))
        plt.plot(x, y, lw=1.3)
        if x and y:
            plt.plot(x[0], y[0], 'go', label='inicio')
            plt.plot(x[-1], y[-1], 'rs', label='fin')
        plt.xlabel('x (m)'); plt.ylabel('y (m)')
        plt.title('Trayectoria del robot (odom)'); plt.axis('equal')
        plt.legend(); plt.grid(alpha=0.3)
        plt.tight_layout(); plt.savefig(os.path.join(figs, 'trayectoria.png'), dpi=140)
        plt.close()

    # ── Metricas ───────────────────────────────────────────────────────────────
    def clean(xs):
        return [v for v in xs if not math.isnan(v)]

    dist_c = clean(dist)
    err = [v - target for v in dist_c]
    rms = math.sqrt(sum(e * e for e in err) / len(err)) if err else float('nan')
    mae = sum(abs(e) for e in err) / len(err) if err else float('nan')

    # Perdidas de deteccion: transiciones 1->0 en /person_detected
    det_vals = [r for r in det if r.get('kind') == 'detected']
    losses, prev = 0, None
    detected_frac = float('nan')
    if det_vals:
        seq = [int(r['value']) for r in det_vals]
        for v in seq:
            if prev == 1 and v == 0:
                losses += 1
            prev = v
        detected_frac = sum(seq) / len(seq)

    dur = (t[-1] - t[0]) if len(t) > 1 else 0.0

    # Saltos de posicion cruda (/person_position) y saturacion angular con
    # posicion estable — requieren position.csv (bag_to_csv.py actualizado
    # 2026-07). Si no existe (bag generado con una version anterior del
    # script), se omiten estas lineas en vez de fallar.
    pos_pts = load_xy(position)
    jump_lines = []
    if pos_pts:
        jump_frac, jump_max, n_pairs = position_jumps(pos_pts, args.jump_threshold)
        sat_overall, sat_stable, n_stable = saturation_with_stability(
            vang, t_abs, pos_pts, args.sat_threshold,
            args.stable_window, args.stable_radius)
        jump_lines = [
            f"  % saltos posicion >{args.jump_threshold:.2f}m: {jump_frac*100:.1f} % "
            f"({n_pairs} pares consecutivos, salto max {jump_max:.2f} m)",
            f"  % saturacion |vang|>={args.sat_threshold:.2f} (global): {sat_overall*100:.1f} %",
            (f"  % saturacion con posicion estable*: {sat_stable*100:.1f} % "
             f"({n_stable} muestras estables de {len(pos_pts)} pos.)")
            if not math.isnan(sat_stable) else
            "  % saturacion con posicion estable*: sin muestras estables suficientes",
        ]
    else:
        jump_lines = ["  saltos posicion / saturacion estable: sin position.csv "
                      "(re-generar con bag_to_csv.py actualizado)"]

    lines = [
        f"Resumen de la toma: {os.path.basename(d)}",
        f"  duracion                : {dur:.1f} s ({len(telem)} muestras telemetria)",
        f"  distancia objetivo      : {target:.2f} m",
        f"  error distancia MAE     : {mae:.3f} m",
        f"  error distancia RMS     : {rms:.3f} m",
        f"  distancia min / max     : {min(dist_c):.2f} / {max(dist_c):.2f} m" if dist_c else "  distancia: sin datos",
        f"  |error angular| medio   : {sum(abs(a) for a in clean(angle))/max(len(clean(angle)),1):.1f} deg",
        f"  v lineal max            : {max(clean(vlin), default=float('nan')):.3f} m/s",
        f"  |v angular| max         : {max((abs(v) for v in clean(vang)), default=float('nan')):.3f} rad/s",
        f"  % tiempo persona detect.: {detected_frac*100:.1f} %" if not math.isnan(detected_frac) else "  deteccion: sin datos",
        f"  nº perdidas deteccion   : {losses}",
    ] + jump_lines
    if pos_pts:
        lines.append(
            "  * 'estable' = posicion cruda con desviacion <="
            f"{args.stable_radius:.2f}m dentro de los ultimos {args.stable_window:.1f}s "
            "(ver docs/decisiones.md, 2026-07-09, y docs/07_resultados.md §7.5: "
            "metodologia propia, no garantiza reproducir de forma identica las "
            "cifras de PROGRESO.md calculadas con el script ad-hoc perdido).")
    report = '\n'.join(lines)
    print(report)
    with open(os.path.join(d, 'metrics.txt'), 'w') as f:
        f.write(report + '\n')

    print(f"\n[ok] Figuras en {figs}/  ·  metricas en {os.path.join(d, 'metrics.txt')}")


if __name__ == '__main__':
    main()
