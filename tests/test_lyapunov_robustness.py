"""
Lyapunov saglamlik (robustness) test suiti.

Mevcut test_validation.py literatur degerleriyle dogrulama yapiyor.
Bu suit, Lyapunov hesaplayicisinin GURBETLI kosullara karsi davranisini olcer.

Yuksek oncelikli testler:
- Test #3: SNR / Gurultu dayanikliligi
- Test #2: Veri uzunlugu sweep (N konvergansi)
- Test #4: Lorenz rho parametre sweep
- Test #7: Baslangic kosulu duyarliligi
- Test #8a: Surrogate data testi (shuffle)

Cikti: tests/test_robustness_sonuc.txt
"""
import os
import sys
import time
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import generate_lorenz
from analysis import (
    compute_ami, find_first_minimum,
    compute_fnn, find_embedding_dimension,
    lyapunov_wolf_detailed,
    lyapunov_rosenstein,
    estimate_lyapunov_from_curve,
    estimate_theiler_window,
)


# Lorenz literatur referans degeri (sigma=10, rho=28, beta=8/3)
LORENZ_LE_REF = 0.9056

# Cikti satirlari (sonunda dosyaya yazilacak)
OUTPUT_LINES = []


def log(msg=""):
    """Print + buffer for final report file."""
    print(msg)
    OUTPUT_LINES.append(msg)


# ----------------------------------------------------------------------
# Ortak yardimci fonksiyonlar
# ----------------------------------------------------------------------

def estimate_params(data, dt):
    """AMI + FNN ile tau ve m bulur, Theiler penceresini hesaplar."""
    ami = compute_ami(data, max_lag=100)
    tau = find_first_minimum(ami)
    fnn = compute_fnn(data, tau=tau, max_dim=10)
    m = find_embedding_dimension(fnn, threshold=1.0)
    if m == 1:
        m = 2
    min_tsep = estimate_theiler_window(data, m=m, tau=tau, min_window=1)
    return tau, m, min_tsep


def compute_rosenstein_le(data, m, tau, dt, min_tsep):
    """Rosenstein LE (auto-fit) hesaplar; hata olursa NaN."""
    try:
        t_steps, div = lyapunov_rosenstein(data, m=m, tau=tau, dt=dt, min_tsep=min_tsep)
        return float(estimate_lyapunov_from_curve(t_steps, div))
    except Exception:
        return float('nan')


def compute_wolf_le(data, m, tau, dt, min_tsep, evolve_steps=8):
    """Wolf LE; hata olursa NaN."""
    try:
        det = lyapunov_wolf_detailed(
            data, m=m, tau=tau, dt=dt,
            evolve_steps=evolve_steps, min_tsep=min_tsep
        )
        return float(det['le'])
    except Exception:
        return float('nan')


def make_lorenz(n_points, dt=0.01, transient=2000, y0=None,
                rho=28.0, sigma=10.0, beta=8.0/3.0):
    """Belirli uzunlukta Lorenz serisi uretir (transient atilmis)."""
    t_end = (n_points + transient) * dt
    ts = generate_lorenz(y0=y0, t_span=(0, t_end), dt=dt,
                         sigma=sigma, rho=rho, beta=beta)
    data = ts.data[transient:transient + n_points]
    return data


def section_header(title):
    log("\n" + "=" * 78)
    log(title)
    log("=" * 78)


# ----------------------------------------------------------------------
# Test #3: SNR / Gurultu dayanikliligi
# ----------------------------------------------------------------------

def test_snr_robustness():
    section_header("TEST #3: SNR / GURULTU DAYANIKLILIGI (Lorenz, N=10000)")
    log("Beklenti: SNR azaldikca LE bozulur. Saglam algoritma yavas bozulur.")
    log("Referans LE = 0.9056")
    log("")

    np.random.seed(42)
    base_data = make_lorenz(n_points=10000, dt=0.01)
    signal_std = float(np.std(base_data))
    dt = 0.01

    snr_db_values = [None, 40, 30, 20, 15, 10]
    log(f"{'SNR(dB)':>8s} | {'tau':>3s} | {'m':>2s} | "
        f"{'Wolf LE':>9s} | {'W.Err%':>7s} | "
        f"{'Ros LE':>9s} | {'R.Err%':>7s}")
    log("-" * 70)

    results = []
    for snr_db in snr_db_values:
        if snr_db is None:
            data = base_data.copy()
            label = "clean"
        else:
            noise_std = signal_std / (10 ** (snr_db / 20.0))
            noise = np.random.randn(len(base_data)) * noise_std
            data = base_data + noise
            label = str(snr_db)

        tau, m, min_tsep = estimate_params(data, dt)
        wolf_le = compute_wolf_le(data, m, tau, dt, min_tsep, evolve_steps=8)
        ros_le = compute_rosenstein_le(data, m, tau, dt, min_tsep)
        w_err = abs(wolf_le - LORENZ_LE_REF) / LORENZ_LE_REF * 100 if np.isfinite(wolf_le) else float('nan')
        r_err = abs(ros_le - LORENZ_LE_REF) / LORENZ_LE_REF * 100 if np.isfinite(ros_le) else float('nan')

        log(f"{label:>8s} | {tau:>3d} | {m:>2d} | "
            f"{wolf_le:>9.4f} | {w_err:>6.1f}% | "
            f"{ros_le:>9.4f} | {r_err:>6.1f}%")
        results.append({'snr': snr_db, 'tau': tau, 'm': m,
                        'wolf_le': wolf_le, 'ros_le': ros_le})

    # Hizli yorum
    clean = results[0]
    worst = results[-1]
    log("")
    log(f"Yorum: Clean -> SNR=10dB arasinda Wolf {clean['wolf_le']:.3f} -> {worst['wolf_le']:.3f}, "
        f"Ros {clean['ros_le']:.3f} -> {worst['ros_le']:.3f}")
    return results


# ----------------------------------------------------------------------
# Test #2: Veri uzunlugu sweep
# ----------------------------------------------------------------------

def test_data_length_sweep():
    section_header("TEST #2: VERI UZUNLUGU SWEEP (Lorenz)")
    log("Beklenti: N arttikca LE konverge etmeli. Sapma -> embedding/algoritma kirilgan.")
    log(f"Referans LE = {LORENZ_LE_REF}")
    log("")

    n_values = [1000, 5000, 10000, 50000]  # 100k atlandi: Wolf cok yavas
    dt = 0.01

    log(f"{'N':>7s} | {'tau':>3s} | {'m':>2s} | "
        f"{'Wolf LE':>9s} | {'W.Err%':>7s} | "
        f"{'Ros LE':>9s} | {'R.Err%':>7s} | {'Time(s)':>7s}")
    log("-" * 78)

    results = []
    for n in n_values:
        t0 = time.time()
        data = make_lorenz(n_points=n, dt=dt)
        tau, m, min_tsep = estimate_params(data, dt)

        # Buyuk N'de Wolf cok yavas; N>=50000 icin Wolf'i atla
        if n <= 10000:
            wolf_le = compute_wolf_le(data, m, tau, dt, min_tsep, evolve_steps=8)
        else:
            wolf_le = float('nan')

        ros_le = compute_rosenstein_le(data, m, tau, dt, min_tsep)
        w_err = abs(wolf_le - LORENZ_LE_REF) / LORENZ_LE_REF * 100 if np.isfinite(wolf_le) else float('nan')
        r_err = abs(ros_le - LORENZ_LE_REF) / LORENZ_LE_REF * 100 if np.isfinite(ros_le) else float('nan')
        elapsed = time.time() - t0

        log(f"{n:>7d} | {tau:>3d} | {m:>2d} | "
            f"{wolf_le:>9.4f} | {w_err:>6.1f}% | "
            f"{ros_le:>9.4f} | {r_err:>6.1f}% | {elapsed:>7.1f}")
        results.append({'n': n, 'wolf_le': wolf_le, 'ros_le': ros_le, 'time': elapsed})

    # Konvergans olcumu (Rosenstein uzerinden)
    ros_values = [r['ros_le'] for r in results if np.isfinite(r['ros_le'])]
    if len(ros_values) >= 3:
        last_three = ros_values[-3:]
        spread = max(last_three) - min(last_three)
        log("")
        log(f"Yorum: Son 3 N degerinde Rosenstein spread = {spread:.4f} "
            f"({'KONVERGE' if spread < 0.1 else 'KONVERGE DEGIL'})")
    return results


# ----------------------------------------------------------------------
# Test #4: Lorenz rho parametre sweep
# ----------------------------------------------------------------------

def test_rho_parameter_sweep():
    section_header("TEST #4: LORENZ rho PARAMETRE SWEEP")
    log("Beklenti: rho=24.74 civarinda Hopf bifurcation; rho<24.74 stabil, rho>24.74 kaotik.")
    log("LE duzgun degismeli, kaotik->periyodik gecisleri yakalanmali.")
    log("")

    rho_values = [20.0, 22.0, 24.0, 25.0, 26.0, 28.0, 30.0, 32.0, 35.0]
    dt = 0.01
    n_points = 10000

    log(f"{'rho':>5s} | {'tau':>3s} | {'m':>2s} | "
        f"{'Ros LE':>9s} | {'Yorum':<25s}")
    log("-" * 60)

    results = []
    for rho in rho_values:
        try:
            data = make_lorenz(n_points=n_points, dt=dt, rho=rho)
        except Exception as e:
            log(f"{rho:>5.1f} | -- FAIL: {e} --")
            continue

        tau, m, min_tsep = estimate_params(data, dt)
        ros_le = compute_rosenstein_le(data, m, tau, dt, min_tsep)

        if not np.isfinite(ros_le):
            comment = "NaN"
        elif ros_le < -0.05:
            comment = "stabil (LE<0)"
        elif abs(ros_le) < 0.1:
            comment = "kritik/periyodik"
        elif ros_le < 0.5:
            comment = "zayif kaos"
        else:
            comment = "kaotik"

        log(f"{rho:>5.1f} | {tau:>3d} | {m:>2d} | "
            f"{ros_le:>9.4f} | {comment:<25s}")
        results.append({'rho': rho, 'le': ros_le, 'comment': comment})

    log("")
    log("Yorum: rho<24.74 LE<=0, rho>=25 LE>0 olmali. Aksi halde algoritma gecisi kaciriyor.")
    return results


# ----------------------------------------------------------------------
# Test #7: Baslangic kosulu duyarliligi
# ----------------------------------------------------------------------

def test_initial_condition_sensitivity():
    section_header("TEST #7: BASLANGIC KOSULU DUYARLILIGI (Lorenz, N=10000)")
    log("Beklenti: Ergodiklik nedeniyle ayni rho icin farkli (x0,y0,z0) ayni LE vermeli.")
    log(f"Referans LE = {LORENZ_LE_REF}")
    log("")

    np.random.seed(123)
    n_ic = 5
    initial_conditions = [
        np.array([1.0, 1.0, 1.0]),
        np.array([5.0, 5.0, 20.0]),
        np.array([-3.0, 2.0, 15.0]),
        np.random.uniform(-10, 10, 3),
        np.random.uniform(-10, 10, 3),
    ]
    dt = 0.01

    log(f"{'IC':>3s} | {'(x0,y0,z0)':<25s} | {'tau':>3s} | {'m':>2s} | "
        f"{'Ros LE':>9s} | {'Err%':>6s}")
    log("-" * 72)

    results = []
    for i, y0 in enumerate(initial_conditions):
        data = make_lorenz(n_points=10000, dt=dt, y0=y0)
        tau, m, min_tsep = estimate_params(data, dt)
        ros_le = compute_rosenstein_le(data, m, tau, dt, min_tsep)
        err = abs(ros_le - LORENZ_LE_REF) / LORENZ_LE_REF * 100 if np.isfinite(ros_le) else float('nan')
        ic_str = f"({y0[0]:.1f},{y0[1]:.1f},{y0[2]:.1f})"
        log(f"{i+1:>3d} | {ic_str:<25s} | {tau:>3d} | {m:>2d} | "
            f"{ros_le:>9.4f} | {err:>5.1f}%")
        results.append({'ic': y0.tolist(), 'le': ros_le})

    le_arr = np.array([r['le'] for r in results if np.isfinite(r['le'])])
    if len(le_arr) >= 2:
        mean = float(np.mean(le_arr))
        std = float(np.std(le_arr))
        cv = std / abs(mean) if abs(mean) > 1e-10 else float('nan')
        log("")
        log(f"Yorum: mean={mean:.4f}, std={std:.4f}, CV={cv:.3f} "
            f"({'STABIL' if cv < 0.10 else 'STABIL DEGIL'})")
    return results


# ----------------------------------------------------------------------
# Test #8a: Surrogate (shuffle) testi
# ----------------------------------------------------------------------

def test_surrogate_shuffle():
    section_header("TEST #8a: SURROGATE DATA (SHUFFLE) TESTI")
    log("Beklenti: Shuffle ile zamansal yapi yok edilir. LE >> 0 cikiyorsa sahte kaos.")
    log(f"Orijinal Lorenz LE = {LORENZ_LE_REF}, Shuffle LE -> 0 olmali.")
    log("")

    np.random.seed(7)
    dt = 0.01
    base_data = make_lorenz(n_points=10000, dt=dt)

    # Orijinal verinin tau, m'sini ogren
    tau_orig, m_orig, _ = estimate_params(base_data, dt)
    min_tsep_orig = estimate_theiler_window(base_data, m=m_orig, tau=tau_orig, min_window=1)
    le_orig = compute_rosenstein_le(base_data, m_orig, tau_orig, dt, min_tsep_orig)

    log(f"Orijinal Lorenz: tau={tau_orig}, m={m_orig}, LE={le_orig:.4f}")
    log("")
    log(f"{'Trial':>5s} | {'tau_s':>5s} | {'m_s':>3s} | "
        f"{'Same params LE':>15s} | {'Re-fit LE':>10s}")
    log("-" * 60)

    results = []
    for trial in range(5):
        shuffled = base_data.copy()
        np.random.shuffle(shuffled)

        # Yontem A: Orijinal tau, m'i kullan -> LE 0'a yakin olmali
        le_same = compute_rosenstein_le(shuffled, m_orig, tau_orig, dt, min_tsep_orig)

        # Yontem B: Shuffle uzerinde yeni AMI/FNN
        try:
            tau_s, m_s, min_tsep_s = estimate_params(shuffled, dt)
            le_refit = compute_rosenstein_le(shuffled, m_s, tau_s, dt, min_tsep_s)
        except Exception:
            tau_s, m_s, le_refit = -1, -1, float('nan')

        log(f"{trial+1:>5d} | {tau_s:>5d} | {m_s:>3d} | "
            f"{le_same:>15.4f} | {le_refit:>10.4f}")
        results.append({'trial': trial+1, 'le_same': le_same, 'le_refit': le_refit})

    # Yorum
    same_arr = np.array([r['le_same'] for r in results if np.isfinite(r['le_same'])])
    if len(same_arr) > 0:
        mean_abs = float(np.mean(np.abs(same_arr)))
        log("")
        log(f"Yorum: Orijinal parametrelerle shuffle LE ortalama |LE|={mean_abs:.4f} "
            f"(orijinal {le_orig:.4f}). "
            f"|LE| << orijinal ise SAGLIKLI. Aksi halde algoritma rasgele veriden de kaos uretiyor.")
    return results


# ----------------------------------------------------------------------
# Test #5: Embedding hassasiyeti (genis tau ve m sweep)
# ----------------------------------------------------------------------

def test_embedding_sensitivity():
    section_header("TEST #5: EMBEDDING HASSASIYETI (Lorenz, N=10000)")
    log("Beklenti: tau ve m makul aralikta degisirse LE az oynamali.")
    log("Mevcut compute_le_stability m+-1, tau+-10% bakiyor; burada tam grid sweep yapiyoruz.")
    log(f"Referans LE = {LORENZ_LE_REF}")
    log("")

    dt = 0.01
    data = make_lorenz(n_points=10000, dt=dt)
    tau_auto, m_auto, _ = estimate_params(data, dt)
    log(f"Auto: tau={tau_auto}, m={m_auto}")
    log("")

    # Kucuk grid: tau yaridan iki katina, m=2..6
    tau_values = sorted(set([max(1, tau_auto // 2), max(1, int(tau_auto * 0.75)),
                             tau_auto, int(tau_auto * 1.5), tau_auto * 2]))
    m_values = [2, 3, 4, 5, 6]

    # Tablo: satir = m, sutun = tau
    label = "m / tau"
    header = f"{label:>8s} | " + " | ".join(f"{t:>7d}" for t in tau_values)
    log(header)
    log("-" * len(header))

    grid = {}
    for m in m_values:
        row_vals = []
        for tau in tau_values:
            min_tsep = estimate_theiler_window(data, m=m, tau=tau, min_window=1)
            le = compute_rosenstein_le(data, m, tau, dt, min_tsep)
            grid[(m, tau)] = le
            row_vals.append(f"{le:>7.3f}" if np.isfinite(le) else "    nan")
        log(f"{m:>8d} | " + " | ".join(row_vals))

    # Istatistik
    finite_vals = np.array([v for v in grid.values() if np.isfinite(v)])
    if len(finite_vals) > 0:
        log("")
        log(f"Grid: mean={finite_vals.mean():.4f}, std={finite_vals.std():.4f}, "
            f"min={finite_vals.min():.4f}, max={finite_vals.max():.4f}")
        cv = finite_vals.std() / abs(finite_vals.mean()) if abs(finite_vals.mean()) > 1e-10 else float('nan')
        log(f"Yorum: CV={cv:.3f} ({'STABIL' if cv < 0.20 else 'STABIL DEGIL'})")
    return grid


# ----------------------------------------------------------------------
# Test #9: Sampling rate etkisi
# ----------------------------------------------------------------------

def test_sampling_rate():
    section_header("TEST #9: SAMPLING RATE ETKISI (Lorenz)")
    log("Beklenti: Downsample ile dt buyur, tau dusurulur. LE makul kalmali.")
    log("LE ciddi sapiyorsa reconstruction yanlis, tau secimi kirilgan.")
    log(f"Referans LE = {LORENZ_LE_REF}")
    log("")

    dt_orig = 0.01
    n_orig = 50000  # downsample sonra yeterli noktayi tutmak icin
    base_data = make_lorenz(n_points=n_orig, dt=dt_orig)

    log(f"{'k':>3s} | {'dt_eff':>7s} | {'N_eff':>6s} | {'tau':>3s} | {'m':>2s} | "
        f"{'Ros LE':>9s} | {'Err%':>6s}")
    log("-" * 60)

    results = []
    for k in [1, 2, 4, 8]:
        downsampled = base_data[::k]
        dt_eff = dt_orig * k
        try:
            tau, m, min_tsep = estimate_params(downsampled, dt_eff)
            le = compute_rosenstein_le(downsampled, m, tau, dt_eff, min_tsep)
        except Exception as e:
            tau, m, le = -1, -1, float('nan')
        err = abs(le - LORENZ_LE_REF) / LORENZ_LE_REF * 100 if np.isfinite(le) else float('nan')
        log(f"{k:>3d} | {dt_eff:>7.4f} | {len(downsampled):>6d} | {tau:>3d} | {m:>2d} | "
            f"{le:>9.4f} | {err:>5.1f}%")
        results.append({'k': k, 'dt': dt_eff, 'le': le})

    le_arr = np.array([r['le'] for r in results if np.isfinite(r['le'])])
    if len(le_arr) >= 2:
        log("")
        log(f"Yorum: LE spread = {le_arr.max() - le_arr.min():.4f} "
            f"({'STABIL' if le_arr.max() - le_arr.min() < 0.2 else 'STABIL DEGIL'})")
    return results


# ----------------------------------------------------------------------
# Test #10: Sliding window analiz
# ----------------------------------------------------------------------

def test_sliding_window():
    section_header("TEST #10: SLIDING WINDOW ANALIZ (Lorenz, N=20000)")
    log("Beklenti: Stabil kaotik sistemde pencereler arasi LE varyansi kucuk olmali.")
    log("AMI+FNN hesabi her pencerede tekrarlanmaz; tum seriden bulunan tau/m sabit tutulur.")
    log(f"Referans LE = {LORENZ_LE_REF}")
    log("")

    dt = 0.01
    data = make_lorenz(n_points=20000, dt=dt)
    tau, m, min_tsep = estimate_params(data, dt)
    log(f"Sabit parametreler (tum seriden): tau={tau}, m={m}, min_tsep={min_tsep}")
    log("")

    window_size = 5000
    stride = 2500
    n_windows = (len(data) - window_size) // stride + 1

    log(f"{'Win':>3s} | {'Start':>6s} | {'End':>6s} | {'Ros LE':>9s} | {'Err%':>6s}")
    log("-" * 50)

    le_values = []
    for i in range(n_windows):
        start = i * stride
        end = start + window_size
        window = data[start:end]
        le = compute_rosenstein_le(window, m, tau, dt, min_tsep)
        err = abs(le - LORENZ_LE_REF) / LORENZ_LE_REF * 100 if np.isfinite(le) else float('nan')
        log(f"{i+1:>3d} | {start:>6d} | {end:>6d} | {le:>9.4f} | {err:>5.1f}%")
        if np.isfinite(le):
            le_values.append(le)

    if len(le_values) >= 2:
        le_arr = np.array(le_values)
        mean = le_arr.mean()
        std = le_arr.std()
        cv = std / abs(mean) if abs(mean) > 1e-10 else float('nan')
        log("")
        log(f"Yorum: mean={mean:.4f}, std={std:.4f}, CV={cv:.3f} "
            f"({'STABIL' if cv < 0.10 else 'STABIL DEGIL'})")
    return le_values


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def run_all():
    log("=" * 78)
    log("LYAPUNOV ROBUSTNESS TEST SUITE")
    log("=" * 78)

    total_start = time.time()

    test_snr_robustness()
    test_data_length_sweep()
    test_rho_parameter_sweep()
    test_initial_condition_sensitivity()
    test_surrogate_shuffle()
    test_embedding_sensitivity()
    test_sampling_rate()
    test_sliding_window()

    total = time.time() - total_start
    log("")
    log("=" * 78)
    log(f"TUM TESTLER TAMAMLANDI - Toplam sure: {total:.1f}s ({total/60:.1f} dk)")
    log("=" * 78)

    # Sonuclari dosyaya yaz
    output_path = os.path.join(os.path.dirname(__file__), 'test_robustness_sonuc.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(OUTPUT_LINES) + "\n")
    print(f"\nSonuclar kaydedildi: {os.path.abspath(output_path)}")


if __name__ == "__main__":
    run_all()
