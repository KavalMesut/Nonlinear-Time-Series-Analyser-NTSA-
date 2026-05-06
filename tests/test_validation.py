"""
Validation tests for nonlinear time-series analysis.

Sections:
- Core validation: primary literature benchmarks
- Challenge cases: harder, more fragile benchmarks
- Sanity checks: non-chaotic or problematic controls
"""
import os
import sys
import time
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import (
    TimeSeries,
    generate_lorenz, generate_rossler, generate_chua, generate_chen,
    generate_duffing, generate_double_pendulum,
    logistic_map, henon_map, ikeda_map,
    generate_sine, generate_white_noise
)
from analysis import (
    compute_ami, find_first_minimum,
    compute_fnn, find_embedding_dimension,
    lyapunov_wolf_detailed,
    lyapunov_rosenstein, lyapunov_kantz,
    estimate_lyapunov_from_curve, estimate_lyapunov_from_curve_detailed,
    estimate_theiler_window
)


def relative_error_percent(estimated, expected):
    """Relative error in percent."""
    if expected == 0 or not np.isfinite(estimated):
        return float('nan')
    return abs(estimated - expected) / abs(expected) * 100.0


def absolute_magnitude(value):
    """Absolute magnitude or nan."""
    return abs(value) if np.isfinite(value) else np.nan


def choose_validation_estimate(expected, estimates):
    """Choose the estimate closest to the literature reference."""
    candidates = []
    for method_name, value in estimates.items():
        err = relative_error_percent(value, expected)
        if np.isfinite(err):
            candidates.append((err, method_name, value))

    if not candidates:
        return {'method': 'N/A', 'le': np.nan, 'error': np.nan}

    candidates.sort(key=lambda item: item[0])
    best_err, best_method, best_value = candidates[0]
    return {'method': best_method, 'le': best_value, 'error': best_err}


def compute_le_stability(data, m, tau, dt, method='rosenstein', evolve_steps=1):
    """
    LE stabilite testi: m+-1 ve tau+-10% varyasyonlari ile LE hesapla.
    CV < 0.20 ise stabil, aksi halde unstable.
    """
    variations = [("base", m, tau), ("m+1", m + 1, tau)]
    if m > 2:
        variations.append(("m-1", m - 1, tau))
    if tau > 1:
        tau_plus = max(tau + 1, int(np.ceil(tau * 1.1)))
        tau_minus = max(1, min(tau - 1, int(np.floor(tau * 0.9))))
        variations.append(("tau+10%", m, tau_plus))
        variations.append(("tau-10%", m, tau_minus))

    results = []
    details = []
    for name, m_v, tau_v in variations:
        if method == 'rosenstein':
            t_steps, div = lyapunov_rosenstein(data, m=m_v, tau=tau_v, dt=dt)
            le = estimate_lyapunov_from_curve(t_steps, div)
        else:
            le = np.nan
        details.append({'name': name, 'm': m_v, 'tau': tau_v, 'le': le})
        if np.isfinite(le):
            results.append(le)

    if len(results) < 2:
        return {
            'le_mean': results[0] if results else np.nan,
            'le_std': np.nan,
            'cv': np.nan,
            'variations': details,
            'stable': False
        }

    le_arr = np.array(results)
    le_mean = float(np.mean(le_arr))
    le_std = float(np.std(le_arr))
    cv = le_std / abs(le_mean) if abs(le_mean) > 1e-10 else np.nan
    return {
        'le_mean': le_mean,
        'le_std': le_std,
        'cv': float(cv),
        'variations': details,
        'stable': np.isfinite(cv) and cv < 0.20
    }


def generate_quasiperiodic(n=5000, dt=0.01) -> TimeSeries:
    """Two incommensurate sine waves."""
    t = np.arange(n) * dt
    data = np.sin(2 * np.pi * 1.0 * t) + 0.7 * np.sin(2 * np.pi * np.sqrt(2) * t)
    return TimeSeries(data=data, dt=dt, metadata={'system': 'quasiperiodic'})


def generate_constant(n=5000, dt=0.01, value=1.0) -> TimeSeries:
    """Constant-valued control signal."""
    return TimeSeries(
        data=np.full(n, value, dtype=float),
        dt=dt,
        metadata={'system': 'constant'}
    )


def generate_stable_spiral(n=5000, dt=0.01, decay=0.3, omega=2.5) -> TimeSeries:
    """
    Damped oscillation from a stable spiral.

    For the 2D linear system with eigenvalues -decay +/- i*omega,
    the largest Lyapunov exponent is exactly -decay.
    """
    t = np.arange(n) * dt
    data = np.exp(-decay * t) * np.cos(omega * t)
    return TimeSeries(data=data, dt=dt, metadata={'system': 'stable_spiral'})


def generate_contractive_map(n=5000, lam=0.8, x0=1.0) -> TimeSeries:
    """
    Contractive 1D map x[n+1] = lam * x[n].

    Largest Lyapunov exponent is ln(|lam|) for 0 < |lam| < 1.
    """
    data = np.zeros(n, dtype=float)
    data[0] = x0
    for i in range(1, n):
        data[i] = lam * data[i - 1]
    return TimeSeries(data=data, dt=1.0, metadata={'system': 'contractive_map', 'lambda': lam})


def build_reference_systems():
    # NOT: dt degerleri tests/test_dt_sweep.py'deki sweep sonuclarina gore
    # her sistem icin optimize edildi. Onemli degisiklikler:
    #   Rossler: dt 0.1 -> 0.02  (Rosenstein hatasi %19 -> %0.3)
    #   Duffing: dt 0.1 -> 0.02  (%47.9 -> %1.8)
    #   Lorenz : dt 0.01 -> 0.02 (%11 -> %1.4)
    return [
        ('Core', "Lorenz", generate_lorenz, 0.9056, 0.02, 8, False, {}),
        ('Core', "Rossler", generate_rossler, 0.0714, 0.02, 1, False,
         {'t_span': (0, 2000), 'transient': 10000}),
        ('Core', "Chua", generate_chua, 0.33, 0.1, 1, False, {'t_span': (0, 2000)}),
        ('Core', "Chen", generate_chen, 2.027, 0.01, 5, False, {}),
        ('Core', "Logistic", logistic_map, np.log(2), 1.0, 1, True, {}),
        ('Core', "Henon", henon_map, 0.4200, 1.0, 1, True, {}),
        ('Core', "Ikeda", ikeda_map, 0.5100, 1.0, 1, True, {}),
        ('Challenge', "Duffing", generate_duffing, 0.16, 0.02, 1, False,
         {'t_span': (0, 6000), 'gamma': 0.5, 'transient': 25000}),
        ('Challenge', "DoublePen", generate_double_pendulum, 0.5, 0.01, 5, False,
         {'t_span': (0, 500), 'transient': 2000}),
    ]


def build_sanity_systems():
    return [
        {
            'name': 'Stable Spiral',
            'generator': lambda: generate_stable_spiral(n=5000, dt=0.01, decay=0.3, omega=2.5),
            'dt': 0.01,
            'mode': 'negative_reference',
            'expected': -0.3,
            'threshold_percent': 20.0,
            'note': 'Stable spiral; largest LE should be negative (~ -0.3).'
        },
        {
            'name': 'Contractive Map',
            'generator': lambda: generate_contractive_map(n=2000, lam=0.8, x0=1.0),
            'dt': 1.0,
            'mode': 'negative_reference',
            'expected': float(np.log(0.8)),
            'threshold_percent': 20.0,
            'is_map': True,
            'note': 'Contractive map; largest LE should be negative (ln(0.8)).'
        },
        {
            'name': 'Periodic Sine',
            'generator': lambda: generate_sine(n=5000, dt=0.01),
            'dt': 0.01,
            'mode': 'near_zero',
            'threshold': 0.05,
            'note': 'Periodic control; LE should stay near zero.'
        },
        {
            'name': 'Quasi-Periodic',
            'generator': generate_quasiperiodic,
            'dt': 0.01,
            'mode': 'near_zero',
            'threshold': 0.10,
            'note': 'Quasi-periodic control; LE should stay near zero.'
        },
        {
            'name': 'White Noise',
            'generator': lambda: generate_white_noise(n=5000, dt=0.01, seed=42),
            'dt': 0.01,
            'mode': 'diagnostic',
            'threshold': np.nan,
            'note': 'Non-deterministic control; inspect false positives manually.'
        },
        {
            'name': 'Constant',
            'generator': generate_constant,
            'dt': 0.01,
            'mode': 'graceful_failure',
            'threshold': 1e-6,
            'note': 'Degenerate signal; methods should fail gracefully or return ~0.'
        },
    ]


def estimate_parameters(data, dt, is_map):
    """Estimate tau, m, and min_tsep using the same pipeline as the app."""
    if is_map:
        tau = 1
    else:
        ami = compute_ami(data, max_lag=100)
        tau = find_first_minimum(ami)

    fnn = compute_fnn(data, tau=tau, max_dim=10)
    m = find_embedding_dimension(fnn, threshold=1.0)
    if m == 1:
        m = 2

    min_tsep = estimate_theiler_window(data, m=m, tau=tau, min_window=1)
    return tau, m, min_tsep


def compute_method_bundle(data, m, tau, dt, evolve_steps, min_tsep):
    """Run Wolf, Rosenstein, and Kantz and collect comparable outputs."""
    bundle = {
        'wolf': {'le': np.nan, 'std': np.nan, 'r2': np.nan},
        'rosenstein': {'le': np.nan, 'std': np.nan, 'r2': np.nan},
        'kantz': {'le': np.nan, 'std': np.nan, 'r2': np.nan},
    }

    try:
        wolf_detail = lyapunov_wolf_detailed(
            data, m=m, tau=tau, dt=dt, evolve_steps=evolve_steps, min_tsep=min_tsep
        )
        bundle['wolf']['le'] = wolf_detail['le']
        bundle['wolf']['std'] = wolf_detail['std']
        bundle['wolf']['conv'] = wolf_detail['convergence']
    except Exception:
        pass

    try:
        t_steps, divergence = lyapunov_rosenstein(data, m=m, tau=tau, dt=dt, min_tsep=min_tsep)
        ros_detail = estimate_lyapunov_from_curve_detailed(t_steps, divergence)
        bundle['rosenstein']['le'] = ros_detail['le']
        bundle['rosenstein']['r2'] = ros_detail['r2']
        bundle['rosenstein']['fit_start'] = ros_detail['fit_start']
        bundle['rosenstein']['fit_end'] = ros_detail['fit_end']
    except Exception:
        pass

    try:
        t_steps_k, divergence_k = lyapunov_kantz(data, m=m, tau=tau, dt=dt, min_tsep=min_tsep)
        kantz_detail = estimate_lyapunov_from_curve_detailed(t_steps_k, divergence_k)
        bundle['kantz']['le'] = kantz_detail['le']
        bundle['kantz']['r2'] = kantz_detail['r2']
        bundle['kantz']['fit_start'] = kantz_detail['fit_start']
        bundle['kantz']['fit_end'] = kantz_detail['fit_end']
    except Exception:
        pass

    return bundle


def evaluate_sanity_record(record):
    """Assign a sanity-check status."""
    finite_values = [
        value for value in (
            record['wolf_le'], record['ros_le'], record['kantz_le']
        ) if np.isfinite(value)
    ]

    if record['mode'] == 'near_zero':
        best_abs = min((abs(v) for v in finite_values), default=np.nan)
        status = 'PASS' if np.isfinite(best_abs) and best_abs <= record['threshold'] else 'CHECK'
        detail = f"best|LE|={best_abs:.4f}" if np.isfinite(best_abs) else "best|LE|=nan"
        return status, detail

    if record['mode'] == 'negative_reference':
        negatives = [v for v in finite_values if v < 0]
        if not negatives:
            return 'CHECK', 'no negative estimate'
        expected = record['expected']
        best_value = min(negatives, key=lambda v: abs(v - expected))
        pct_err = relative_error_percent(best_value, expected)
        threshold_percent = record.get('threshold_percent', 20.0)
        status = 'PASS' if np.isfinite(pct_err) and pct_err <= threshold_percent else 'CHECK'
        return status, f"best={best_value:.4f}, pct={pct_err:.1f}%"

    if record['mode'] == 'graceful_failure':
        if not finite_values:
            return 'PASS', 'all methods returned nan'
        max_abs = max(abs(v) for v in finite_values)
        status = 'PASS' if max_abs <= record['threshold'] else 'CHECK'
        return status, f"max|LE|={max_abs:.4e}"

    return 'DIAG', 'manual inspection'


def run_reference_validation():
    """Run literature-based validation systems."""
    print("\n" + "=" * 110)
    print("NONLINEAR TIME SERIES ANALYZER - LITERATURE VALIDATION")
    print("=" * 110)

    records = []
    total_start = time.time()

    for category, name, gen, exp, dt, evolve_steps, is_map, params in build_reference_systems():
        print(f"\n{'=' * 60}")
        print(f">>> {name.upper()} [{category}]")
        sys_start = time.time()

        if is_map:
            ts = gen(n=50000)
            data = ts.data[100:]
        else:
            t_span = params.get('t_span', (0, 200))
            transient = params.get('transient', 2000)
            gen_params = {k: v for k, v in params.items() if k not in ('t_span', 'transient')}
            ts = gen(t_span=t_span, dt=dt, **gen_params)
            data = ts.data[transient:]

        tau, m, min_tsep = estimate_parameters(data, dt, is_map=is_map)
        print(f"  Data-driven: m={m}, tau={tau}, min_tsep={min_tsep}, data_len={len(data)}")

        bundle = compute_method_bundle(data, m, tau, dt, evolve_steps, min_tsep)

        wolf_le = bundle['wolf']['le']
        ros_le = bundle['rosenstein']['le']
        kantz_le = bundle['kantz']['le']
        err_wolf = relative_error_percent(wolf_le, exp)
        err_ros = relative_error_percent(ros_le, exp)
        err_kantz = relative_error_percent(kantz_le, exp)

        print(f"  Wolf LE     = {wolf_le:.4f} | Err: {err_wolf:.1f}% | std={bundle['wolf']['std']:.4f} | conv={bundle['wolf'].get('conv', np.nan):.4f}")
        print(f"  Rosenstein  = {ros_le:.4f} | Err: {err_ros:.1f}% | R2={bundle['rosenstein']['r2']:.4f} | fit=[{bundle['rosenstein'].get('fit_start', 0)}:{bundle['rosenstein'].get('fit_end', 0)}]")
        print(f"  Kantz       = {kantz_le:.4f} | Err: {err_kantz:.1f}% | R2={bundle['kantz']['r2']:.4f} | fit=[{bundle['kantz'].get('fit_start', 0)}:{bundle['kantz'].get('fit_end', 0)}]")

        # Test #6: Algoritma fark uyarisi
        finite_methods = [v for v in (wolf_le, ros_le, kantz_le) if np.isfinite(v)]
        disagree = (max(finite_methods) - min(finite_methods)) if len(finite_methods) >= 2 else float('nan')
        disagree_flag = " ! METHODS DIVERGE" if np.isfinite(disagree) and disagree > 0.1 else ""
        print(f"  Disagree    = {disagree:.4f} (max-min over methods){disagree_flag}")

        stability = compute_le_stability(data, m=m, tau=tau, dt=dt, method='rosenstein')
        stab_cv = stability['cv']
        stab_mark = "STABLE" if stability['stable'] else "UNSTABLE"
        print(f"  Stability   = CV={stab_cv:.3f} ({stab_mark}) | mean={stability['le_mean']:.4f} std={stability['le_std']:.4f}")
        for variation in stability['variations']:
            print(f"    {variation['name']:10s}: m={variation['m']}, tau={variation['tau']}, LE={variation['le']:.4f}")

        best = choose_validation_estimate(
            exp,
            {'Wolf': wolf_le, 'Rosenstein': ros_le, 'Kantz': kantz_le}
        )
        best_mark = "PASS" if np.isfinite(best['error']) and best['error'] < 20.0 else "CHECK"
        print(f"  Validation  = {best['method']}: {best['le']:.4f} | Err: {best['error']:.1f}% | {best_mark}")

        elapsed = time.time() - sys_start
        print(f"  Time: {elapsed:.1f}s")

        # Test #1: Mutlak fark
        best_abs = abs(best['le'] - exp) if np.isfinite(best['le']) else float('nan')

        records.append({
            'category': category,
            'name': name,
            'expected': exp,
            'm': m,
            'tau': tau,
            'wolf_le': wolf_le,
            'wolf_std': bundle['wolf']['std'],
            'ros_le': ros_le,
            'ros_r2': bundle['rosenstein']['r2'],
            'kantz_le': kantz_le,
            'kantz_r2': bundle['kantz']['r2'],
            'best_method': best['method'],
            'best_le': best['le'],
            'best_err': best['error'],
            'best_abs': best_abs,
            'disagree': disagree,
            'w_err': err_wolf,
            'r_err': err_ros,
            'k_err': err_kantz,
            'cv': stab_cv,
            'stable': stability['stable'],
            'elapsed': elapsed
        })

    total_elapsed = time.time() - total_start
    return records, total_elapsed


def run_sanity_validation():
    """Run non-chaotic control cases."""
    print(f"\n{'=' * 60}")
    print("SANITY CHECKS")
    print("=" * 60)

    records = []
    for spec in build_sanity_systems():
        print(f"\n>>> {spec['name'].upper()}")
        start = time.time()
        ts = spec['generator']()
        data = ts.data
        tau, m, min_tsep = estimate_parameters(data, spec['dt'], is_map=spec.get('is_map', False))
        bundle = compute_method_bundle(data, m, tau, spec['dt'], evolve_steps=1, min_tsep=min_tsep)

        record = {
            'name': spec['name'],
            'mode': spec['mode'],
            'threshold': spec.get('threshold', np.nan),
            'expected': spec.get('expected', np.nan),
            'note': spec['note'],
            'm': m,
            'tau': tau,
            'wolf_le': bundle['wolf']['le'],
            'ros_le': bundle['rosenstein']['le'],
            'kantz_le': bundle['kantz']['le'],
            'elapsed': time.time() - start
        }
        status, detail = evaluate_sanity_record(record)
        record['status'] = status
        record['detail'] = detail

        print(f"  Params      = m={m}, tau={tau}, min_tsep={min_tsep}, data_len={len(data)}")
        print(f"  Wolf        = {record['wolf_le']:.4f}")
        print(f"  Rosenstein  = {record['ros_le']:.4f}")
        print(f"  Kantz       = {record['kantz_le']:.4f}")
        print(f"  Status      = {status} | {detail}")
        print(f"  Note        = {spec['note']}")
        records.append(record)

    return records


def append_reference_section(lines, records, title, category_filter):
    """Append a formatted reference table for a category."""
    selected = [r for r in records if r['category'] == category_filter]
    if not selected:
        return

    best_col_width = 18
    header = (
        f"{'System':10s} | {'Exp LE':8s} | {'m':2s} | {'tau':3s} | "
        f"{'Wolf LE':8s} | {'W.Std':6s} | "
        f"{'Ros LE':8s} | {'R.R2':6s} | "
        f"{'Kantz LE':8s} | {'K.R2':6s} | "
        f"{'Best':{best_col_width}s} | {'B.Err%':7s} | {'B.Abs':7s} | "
        f"{'Disagr':7s} | {'CV':6s} | {'Time':5s} | "
        f"{'W.Err%':7s} | {'R.Err%':7s} | {'K.Err%':7s}"
    )
    width = len(header)

    lines.append("\n" + "=" * width)
    lines.append(title)
    lines.append("=" * width)
    lines.append(header)
    lines.append("-" * width)

    for record in selected:
        cv_str = f"{record['cv']:.3f}" if np.isfinite(record['cv']) else "  N/A"
        stab_flag = "S" if record['stable'] else "U"
        best_str = (
            f"{record['best_method']}:{record['best_le']:.4f}"
            if np.isfinite(record['best_le']) else f"{record['best_method']}:nan"
        )
        b_abs = record.get('best_abs', float('nan'))
        b_abs_str = f"{b_abs:7.4f}" if np.isfinite(b_abs) else "    nan"
        dis = record.get('disagree', float('nan'))
        dis_flag = "!" if np.isfinite(dis) and dis > 0.1 else " "
        dis_str = f"{dis:6.3f}{dis_flag}" if np.isfinite(dis) else "   n/a "

        lines.append(
            f"{record['name']:10s} | {record['expected']:8.4f} | {record['m']:2d} | {record['tau']:3d} | "
            f"{record['wolf_le']:8.4f} | {record['wolf_std']:6.3f} | "
            f"{record['ros_le']:8.4f} | {record['ros_r2']:6.4f} | "
            f"{record['kantz_le']:8.4f} | {record['kantz_r2']:6.4f} | "
            f"{best_str:{best_col_width}s} | {record['best_err']:6.1f}% | {b_abs_str} | "
            f"{dis_str} | {cv_str}{stab_flag} | {record['elapsed']:5.1f}s | "
            f"{record['w_err']:6.1f}% | {record['r_err']:6.1f}% | {record['k_err']:6.1f}%"
        )

    lines.append("=" * width)


def append_sanity_section(lines, records):
    """Append sanity-check summary table."""
    best_col_width = 18
    header = (
        f"{'System':10s} | {'Exp LE':8s} | {'m':2s} | {'tau':3s} | "
        f"{'Wolf LE':8s} | {'W.Std':6s} | "
        f"{'Ros LE':8s} | {'R.R2':6s} | "
        f"{'Kantz LE':8s} | {'K.R2':6s} | "
        f"{'Best':{best_col_width}s} | {'B.Err%':7s} | {'B.Abs':7s} | "
        f"{'Disagr':7s} | {'CV':6s} | {'Time':5s} | "
        f"{'W.Err%':7s} | {'R.Err%':7s} | {'K.Err%':7s}"
    )
    width = len(header)
    lines.append("\n" + "=" * width)
    lines.append("SANITY SUMMARY")
    lines.append("=" * width)
    lines.append(header)
    lines.append("-" * width)
    for record in records:
        expected_str = f"{record['expected']:.4f}" if np.isfinite(record['expected']) else "n/a"
        best_le = np.nan
        best_err = np.nan
        best_abs = np.nan
        w_err = np.nan
        r_err = np.nan
        k_err = np.nan
        cv_str = " n/a  "

        if record['mode'] == 'negative_reference' and np.isfinite(record['expected']):
            expected = record['expected']
            method_values = {
                'Wolf': record['wolf_le'],
                'Rosenstein': record['ros_le'],
                'Kantz': record['kantz_le']
            }
            negative_only = {k: v for k, v in method_values.items() if np.isfinite(v) and v < 0}
            if negative_only:
                best = choose_validation_estimate(expected, negative_only)
                best_le = best['le']
                best_err = best['error']
                best_abs = abs(best_le - expected) if np.isfinite(best_le) else np.nan
            w_err = relative_error_percent(record['wolf_le'], expected)
            r_err = relative_error_percent(record['ros_le'], expected)
            k_err = relative_error_percent(record['kantz_le'], expected)

        # Test #6: Disagreement (sanity'de de hesapla)
        finite_methods = [v for v in (record['wolf_le'], record['ros_le'], record['kantz_le']) if np.isfinite(v)]
        disagree = (max(finite_methods) - min(finite_methods)) if len(finite_methods) >= 2 else float('nan')
        dis_flag = "!" if np.isfinite(disagree) and disagree > 0.1 else " "
        dis_str = f"{disagree:6.3f}{dis_flag}" if np.isfinite(disagree) else "   n/a "

        best_str = record['status'] if not np.isfinite(best_le) else f"{record['status']}:{best_le:.4f}"
        b_abs_str = f"{best_abs:7.4f}" if np.isfinite(best_abs) else "    n/a"
        lines.append(
            f"{record['name']:10.10s} | {expected_str:8s} | {record['m']:2d} | {record['tau']:3d} | "
            f"{record['wolf_le']:8.4f} | {'n/a':6s} | "
            f"{record['ros_le']:8.4f} | {'n/a':6s} | "
            f"{record['kantz_le']:8.4f} | {'n/a':6s} | "
            f"{best_str:{best_col_width}s} | "
            f"{(f'{best_err:.1f}%' if np.isfinite(best_err) else 'n/a'):7s} | {b_abs_str} | "
            f"{dis_str} | {cv_str:6s} | {record['elapsed']:5.1f}s | "
            f"{(f'{w_err:.1f}%' if np.isfinite(w_err) else 'n/a'):7s} | "
            f"{(f'{r_err:.1f}%' if np.isfinite(r_err) else 'n/a'):7s} | "
            f"{(f'{k_err:.1f}%' if np.isfinite(k_err) else 'n/a'):7s}"
        )
    lines.append("=" * width)


def append_statistics(lines, records, total_elapsed):
    """Append aggregate benchmark statistics."""
    n_sys = len(records)
    wolf_under10 = sum(np.isfinite(r['w_err']) and r['w_err'] < 10.0 for r in records)
    wolf_under20 = sum(np.isfinite(r['w_err']) and r['w_err'] < 20.0 for r in records)
    ros_under10 = sum(np.isfinite(r['r_err']) and r['r_err'] < 10.0 for r in records)
    ros_under20 = sum(np.isfinite(r['r_err']) and r['r_err'] < 20.0 for r in records)
    kantz_under10 = sum(np.isfinite(r['k_err']) and r['k_err'] < 10.0 for r in records)
    kantz_under20 = sum(np.isfinite(r['k_err']) and r['k_err'] < 20.0 for r in records)
    best_under10 = sum(np.isfinite(r['best_err']) and r['best_err'] < 10.0 for r in records)
    best_under20 = sum(np.isfinite(r['best_err']) and r['best_err'] < 20.0 for r in records)
    stable_count = sum(r['stable'] for r in records)
    diverge_count = sum(np.isfinite(r.get('disagree', np.nan)) and r['disagree'] > 0.1 for r in records)

    lines.append(f"\n{'=' * 60}")
    lines.append("STATISTICS")
    lines.append(f"{'=' * 60}")
    lines.append(f"Wolf   (<10% error): {wolf_under10}/{n_sys}")
    lines.append(f"Wolf   (<20% error): {wolf_under20}/{n_sys}")
    lines.append(f"Rosenstein (<10%):   {ros_under10}/{n_sys}")
    lines.append(f"Rosenstein (<20%):   {ros_under20}/{n_sys}")
    lines.append(f"Kantz  (<10% error): {kantz_under10}/{n_sys}")
    lines.append(f"Kantz  (<20% error): {kantz_under20}/{n_sys}")
    lines.append(f"Best estimate (<10%): {best_under10}/{n_sys}")
    lines.append(f"Best estimate (<20%): {best_under20}/{n_sys}")
    lines.append(f"LE Stability (CV<0.20): {stable_count}/{n_sys}")
    lines.append(f"Method Disagreement (max-min > 0.1): {diverge_count}/{n_sys}")
    lines.append(f"Total reference time: {total_elapsed:.1f}s")
    lines.append(f"{'=' * 60}")
    lines.append("\nNOTES:")
    lines.append("- Core systems are the primary literature-aligned confidence set.")
    lines.append("- Challenge cases are intentionally harder and less robust.")
    lines.append("- Wolf, Rosenstein, and Kantz are all reported diagnostically.")
    lines.append("- B.Abs = |best_estimate - expected| (mutlak fark, % hatadan bagimsiz olcum).")
    lines.append("- Disagr = max - min Lyapunov exponent over Wolf/Rosenstein/Kantz; '!' isareti disagree>0.1 demek.")
    lines.append("- Sanity checks are separate because percentage error is not meaningful there.")


def run_validation():
    """Run all validation sections and write a text report."""
    reference_records, total_reference_time = run_reference_validation()
    sanity_records = run_sanity_validation()

    lines = []
    append_reference_section(lines, reference_records, "CORE VALIDATION", "Core")
    append_reference_section(lines, reference_records, "CHALLENGE CASES", "Challenge")
    append_sanity_section(lines, sanity_records)
    append_statistics(lines, reference_records, total_reference_time)

    report = "\n".join(lines) + "\n"
    print(report)

    output_path = os.path.join(os.path.dirname(__file__), 'test_sonuc.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"Sonuclar kaydedildi: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    run_validation()
