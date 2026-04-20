"""
Wolf MATLAB -> Python Dogrulama Testi
=====================================
Amac: Wolf'un orijinal MATLAB kodunu (testbench.m) Python'a dogru cevirdigimizi
dogrulamak. Wolf'un kendi Data2.lor verisini ve birebir ayni parametreleri kullanir.

Referans:
  - Physica 16D (1985) 285-317, Wolf et al.
  - testbench.m parametreleri: tau=10, ndim=3, dt=0.01, evolve=20
  - Data2.lor: 16384 nokta Lorenz (sigma=10, rho=28, beta=8/3)
  - Beklenen sonuc: ~2.1 bits/s (Wolf'un dokumantasyonundan)

NOT: Bu test bilimsel referans dogrulamasi DEGILDIR.
     Bilimsel dogrulama icin test_validation.py'ye bakin.
"""
import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.lyapunov import lyapunov_wolf_detailed

WOLF_EXPECTED_BITS = 2.1    # Wolf'un dokumantasyonundaki deger
TOLERANCE_PCT = 10.0        # %10 tolerans


def run_wolf_match_test():
    """Wolf MATLAB kodunu birebir parametrelerle dogrula."""
    print("=" * 70)
    print("WOLF MATLAB -> PYTHON DOGRULAMA TESTI")
    print("=" * 70)

    # Wolf'un kendi verisini yukle
    data_path = os.path.join(
        os.path.dirname(__file__), '..', 'documents',
        'Wolf_Lyapunov - 1.2', 'Data2.lor'
    )
    data = np.loadtxt(data_path)
    print(f"Veri:       {data_path}")
    print(f"Nokta:      {len(data)}")

    # Wolf testbench.m parametreleri — birebir
    tau = 10
    m = 3           # ndim
    dt = 0.01
    evolve = 20
    thmax = 30.0    # derece

    # Wolf'un relatif mesafe parametreleri (veri araligina gore olceklenir)
    data_range = data.max() - data.min()
    dismin = 0.001 * data_range     # minimum komsu mesafesi
    dismax = 0.3 * data_range       # maximum komsu mesafesi

    print(f"\nParametreler (testbench.m ile ayni):")
    print(f"  tau={tau}, m={m}, dt={dt}, evolve={evolve}")
    print(f"  dismin={dismin:.6f} (0.001 * range)")
    print(f"  dismax={dismax:.4f} (0.3 * range)")
    print(f"  thmax={thmax} derece")
    print(f"  min_tsep={evolve} (Wolf: abs(runner-oldpnt) < evolve)")

    # Calistir
    result = lyapunov_wolf_detailed(
        data, m=m, tau=tau, dt=dt,
        evolve_steps=evolve,
        min_neighbor_distance=dismin,
        initial_neighbor_distance=dismax,
        replacement_threshold=dismax,
        replacement_angle_deg=thmax,
        min_tsep=evolve
    )

    le_nats = result['le']
    le_bits = le_nats / np.log(2)
    iters = len(result['le_per_step'])
    err_pct = abs(le_bits - WOLF_EXPECTED_BITS) / WOLF_EXPECTED_BITS * 100

    print(f"\nSonuclar:")
    print(f"  Python sonucu:    {le_bits:.4f} bits/s  ({le_nats:.4f} nats/s)")
    print(f"  MATLAB beklenen:  ~{WOLF_EXPECTED_BITS} bits/s")
    print(f"  Fark:             {err_pct:.1f}%")
    print(f"  Iterations:       {iters}")
    print(f"  Convergence:      {result['convergence']:.4f}")
    print(f"  Std:              {result['std']:.4f}")

    # Running estimate son 10
    running = result['running_le']
    if len(running) > 10:
        print(f"\nSon 10 running LE:")
        for i, v in enumerate(running[-10:]):
            idx = len(running) - 10 + i
            print(f"    [{idx:3d}] {v:.4f} nats/s  ({v / np.log(2):.4f} bits/s)")

    # Karar
    print(f"\n{'=' * 70}")
    if err_pct <= TOLERANCE_PCT:
        print(f"SONUC: BASARILI — Python kodu MATLAB ile uyumlu (fark {err_pct:.1f}% < {TOLERANCE_PCT}%)")
    else:
        print(f"SONUC: BASARISIZ — fark {err_pct:.1f}% > tolerans {TOLERANCE_PCT}%")
    print("=" * 70)

    # Dosyaya kaydet
    output_path = os.path.join(os.path.dirname(__file__), 'wolf_lorenz_matlab_match_sonuc.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Wolf MATLAB -> Python Dogrulama\n")
        f.write(f"{'=' * 50}\n")
        f.write(f"Veri:     Data2.lor ({len(data)} nokta)\n")
        f.write(f"Params:   tau={tau}, m={m}, dt={dt}, evolve={evolve}\n")
        f.write(f"Python:   {le_bits:.4f} bits/s ({le_nats:.4f} nats/s)\n")
        f.write(f"MATLAB:   ~{WOLF_EXPECTED_BITS} bits/s\n")
        f.write(f"Fark:     {err_pct:.1f}%\n")
        f.write(f"Iters:    {iters}\n")
        f.write(f"Sonuc:    {'BASARILI' if err_pct <= TOLERANCE_PCT else 'BASARISIZ'}\n")
    print(f"\nSonuclar kaydedildi: {os.path.abspath(output_path)}")

    return err_pct <= TOLERANCE_PCT


if __name__ == "__main__":
    success = run_wolf_match_test()
    sys.exit(0 if success else 1)
