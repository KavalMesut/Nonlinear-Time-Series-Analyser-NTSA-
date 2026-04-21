"""
Wolf MATLAB -> Python Dogrulama Testleri
=========================================
Amac: Wolf'un orijinal MATLAB kodunu Python'a dogru cevirdigimizi dogrulamak.

Test 1: Lorenz (Data2.lor)
  - 16384 nokta, sigma=10, rho=28, beta=8/3, dt=0.01
  - Parametreler: tau=10, m=3, evolve=20
  - Beklenen: ~2.1 bits/s

Test 2: Logistic Map (uretiliyor)
  - 512 iterasyon, x(n+1) = 4.0*x(n)*(1-x(n))
  - Parametreler: tau=1, m=2, evolve=3, dt=1
  - Beklenen: 1.0 bits/iteration (Wolf: 0.98)

Referans: Physica 16D (1985) 285-317, Wolf et al.
"""
import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.lyapunov import lyapunov_wolf_detailed


def test_lorenz_data2():
    """Test #1: Lorenz Data2.lor ile Wolf MATLAB uyumluluğu."""
    print("\n" + "=" * 70)
    print("TEST #1: LORENZ (Data2.lor)")
    print("=" * 70)

    data_path = os.path.join(
        os.path.dirname(__file__), '..', 'documents',
        'Wolf_Lyapunov - 1.2', 'Data2.lor'
    )
    data = np.loadtxt(data_path)
    print(f"Veri:       Data2.lor (16384 nokta Lorenz)")
    print(f"Sistem:     sigma=10, rho=28, beta=8/3, dt=0.01")

    # Wolf parametreleri (testbench.m)
    tau = 10
    m = 3
    dt = 0.01
    evolve = 20
    thmax = 30.0

    data_range = data.max() - data.min()
    dismin = 0.001 * data_range
    dismax = 0.3 * data_range

    print(f"\nParametreler (testbench.m):")
    print(f"  tau={tau}, m={m}, dt={dt}, evolve={evolve}")
    print(f"  dismin={dismin:.6f} (0.001*range), dismax={dismax:.4f} (0.3*range)")

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
    
    wolf_expected = 2.1
    err_pct = abs(le_bits - wolf_expected) / wolf_expected * 100

    print(f"\nSonuc:")
    print(f"  Python:     {le_bits:.4f} bits/s  ({le_nats:.4f} nats/s)")
    print(f"  Wolf:       ~{wolf_expected} bits/s")
    print(f"  Fark:       {err_pct:.1f}%")
    print(f"  Iterations: {iters}")
    print(f"  Durum:      {'BASARILI' if err_pct <= 10 else 'BASARISIZ'}")

    return {
        'name': 'Lorenz',
        'python_bits': le_bits,
        'wolf_bits': wolf_expected,
        'error_pct': err_pct,
        'success': err_pct <= 10.0
    }


def test_logistic_map():
    """Test #2: Logistic map ile Wolf MATLAB uyumluluğu."""
    print("\n" + "=" * 70)
    print("TEST #2: LOGISTIC MAP")
    print("=" * 70)

    # Logistic map: x(n+1) = 4*x(n)*(1-x(n)), 512 iterasyon
    n = 512
    x0 = 0.1
    data = np.zeros(n)
    data[0] = x0
    for i in range(1, n):
        data[i] = 4.0 * data[i-1] * (1.0 - data[i-1])

    print(f"Veri:       512 iterasyon logistic map")
    print(f"Sistem:     x(n+1) = 4.0*x(n)*(1-x(n)), x0={x0}")
    print(f"Analitik:   ln(2) per iteration = {np.log(2):.4f} nats/iter")

    # Wolf parametreleri (lyapunews.pdf)
    # BASGEN 512, 1, 2, 20
    # FET 1, 3, 0.0001, 0.05, 30
    tau = 1
    m = 2
    dt = 1.0        # discrete map, dt=1 iteration
    evolve = 3
    thmax = 30.0

    data_range = data.max() - data.min()
    dismin = 0.0001 * data_range
    dismax = 0.05 * data_range

    print(f"\nParametreler (Wolf lyapunews.pdf):")
    print(f"  tau={tau}, m={m}, dt={dt}, evolve={evolve}")
    print(f"  dismin={dismin:.6f} (0.0001*range), dismax={dismax:.4f} (0.05*range)")

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
    
    # Wolf: 0.98 bits/iteration
    # Theory: 1.0 bits/iteration (ln(2) nats/iteration)
    wolf_expected = 0.98
    theory_bits = 1.0
    err_pct_wolf = abs(le_bits - wolf_expected) / wolf_expected * 100
    err_pct_theory = abs(le_bits - theory_bits) / theory_bits * 100

    print(f"\nSonuc:")
    print(f"  Python:     {le_bits:.4f} bits/iter  ({le_nats:.4f} nats/iter)")
    print(f"  Wolf:       {wolf_expected} bits/iter")
    print(f"  Theory:     {theory_bits} bits/iter")
    print(f"  Fark(Wolf): {err_pct_wolf:.1f}%")
    print(f"  Fark(Teori):{err_pct_theory:.1f}%")
    print(f"  Iterations: {iters}")
    print(f"  Durum:      {'BASARILI' if err_pct_wolf <= 15 else 'BASARISIZ'}")

    return {
        'name': 'Logistic',
        'python_bits': le_bits,
        'wolf_bits': wolf_expected,
        'theory_bits': theory_bits,
        'error_pct': err_pct_wolf,
        'success': err_pct_wolf <= 15.0
    }


def run_all_tests():
    """Tüm Wolf MATLAB uyumluluk testlerini çalıştır."""
    print("=" * 70)
    print("WOLF MATLAB -> PYTHON DOGRULAMA TESTLERI")
    print("=" * 70)

    results = []
    results.append(test_lorenz_data2())
    results.append(test_logistic_map())

    # Özet tablo
    print("\n" + "=" * 70)
    print("ÖZET")
    print("=" * 70)
    print(f"{'Sistem':<12} {'Python':<12} {'Wolf':<12} {'Fark':<8} {'Durum':<10}")
    print("-" * 70)
    
    for r in results:
        status = "BASARILI" if r['success'] else "BASARISIZ"
        print(f"{r['name']:<12} {r['python_bits']:>10.4f}b  {r['wolf_bits']:>10.4f}b  "
              f"{r['error_pct']:>6.1f}%  {status:<10}")

    # Dosyaya kaydet
    output_path = os.path.join(os.path.dirname(__file__), 'wolf_matlab_match_sonuc.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("Wolf MATLAB -> Python Dogrulama Testleri\n")
        f.write("=" * 50 + "\n\n")
        
        for r in results:
            f.write(f"{r['name']}:\n")
            f.write(f"  Python: {r['python_bits']:.4f} bits\n")
            f.write(f"  Wolf:   {r['wolf_bits']:.4f} bits\n")
            f.write(f"  Fark:   {r['error_pct']:.1f}%\n")
            f.write(f"  Sonuc:  {'BASARILI' if r['success'] else 'BASARISIZ'}\n\n")
        
        all_success = all(r['success'] for r in results)
        f.write(f"GENEL SONUC: {'BASARILI' if all_success else 'BASARISIZ'}\n")

    print(f"\nSonuclar: {os.path.abspath(output_path)}")
    
    all_success = all(r['success'] for r in results)
    print("=" * 70)
    if all_success:
        print("GENEL SONUC: BASARILI — Python kodu MATLAB ile uyumlu")
    else:
        print("GENEL SONUC: BASARISIZ — Bazi testler basarisiz")
    print("=" * 70)

    return all_success


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
