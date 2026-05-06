"""
dt sweep testi: her sistem icin optimal zaman adimini bul.

Robustness testi (test_lyapunov_robustness.py #9) gosterdi:
- Lorenz dt=0.01 -> %10 hata, dt=0.02 -> %2.5 (oversampling sorunu)

Bu test her built-in ODE sistemi icin dt'yi tarayip:
- Rosenstein (varsayilan algoritma) lambda1
- Benettin (gold standard) lambda1
- Literatur referansi karsilastirmasi
hesaplar. Sonuc: her sistem icin optimal dt + olcum hatasi.

Cikti: tests/test_dt_sweep_sonuc.txt
"""
import os
import sys
import time
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import (
    generate_lorenz, generate_rossler, generate_chua, generate_chen,
    generate_duffing, generate_double_pendulum,
    get_ode_system,
)
from analysis import (
    compute_ami, find_first_minimum,
    compute_fnn, find_embedding_dimension,
    lyapunov_rosenstein, estimate_lyapunov_from_curve,
    estimate_theiler_window, lyapunov_benettin,
)

OUTPUT_LINES = []


def log(msg=""):
    print(msg)
    OUTPUT_LINES.append(msg)


# ----------------------------------------------------------------------
# Sistem konfigurasyonlari: her sistem icin t_total + dt aralik + ekstra
# ----------------------------------------------------------------------

SYSTEMS = [
    {
        'name': 'Lorenz',
        'gen': generate_lorenz,
        'system_key': 'lorenz',
        'lit': 0.9056,
        'dts': [0.001, 0.005, 0.01, 0.02, 0.05, 0.1],
        't_total': 100.0,
        'transient_time': 20.0,
        'extra': {},
    },
    {
        'name': 'Rossler',
        'gen': generate_rossler,
        'system_key': 'rossler',
        'lit': 0.0714,
        'dts': [0.01, 0.02, 0.05, 0.1, 0.2, 0.5],
        't_total': 2000.0,
        'transient_time': 200.0,
        'extra': {},
    },
    {
        'name': 'Chua',
        'gen': generate_chua,
        'system_key': 'chua',
        'lit': 0.33,
        'dts': [0.001, 0.005, 0.01, 0.02, 0.05, 0.1],
        't_total': 200.0,
        'transient_time': 40.0,
        'extra': {},
    },
    {
        'name': 'Chen',
        'gen': generate_chen,
        'system_key': 'chen',
        'lit': 2.027,
        'dts': [0.001, 0.005, 0.01, 0.02, 0.05],
        't_total': 50.0,
        'transient_time': 10.0,
        'extra': {},
    },
    {
        'name': 'Duffing',
        'gen': generate_duffing,
        'system_key': 'duffing',
        'lit': 0.16,
        'dts': [0.005, 0.01, 0.02, 0.05, 0.1, 0.2],
        't_total': 6000.0,
        'transient_time': 500.0,
        'extra': {'gamma': 0.5},
    },
    {
        'name': 'DoublePen',
        'gen': generate_double_pendulum,
        'system_key': 'double_pendulum',
        'lit': 0.5,
        'dts': [0.001, 0.005, 0.01, 0.02, 0.05],
        't_total': 500.0,
        'transient_time': 50.0,
        'extra': {},
    },
]


# ----------------------------------------------------------------------
# Yardimcilar
# ----------------------------------------------------------------------

def estimate_params(data, dt):
    """AMI + FNN + Theiler."""
    ami = compute_ami(data, max_lag=100)
    tau = max(1, find_first_minimum(ami))
    fnn = compute_fnn(data, tau=tau, max_dim=10)
    m = max(2, find_embedding_dimension(fnn, threshold=1.0))
    min_tsep = estimate_theiler_window(data, m=m, tau=tau, min_window=1)
    return tau, m, min_tsep


def compute_rosenstein_at_dt(gen, dt, t_total, transient_time, extra):
    """Verilen dt'de Rosenstein lambda1."""
    n_points = int(t_total / dt)
    transient = int(transient_time / dt)
    ts = gen(t_span=(0, t_total), dt=dt, **extra)
    data = ts.data[transient:]
    if len(data) < 1000:
        return float('nan'), 0, 0
    tau, m, min_tsep = estimate_params(data, dt)
    t_steps, div = lyapunov_rosenstein(data, m=m, tau=tau, dt=dt, min_tsep=min_tsep)
    le = float(estimate_lyapunov_from_curve(t_steps, div))
    return le, tau, m


def compute_benettin_at_dt(system_key, dt, t_total, transient_time, extra):
    """Verilen dt'de Benettin lambda1 (gold standard)."""
    ode_func, y0, dim = get_ode_system(system_key, extra)
    if ode_func is None:
        return float('nan')
    transient_steps = int(transient_time / dt)
    spec = lyapunov_benettin(
        ode_func, y0, t_span=(0, t_total), dt=dt,
        transient=transient_steps, n_exponents=dim,
    )
    exps = spec['exponents']
    return float(exps[0]) if len(exps) > 0 else float('nan')


# ----------------------------------------------------------------------
# Test akisi
# ----------------------------------------------------------------------

def run_dt_sweep_for_system(spec):
    log(f"\n{'=' * 86}")
    log(f">>> {spec['name'].upper()}  (literatur lambda_1 = {spec['lit']:.4f})")
    log(f"{'=' * 86}")
    log(f"{'dt':>8s} | {'tau':>3s} | {'m':>2s} | "
        f"{'Ros LE':>10s} | {'Ros |err|':>9s} | {'Ros err%':>8s} | "
        f"{'Ben LE':>10s} | {'Ben |err|':>9s} | {'Ben err%':>8s} | {'time':>6s}")
    log("-" * 100)

    rows = []
    for dt in spec['dts']:
        t0 = time.time()
        try:
            ros_le, tau, m = compute_rosenstein_at_dt(
                spec['gen'], dt, spec['t_total'], spec['transient_time'], spec['extra']
            )
        except Exception:
            ros_le, tau, m = float('nan'), 0, 0
        try:
            ben_le = compute_benettin_at_dt(
                spec['system_key'], dt, spec['t_total'], spec['transient_time'], spec['extra']
            )
        except Exception:
            ben_le = float('nan')

        elapsed = time.time() - t0
        ros_abs = abs(ros_le - spec['lit']) if np.isfinite(ros_le) else float('nan')
        ben_abs = abs(ben_le - spec['lit']) if np.isfinite(ben_le) else float('nan')
        ros_pct = (ros_abs / spec['lit'] * 100) if np.isfinite(ros_abs) else float('nan')
        ben_pct = (ben_abs / spec['lit'] * 100) if np.isfinite(ben_abs) else float('nan')

        log(f"{dt:>8.4f} | {tau:>3d} | {m:>2d} | "
            f"{ros_le:>10.4f} | {ros_abs:>9.4f} | {ros_pct:>7.1f}% | "
            f"{ben_le:>10.4f} | {ben_abs:>9.4f} | {ben_pct:>7.1f}% | {elapsed:>5.1f}s")

        rows.append({
            'dt': dt, 'ros_le': ros_le, 'ben_le': ben_le,
            'ros_err': ros_pct, 'ben_err': ben_pct, 'tau': tau, 'm': m,
        })

    # Optimal dt'yi bul (en dusuk Rosenstein hatasi)
    valid = [r for r in rows if np.isfinite(r['ros_err'])]
    if valid:
        best = min(valid, key=lambda r: r['ros_err'])
        # Mevcut TSA varsayilani (test_validation.py'deki dt) ile kiyas
        log("")
        log(f"Optimal Rosenstein dt = {best['dt']} -> {best['ros_le']:.4f} ({best['ros_err']:.1f}% hata)")

    valid_ben = [r for r in rows if np.isfinite(r['ben_err'])]
    if valid_ben:
        best_ben = min(valid_ben, key=lambda r: r['ben_err'])
        log(f"Optimal Benettin   dt = {best_ben['dt']} -> {best_ben['ben_le']:.4f} ({best_ben['ben_err']:.1f}% hata)")

    return rows


def main():
    log("=" * 86)
    log("DT SWEEP TESTI — her sistem icin optimal zaman adimi")
    log("=" * 86)
    log("Beklenti: Rosenstein hatasi dt'ye karsi U-sekilli; oversampling (kucuk dt)")
    log("ve undersampling (buyuk dt) ekstremumlarda hata buyur. Benettin (gold")
    log("standard) literature daha yakin sabit kalmali (Jacobian icin yeterince")
    log("kucuk dt gerekir, ama embedding'e duyarli degildir).")

    total_start = time.time()
    summary = {}
    for spec in SYSTEMS:
        rows = run_dt_sweep_for_system(spec)
        valid = [r for r in rows if np.isfinite(r['ros_err'])]
        if valid:
            best = min(valid, key=lambda r: r['ros_err'])
            summary[spec['name']] = {
                'best_dt': best['dt'],
                'best_le': best['ros_le'],
                'best_err': best['ros_err'],
                'lit': spec['lit'],
            }

    total = time.time() - total_start

    # Ozet tablo
    log("\n" + "=" * 86)
    log("OZET — Optimal Rosenstein dt (her sistem icin)")
    log("=" * 86)
    log(f"{'System':10s} | {'Lit LE':>8s} | {'Optimal dt':>10s} | {'LE':>8s} | {'Err%':>6s}")
    log("-" * 60)
    for name, info in summary.items():
        log(f"{name:10s} | {info['lit']:>8.4f} | {info['best_dt']:>10.4f} | "
            f"{info['best_le']:>8.4f} | {info['best_err']:>5.1f}%")
    log("=" * 86)
    log(f"Toplam sure: {total:.1f}s ({total/60:.1f} dk)")

    output_path = os.path.join(os.path.dirname(__file__), 'test_dt_sweep_sonuc.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(OUTPUT_LINES) + "\n")
    print(f"\nSonuclar: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
