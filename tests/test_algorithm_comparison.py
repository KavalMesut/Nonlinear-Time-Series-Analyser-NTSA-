"""
Algoritma karsilastirma matrisi.

3 veri tipi x 5 algoritma sistematik benchmark:

Test A — Map (discrete) sistemler:
  - Wolf, Rosenstein, Kantz, Sano-Sawada
  - 5 sistem: Logistic, Henon, Tent, Sine, Ikeda
  - Benettin uygulanamaz (denklem yok = ayrik harita)

Test B — ODE (denklem bilinen) sistemler:
  - Wolf, Rosenstein, Kantz, Sano-Sawada, Benettin (gold standard)
  - 5 sistem: Lorenz, Rossler, Chua, Chen, Duffing

Test C — Time-series (CSV / deneysel mode):
  - ODE'lerden data uretiliyor ama 'sistem bilinmiyor' olarak ele aliniyor
  - Sadece x(t) zaman serisi, metadata yok
  - Wolf, Rosenstein, Kantz, Sano-Sawada (Benettin yok)

Cikti tabolari:
  - Her sistem icin algoritma siralamasi (en yakin literatur degerine)
  - Veri tipi bazinda ortalama hata
  - Onerilen algoritma matrisi

Cikti dosyasi: tests/test_algorithm_comparison_sonuc.txt
"""
import os
import sys
import time
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import (
    generate_lorenz, generate_rossler, generate_chua, generate_chen,
    generate_duffing,
    logistic_map, henon_map, tent_map, sine_map, ikeda_map,
    get_ode_system,
)
from analysis import (
    compute_ami, find_first_minimum,
    compute_fnn, find_embedding_dimension,
    estimate_theiler_window,
    lyapunov_wolf, lyapunov_rosenstein, lyapunov_kantz,
    lyapunov_spectrum, lyapunov_benettin,
    estimate_lyapunov_from_curve,
)

OUTPUT_LINES = []


def log(msg=""):
    print(msg)
    OUTPUT_LINES.append(msg)


# ----------------------------------------------------------------------
# Sistem konfigurasyonlari
# ----------------------------------------------------------------------

MAP_SYSTEMS = [
    {'name': 'Logistic', 'gen': lambda: logistic_map(r=4.0, n=10000),         'lit': np.log(2)},
    {'name': 'Henon',    'gen': lambda: henon_map(a=1.4, b=0.3, n=10000),     'lit': 0.42},
    {'name': 'Tent',     'gen': lambda: tent_map(mu=2.0, n=10000),            'lit': np.log(2)},
    {'name': 'Sine',     'gen': lambda: sine_map(lambda_param=1.0, n=10000),  'lit': np.log(2)},
    {'name': 'Ikeda',    'gen': lambda: ikeda_map(u=0.9, n=10000),            'lit': 0.51},
]

# ODE sistemleri: optimal dt, t_total ve transient_time test_dt_sweep'ten
ODE_SYSTEMS = [
    {
        'name': 'Lorenz', 'system_key': 'lorenz', 'lit': 0.9056,
        'gen': lambda: generate_lorenz(t_span=(0, 100), dt=0.02),
        'dt': 0.02, 'transient': 1000,  # 20 birim zaman
        't_total': 100.0,
    },
    {
        'name': 'Rossler', 'system_key': 'rossler', 'lit': 0.0714,
        'gen': lambda: generate_rossler(t_span=(0, 2000), dt=0.02),
        'dt': 0.02, 'transient': 10000,  # 200 birim zaman
        't_total': 2000.0,
    },
    {
        'name': 'Chua', 'system_key': 'chua', 'lit': 0.33,
        'gen': lambda: generate_chua(t_span=(0, 200), dt=0.1),
        'dt': 0.1, 'transient': 400,  # 40 birim zaman
        't_total': 200.0,
    },
    {
        'name': 'Chen', 'system_key': 'chen', 'lit': 2.027,
        'gen': lambda: generate_chen(t_span=(0, 50), dt=0.01),
        'dt': 0.01, 'transient': 1000,  # 10 birim zaman
        't_total': 50.0,
    },
    {
        'name': 'Duffing', 'system_key': 'duffing', 'lit': 0.16,
        'gen': lambda: generate_duffing(t_span=(0, 6000), dt=0.02, gamma=0.5),
        'dt': 0.02, 'transient': 25000,  # 500 birim zaman
        't_total': 6000.0,
        'extra': {'gamma': 0.5},
    },
]


# ----------------------------------------------------------------------
# Algoritma calistirma yardimcilari
# ----------------------------------------------------------------------

def run_algo(algo_name: str, data: np.ndarray, dt: float,
             system_key: str = None, ode_extra: dict = None,
             t_total: float = 100.0, transient_steps: int = 2000) -> tuple:
    """
    Bir algoritmayi calistirir. (lambda1, sure_saniye) doner.
    Hata olursa (NaN, sure) doner.
    """
    t0 = time.time()
    try:
        if algo_name == 'benettin':
            if system_key is None:
                return float('nan'), time.time() - t0
            kwargs = ode_extra or {}
            ode_func, y0, dim = get_ode_system(system_key, kwargs)
            if ode_func is None:
                return float('nan'), time.time() - t0
            spec = lyapunov_benettin(
                ode_func, y0, t_span=(0, t_total), dt=dt,
                transient=transient_steps, n_exponents=dim,
            )
            exps = spec['exponents']
            le = float(exps[0]) if len(exps) > 0 else float('nan')
        else:
            # Veri uzerinden hesap: AMI + FNN + algoritma
            if dt < 0.5:  # ODE
                ami = compute_ami(data, max_lag=100)
                tau = max(1, find_first_minimum(ami))
            else:  # Map
                tau = 1
            fnn = compute_fnn(data, tau=tau, max_dim=10)
            m = max(2, find_embedding_dimension(fnn, threshold=1.0))
            min_tsep = estimate_theiler_window(data, m=m, tau=tau, min_window=1)

            if algo_name == 'wolf':
                le = float(lyapunov_wolf(data, m=m, tau=tau, dt=dt, min_tsep=min_tsep))
            elif algo_name == 'rosenstein':
                t_steps, div = lyapunov_rosenstein(data, m=m, tau=tau, dt=dt,
                                                    min_tsep=min_tsep)
                le = float(estimate_lyapunov_from_curve(t_steps, div))
            elif algo_name == 'kantz':
                t_steps, div = lyapunov_kantz(data, m=m, tau=tau, dt=dt,
                                               min_tsep=min_tsep)
                le = float(estimate_lyapunov_from_curve(t_steps, div))
            elif algo_name == 'sano_sawada':
                spec = lyapunov_spectrum(data, m=m, tau=tau, dt=dt, min_tsep=min_tsep)
                exps = spec['exponents']
                le = float(exps[0]) if len(exps) > 0 else float('nan')
            else:
                le = float('nan')
    except Exception:
        le = float('nan')
    return le, time.time() - t0


def err_pct(le: float, lit: float) -> float:
    if not np.isfinite(le) or lit == 0:
        return float('nan')
    return abs(le - lit) / abs(lit) * 100


# ----------------------------------------------------------------------
# Test A — Map systems (Benettin yok)
# ----------------------------------------------------------------------

def test_a_maps():
    log("\n" + "=" * 92)
    log("TEST A — MAP SYSTEMS (discrete) | Benettin uygulanamaz")
    log("=" * 92)
    log(f"{'System':>10s} | {'Lit':>8s} | "
        f"{'Wolf':>8s}/{'Err%':>6s} | "
        f"{'Ros':>8s}/{'Err%':>6s} | "
        f"{'Kantz':>8s}/{'Err%':>6s} | "
        f"{'SanoSaw':>8s}/{'Err%':>6s}")
    log("-" * 92)

    rows = []
    for spec in MAP_SYSTEMS:
        ts = spec['gen']()
        data = ts.data
        results = {}
        for algo in ['wolf', 'rosenstein', 'kantz', 'sano_sawada']:
            le, _ = run_algo(algo, data, dt=ts.dt)
            results[algo] = (le, err_pct(le, spec['lit']))

        log(f"{spec['name']:>10s} | {spec['lit']:>8.4f} | "
            f"{results['wolf'][0]:>8.4f}/{results['wolf'][1]:>5.1f}% | "
            f"{results['rosenstein'][0]:>8.4f}/{results['rosenstein'][1]:>5.1f}% | "
            f"{results['kantz'][0]:>8.4f}/{results['kantz'][1]:>5.1f}% | "
            f"{results['sano_sawada'][0]:>8.4f}/{results['sano_sawada'][1]:>5.1f}%")
        rows.append({'name': spec['name'], 'lit': spec['lit'], **results})
    return rows


# ----------------------------------------------------------------------
# Test B — ODE known (Benettin gold standard)
# ----------------------------------------------------------------------

def test_b_ode_known():
    log("\n" + "=" * 105)
    log("TEST B — ODE KNOWN (denklem bilinen) | Benettin gold standard")
    log("=" * 105)
    log(f"{'System':>10s} | {'Lit':>8s} | "
        f"{'Wolf':>8s}/{'Err%':>6s} | "
        f"{'Ros':>8s}/{'Err%':>6s} | "
        f"{'Kantz':>8s}/{'Err%':>6s} | "
        f"{'SanoSaw':>8s}/{'Err%':>6s} | "
        f"{'Benett':>8s}/{'Err%':>6s}")
    log("-" * 105)

    rows = []
    for spec in ODE_SYSTEMS:
        ts = spec['gen']()
        data = ts.data[spec['transient']:]
        ode_extra = spec.get('extra', {})
        results = {}
        for algo in ['wolf', 'rosenstein', 'kantz', 'sano_sawada', 'benettin']:
            le, _ = run_algo(
                algo, data, dt=spec['dt'],
                system_key=spec['system_key'], ode_extra=ode_extra,
                t_total=spec['t_total'], transient_steps=spec['transient'],
            )
            results[algo] = (le, err_pct(le, spec['lit']))

        log(f"{spec['name']:>10s} | {spec['lit']:>8.4f} | "
            f"{results['wolf'][0]:>8.4f}/{results['wolf'][1]:>5.1f}% | "
            f"{results['rosenstein'][0]:>8.4f}/{results['rosenstein'][1]:>5.1f}% | "
            f"{results['kantz'][0]:>8.4f}/{results['kantz'][1]:>5.1f}% | "
            f"{results['sano_sawada'][0]:>8.4f}/{results['sano_sawada'][1]:>5.1f}% | "
            f"{results['benettin'][0]:>8.4f}/{results['benettin'][1]:>5.1f}%")
        rows.append({'name': spec['name'], 'lit': spec['lit'], **results})
    return rows


# ----------------------------------------------------------------------
# Test C — Time-series (CSV mode, sistem bilinmiyor)
# ----------------------------------------------------------------------

def test_c_timeseries():
    log("\n" + "=" * 92)
    log("TEST C — TIME-SERIES (CSV mode) | Benettin n/a (sistem bilinmiyor varsayimi)")
    log("=" * 92)
    log("ODE'lerden data uretiliyor ama metadata atilarak sadece x(t) ele aliniyor.")
    log("")
    log(f"{'System':>10s} | {'Lit':>8s} | "
        f"{'Wolf':>8s}/{'Err%':>6s} | "
        f"{'Ros':>8s}/{'Err%':>6s} | "
        f"{'Kantz':>8s}/{'Err%':>6s} | "
        f"{'SanoSaw':>8s}/{'Err%':>6s}")
    log("-" * 92)

    rows = []
    for spec in ODE_SYSTEMS:
        ts = spec['gen']()
        data = ts.data[spec['transient']:]
        # NOT: system_key=None geciliyor, Benettin de hesaplanmiyor
        results = {}
        for algo in ['wolf', 'rosenstein', 'kantz', 'sano_sawada']:
            le, _ = run_algo(algo, data, dt=spec['dt'])
            results[algo] = (le, err_pct(le, spec['lit']))

        log(f"{spec['name']:>10s} | {spec['lit']:>8.4f} | "
            f"{results['wolf'][0]:>8.4f}/{results['wolf'][1]:>5.1f}% | "
            f"{results['rosenstein'][0]:>8.4f}/{results['rosenstein'][1]:>5.1f}% | "
            f"{results['kantz'][0]:>8.4f}/{results['kantz'][1]:>5.1f}% | "
            f"{results['sano_sawada'][0]:>8.4f}/{results['sano_sawada'][1]:>5.1f}%")
        rows.append({'name': spec['name'], 'lit': spec['lit'], **results})
    return rows


# ----------------------------------------------------------------------
# Ozet ve oneriler
# ----------------------------------------------------------------------

def algo_summary(rows: list, algos: list, label: str):
    """Veri tipi icin her algoritmanin ortalama / median hatasini hesaplar."""
    log("")
    log(f"--- {label}: ortalama hata (en dusuk en iyi) ---")
    log(f"{'Algorithm':>15s} | {'Mean Err%':>10s} | {'Median Err%':>11s} | {'Max Err%':>10s} | {'<10% sayisi':>12s}")
    log("-" * 75)

    summary = []
    for algo in algos:
        errs = [r[algo][1] for r in rows if np.isfinite(r[algo][1])]
        if not errs:
            continue
        errs_arr = np.array(errs)
        n_under10 = int(np.sum(errs_arr < 10))
        summary.append({
            'algo': algo,
            'mean': float(errs_arr.mean()),
            'median': float(np.median(errs_arr)),
            'max': float(errs_arr.max()),
            'n_under10': n_under10,
            'n_total': len(rows),
        })

    summary.sort(key=lambda s: s['mean'])
    for s in summary:
        log(f"{s['algo']:>15s} | {s['mean']:>9.1f}% | {s['median']:>10.1f}% | "
            f"{s['max']:>9.1f}% | {s['n_under10']:>5d}/{s['n_total']}")
    return summary


def main():
    log("=" * 92)
    log("ALGORITMA KARSILASTIRMA MATRISI — Map / ODE-known / Time-series x 5 algoritma")
    log("=" * 92)

    total_start = time.time()

    a_rows = test_a_maps()
    a_summary = algo_summary(a_rows,
                              ['wolf', 'rosenstein', 'kantz', 'sano_sawada'],
                              "Test A (Maps)")

    b_rows = test_b_ode_known()
    b_summary = algo_summary(b_rows,
                              ['wolf', 'rosenstein', 'kantz', 'sano_sawada', 'benettin'],
                              "Test B (ODE known)")

    c_rows = test_c_timeseries()
    c_summary = algo_summary(c_rows,
                              ['wolf', 'rosenstein', 'kantz', 'sano_sawada'],
                              "Test C (Time-series CSV mode)")

    # Final oneriler
    log("\n" + "=" * 92)
    log("ONERI MATRISI — Veri tipine gore en iyi algoritma")
    log("=" * 92)
    log(f"{'Veri tipi':>30s} | {'1.':>15s} | {'2.':>15s} | {'3.':>15s}")
    log("-" * 92)
    for label, summ in [("Map (discrete)",     a_summary),
                        ("ODE (denklem bilinen)", b_summary),
                        ("Time-series (CSV)",    c_summary)]:
        if len(summ) >= 3:
            s0 = "{0}({1:.1f}%)".format(summ[0]['algo'], summ[0]['mean'])
            s1 = "{0}({1:.1f}%)".format(summ[1]['algo'], summ[1]['mean'])
            s2 = "{0}({1:.1f}%)".format(summ[2]['algo'], summ[2]['mean'])
            log(f"{label:>30s} | {s0:>15s} | {s1:>15s} | {s2:>15s}")

    total = time.time() - total_start
    log("")
    log(f"Toplam sure: {total:.1f}s ({total/60:.1f} dk)")

    output_path = os.path.join(os.path.dirname(__file__), 'test_algorithm_comparison_sonuc.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(OUTPUT_LINES) + "\n")
    print(f"\nSonuclar: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
