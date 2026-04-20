"""
Validation tests for 10 chaotic systems.
5 Continuous ODE Systems, 5 Discrete Maps.

Her iki algoritma (Wolf ve Rosenstein) bagimsiz olarak test edilir,
sonuclar tek tabloda yan yana sunulur. Hangisinin kullanilacagi
kullanicinin kararindadir (UI'da elle secilir).

Constraints:
1. m and tau must be purely data-driven (AMI and FNN).
2. LE stability check: m+-1, tau+-10% variations (CV metric).

Outputs:
- Wolf LE with standard deviation and convergence metric
- Rosenstein LE with R^2 fit quality
- LE stability (CV) for Rosenstein
- Comparative summary table
"""
import numpy as np
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import (
    generate_lorenz, generate_rossler, generate_chua, generate_chen, generate_duffing,
    logistic_map, henon_map, tent_map, sine_map, ikeda_map
)
from analysis import (
    compute_ami, find_first_minimum,
    compute_fnn, find_embedding_dimension,
    lyapunov_wolf, lyapunov_wolf_detailed,
    lyapunov_rosenstein, estimate_lyapunov_from_curve,
    estimate_lyapunov_from_curve_detailed
)


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
            le = lyapunov_wolf(data, m=m_v, tau=tau_v, dt=dt, evolve_steps=evolve_steps)
        details.append({'name': name, 'm': m_v, 'tau': tau_v, 'le': le})
        if np.isfinite(le):
            results.append(le)

    if len(results) < 2:
        return {'le_mean': results[0] if results else np.nan,
                'le_std': np.nan, 'cv': np.nan, 'variations': details, 'stable': False}

    le_arr = np.array(results)
    le_mean = float(np.mean(le_arr))
    le_std = float(np.std(le_arr))
    cv = le_std / abs(le_mean) if abs(le_mean) > 1e-10 else np.nan
    return {'le_mean': le_mean, 'le_std': le_std, 'cv': float(cv),
            'variations': details, 'stable': np.isfinite(cv) and cv < 0.20}


def run_validation():
    print("\n" + "=" * 110)
    print("NONLINEAR TIME SERIES ANALYZER - 10 SYSTEM VALIDATION")
    print("=" * 110)
    
    total_start = time.time()

    # (Name, Generator, Expected_LE, dt, evolve_steps, is_map, extra_params)
    # extra_params may contain 'transient' key for ODE systems (default: 2000)
    systems = [
        ("Lorenz",   generate_lorenz,  0.9056, 0.01, 8,  False, {}),
        ("Rossler",  generate_rossler, 0.0714, 0.1,  1,  False, {'t_span': (0, 2000)}),
        ("Chua",     generate_chua,    0.33,   0.1,  1,  False, {'t_span': (0, 2000)}),
        ("Chen",     generate_chen,    2.027,  0.01, 5,  False, {}),
        ("Duffing",  generate_duffing, 0.16,   0.1,  1,  False, {'t_span': (0, 6000), 'gamma': 0.5, 'transient': 5000}),
        ("Logistic", logistic_map,     np.log(2), 1.0, 1, True, {}),
        ("Henon",    henon_map,        0.4200, 1.0,  1,  True, {}),
        ("Tent",     tent_map,         np.log(2), 1.0, 1, True, {}),
        ("Sine Map", sine_map,         0.6931, 1.0,  1,  True, {}),
        ("Ikeda",    ikeda_map,        0.5100, 1.0,  1,  True, {}),
    ]

    summary = []

    for name, gen, exp, dt, ev, is_map, params in systems:
        print(f"\n{'='*60}")
        print(f">>> {name.upper()}")
        sys_start = time.time()
        
        if is_map:
            ts = gen(n=50000)
            data = ts.data[100:]
            tau = 1
        else:
            t_span = params.get('t_span', (0, 200))
            transient = params.get('transient', 2000)
            gen_params = {k: v for k, v in params.items() if k not in ('t_span', 'transient')}
            ts = gen(t_span=t_span, dt=dt, **gen_params)
            data = ts.data[transient:]
            ami = compute_ami(data, max_lag=100)
            tau = find_first_minimum(ami)
            
        fnn = compute_fnn(data, tau=tau, max_dim=10)
        m = find_embedding_dimension(fnn, threshold=1.0)
        
        if m == 1 and is_map:
            m = 2
            print(f"  FNN gave m=1, forced to m=2 for Wolf analysis")
        
        print(f"  Data-driven: m={m}, tau={tau}, data_len={len(data)}")
        
        # --- Wolf Detailed ---
        wolf_detail = lyapunov_wolf_detailed(
            data, m=m, tau=tau, dt=dt, evolve_steps=ev
        )
        calc_wolf = wolf_detail['le']
        wolf_std = wolf_detail['std']
        wolf_conv = wolf_detail['convergence']
        
        if exp != 0 and np.isfinite(calc_wolf):
            err_wolf = abs(calc_wolf - exp) / abs(exp) * 100
        else:
            err_wolf = float('nan')
        
        print(f"  Wolf LE     = {calc_wolf:.4f} | Err: {err_wolf:.1f}% | std={wolf_std:.4f} | conv={wolf_conv:.4f}")
        
        # --- Rosenstein Detailed ---
        t_steps, divergence = lyapunov_rosenstein(data, m=m, tau=tau, dt=dt)
        ros_detail = estimate_lyapunov_from_curve_detailed(t_steps, divergence)
        calc_ros = ros_detail['le']
        ros_r2 = ros_detail['r2']
        
        if exp != 0 and np.isfinite(calc_ros):
            err_ros = abs(calc_ros - exp) / abs(exp) * 100
        else:
            err_ros = float('nan')
        
        print(f"  Rosenstein  = {calc_ros:.4f} | Err: {err_ros:.1f}% | R2={ros_r2:.4f} | fit=[{ros_detail['fit_start']}:{ros_detail['fit_end']}]")
        
        # --- LE Stabilite Testi (Rosenstein) ---
        stability = compute_le_stability(data, m=m, tau=tau, dt=dt, method='rosenstein')
        stab_cv = stability['cv']
        stab_mark = "STABLE" if stability['stable'] else "UNSTABLE"
        print(f"  Stability   = CV={stab_cv:.3f} ({stab_mark})"
              f" | mean={stability['le_mean']:.4f} std={stability['le_std']:.4f}")
        for v in stability['variations']:
            print(f"    {v['name']:10s}: m={v['m']}, tau={v['tau']}, LE={v['le']:.4f}")
        
        elapsed = time.time() - sys_start
        print(f"  Time: {elapsed:.1f}s")
        
        summary.append((name, exp, m, tau, is_map,
                         calc_wolf, err_wolf, wolf_std,
                         calc_ros, err_ros, ros_r2,
                         stab_cv, stability['stable'], elapsed))

    # ===================== SUMMARY TABLE =====================
    total_elapsed = time.time() - total_start
    
    # Tablo satirlarini hem ekrana yaz hem dosyaya kaydet
    lines = []
    
    def out(s=""):
        print(s)
        lines.append(s)
    
    out("\n" + "=" * 130)
    out("SUMMARY: WOLF vs ROSENSTEIN (secim kullaniciya aittir)")
    out("=" * 130)
    out(f"{'System':10s} | {'Exp LE':8s} | {'m':2s} | {'tau':3s} | "
        f"{'Wolf LE':8s} | {'W.Std':6s} | "
        f"{'Ros LE':8s} | {'R.R2':6s} | "
        f"{'CV':6s} | {'Time':5s} | "
        f"{'W.Err%':7s} | {'R.Err%':7s}")
    out("-" * 130)
    
    wolf_under10 = 0
    wolf_under20 = 0
    ros_under10 = 0
    ros_under20 = 0
    stable_count = 0
    
    for (name, exp, m, tau, is_map,
         wolf, w_err, w_std,
         ros, r_err, r_r2,
         s_cv, s_stable, elapsed) in summary:
        
        if np.isfinite(w_err) and w_err < 10.0:
            wolf_under10 += 1
        if np.isfinite(w_err) and w_err < 20.0:
            wolf_under20 += 1
        if np.isfinite(r_err) and r_err < 10.0:
            ros_under10 += 1
        if np.isfinite(r_err) and r_err < 20.0:
            ros_under20 += 1
        if s_stable:
            stable_count += 1
        
        cv_str = f"{s_cv:.3f}" if np.isfinite(s_cv) else "  N/A"
        stab_flag = "S" if s_stable else "U"
        
        out(f"{name:10s} | {exp:8.4f} | {m:2d} | {tau:3d} | "
            f"{wolf:8.4f} | {w_std:6.3f} | "
            f"{ros:8.4f} | {r_r2:6.4f} | "
            f"{cv_str}{stab_flag} | {elapsed:5.1f}s | "
            f"{w_err:6.1f}% | {r_err:6.1f}%")
    
    out("=" * 130)
    
    # ===================== STATISTICS =====================
    out(f"\n{'='*60}")
    out("STATISTICS")
    out(f"{'='*60}")
    out(f"Wolf   (<10% error): {wolf_under10}/10")
    out(f"Wolf   (<20% error): {wolf_under20}/10")
    out(f"Rosenstein (<10%):   {ros_under10}/10")
    out(f"Rosenstein (<20%):   {ros_under20}/10")
    out(f"LE Stability (CV<0.20): {stable_count}/10")
    out(f"Total time: {total_elapsed:.1f}s")
    out(f"{'='*60}")
    
    out(f"\nNOTES:")
    out(f"- Her iki algoritma bagimsiz olarak raporlanir, secim kullaniciya aittir.")
    out(f"- Wolf: ODE sistemlerinde replacement bias nedeniyle overestimate yapabilir.")
    out(f"- Rosenstein: Map'lerde doyum (saturation) nedeniyle underestimate yapabilir.")
    out(f"- CV (varyasyon katsayisi): m+-1 ve tau+-10% ile LE degisimini olcer.")
    out(f"  S = stabil (CV<0.20), U = unstabil (CV>=0.20).")
    
    # test_sonuc.txt dosyasina kaydet
    output_path = os.path.join(os.path.dirname(__file__), 'test_sonuc.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    print(f"\nSonuclar kaydedildi: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    run_validation()
