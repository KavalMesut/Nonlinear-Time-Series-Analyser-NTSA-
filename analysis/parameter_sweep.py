"""
Parametre tarama (parameter sweep) modulu.

Iki ana fonksiyon:
- bifurcation_sweep(): Bir parametreyi tararken her degerde sistem
  dinamiginin orneklenmesi (ODE: lokal maksimumlar; map: x_n degerleri).
- lyapunov_sweep(): Her parametre degerinde en buyuk Lyapunov ustelinin
  hesabi (Rosenstein/Kantz/Wolf/Benettin).

Bu iki cikti dikey hizali grafikler olarak yorumlandiginda klasik
bifurcation diyagrami + Lyapunov sweep gorseli verir: pozitif lambda1
bolgeleri bifurcation'da bulanik kaotik bantlarla ortusur, negatif
lambda1 ise keskin periyodik cizgilerle.
"""
from typing import Callable, Dict, List, Tuple, Optional
import numpy as np


# ---------------------------------------------------------------------------
# Sistem kayit defteri — generator + parametre listesi + map mi flag'i
# ---------------------------------------------------------------------------

# Bir sistem icin "sweep edilebilen" parametre adlari ve generator kwarg
# isimleri ayni olmadiginda metadata->kwarg cevirisi gerekir (sine_map: lambda).
# 'kwargs': sweep_param adi -> generator'a gecirilecek kwarg adi
# 'metadata_keys': sweep_param adi -> metadata'da geldigi key
SYSTEM_INFO: Dict[str, dict] = {
    'lorenz': {
        'is_map': False,
        'kwargs':        {'sigma': 'sigma', 'rho': 'rho', 'beta': 'beta'},
        'metadata_keys': {'sigma': 'sigma', 'rho': 'rho', 'beta': 'beta'},
        'defaults': {'sigma': 10.0, 'rho': 28.0, 'beta': 8.0/3.0},
    },
    'rossler': {
        'is_map': False,
        'kwargs':        {'a': 'a', 'b': 'b', 'c': 'c'},
        'metadata_keys': {'a': 'a', 'b': 'b', 'c': 'c'},
        'defaults': {'a': 0.2, 'b': 0.2, 'c': 5.7},
    },
    'chua': {
        'is_map': False,
        'kwargs':        {'alpha': 'alpha', 'beta': 'beta'},
        'metadata_keys': {'alpha': 'alpha', 'beta': 'beta'},
        'defaults': {'alpha': 15.6, 'beta': 28.0},
    },
    'chen': {
        'is_map': False,
        'kwargs':        {'a': 'a', 'b': 'b', 'c': 'c'},
        'metadata_keys': {'a': 'a', 'b': 'b', 'c': 'c'},
        'defaults': {'a': 35.0, 'b': 3.0, 'c': 28.0},
    },
    'duffing': {
        'is_map': False,
        'kwargs':        {'delta': 'delta', 'gamma': 'gamma', 'omega': 'omega'},
        'metadata_keys': {'delta': 'delta', 'gamma': 'gamma', 'omega': 'omega'},
        'defaults': {'delta': 0.3, 'gamma': 0.5, 'omega': 1.2},
    },
    'double_pendulum': {
        'is_map': False,
        'kwargs':        {'m1': 'm1', 'm2': 'm2', 'l1': 'l1', 'l2': 'l2', 'g': 'g'},
        'metadata_keys': {'m1': 'm1', 'm2': 'm2', 'l1': 'l1', 'l2': 'l2', 'g': 'g'},
        'defaults': {'m1': 1.0, 'm2': 1.0, 'l1': 1.0, 'l2': 1.0, 'g': 9.81},
    },
    'logistic_map': {
        'is_map': True,
        'kwargs':        {'r': 'r'},
        'metadata_keys': {'r': 'r'},
        'defaults': {'r': 4.0},
    },
    'henon_map': {
        'is_map': True,
        'kwargs':        {'a': 'a', 'b': 'b'},
        'metadata_keys': {'a': 'a', 'b': 'b'},
        'defaults': {'a': 1.4, 'b': 0.3},
    },
    'tent_map': {
        'is_map': True,
        'kwargs':        {'mu': 'mu'},
        'metadata_keys': {'mu': 'mu'},
        'defaults': {'mu': 2.0},
    },
    'sine_map': {
        'is_map': True,
        'kwargs':        {'lambda': 'lambda_param'},   # generator kwarg adi farkli
        'metadata_keys': {'lambda': 'lambda'},
        'defaults': {'lambda': 1.0},
    },
    'ikeda_map': {
        'is_map': True,
        'kwargs':        {'u': 'u'},
        'metadata_keys': {'u': 'u'},
        'defaults': {'u': 0.9},
    },
}


def get_sweepable_params(metadata: dict) -> Dict[str, float]:
    """
    Metadata'dan {sweep_name: current_value} sozlugu cikar. Sweep_name'ler
    SYSTEM_INFO'da tanimli, kullanici dostu adlardir.
    """
    if not metadata:
        return {}
    system = (metadata.get('system') or '').lower()
    info = SYSTEM_INFO.get(system)
    if info is None:
        return {}

    result = {}
    if info['is_map']:
        # Map: parametreler metadata'da duz key olarak duruyor
        for sweep_name, meta_key in info['metadata_keys'].items():
            val = metadata.get(meta_key, info['defaults'].get(sweep_name))
            if val is not None:
                result[sweep_name] = float(val)
    else:
        # ODE: parametreler metadata['params'] altinda
        params_dict = metadata.get('params', {}) or {}
        for sweep_name, meta_key in info['metadata_keys'].items():
            val = params_dict.get(meta_key, info['defaults'].get(sweep_name))
            if val is not None:
                result[sweep_name] = float(val)
    return result


def get_system_info(system_name: str) -> Optional[dict]:
    """SYSTEM_INFO girisi getirir (yoksa None)."""
    if not system_name:
        return None
    return SYSTEM_INFO.get(system_name.lower())


def _load_generator(system_name: str) -> Callable:
    """Sistem adina gore generator fonksiyonunu lazy import eder."""
    from core.generators import (
        generate_lorenz, generate_rossler, generate_chua, generate_chen,
        generate_duffing, generate_double_pendulum,
        logistic_map, henon_map, tent_map, sine_map, ikeda_map,
    )
    GENERATORS = {
        'lorenz': generate_lorenz,
        'rossler': generate_rossler,
        'chua': generate_chua,
        'chen': generate_chen,
        'duffing': generate_duffing,
        'double_pendulum': generate_double_pendulum,
        'logistic_map': logistic_map,
        'henon_map': henon_map,
        'tent_map': tent_map,
        'sine_map': sine_map,
        'ikeda_map': ikeda_map,
    }
    return GENERATORS[system_name.lower()]


def _build_kwargs(system_name: str, base_params: Dict[str, float],
                  sweep_param: str, sweep_value: float) -> Dict[str, float]:
    """sweep_param degerini set ederek {kwarg: deger} sozlugu uretir."""
    info = SYSTEM_INFO[system_name.lower()]
    out = {}
    # Once base_params'i kwarg adlarina cevir
    for sweep_name, current_val in base_params.items():
        kwarg_name = info['kwargs'].get(sweep_name, sweep_name)
        out[kwarg_name] = float(current_val)
    # Sweep parametresini override et
    sweep_kwarg = info['kwargs'].get(sweep_param, sweep_param)
    out[sweep_kwarg] = float(sweep_value)
    return out


def _generate_at(system_name: str, kwargs: dict,
                 t_total: float, dt: float, n_map: int):
    """ODE veya map generator'i cagirir, TimeSeries ve is_map flag'i doner."""
    info = SYSTEM_INFO[system_name.lower()]
    factory = _load_generator(system_name)
    if info['is_map']:
        ts = factory(n=n_map, **kwargs)
    else:
        ts = factory(t_span=(0.0, t_total), dt=dt, **kwargs)
    return ts, info['is_map']


# ---------------------------------------------------------------------------
# Bifurcation sweep
# ---------------------------------------------------------------------------

def bifurcation_sweep(
    system_name: str,
    base_params: Dict[str, float],
    sweep_param: str,
    sweep_values: np.ndarray,
    *,
    dt: float = 0.01,
    t_total: float = 200.0,
    transient_frac: float = 0.5,
    n_samples: int = 200,
    n_map: int = 5000,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[Tuple[float, np.ndarray]]:
    """
    Bifurcation tarama.

    Args:
        system_name: 'lorenz', 'logistic_map', vb. (SYSTEM_INFO anahtari).
        base_params: Diger parametrelerin sabit degerleri (sweep_name -> value).
        sweep_param: Taranacak parametre (sweep_name).
        sweep_values: Taranacak parametre degerleri (1D array).
        dt: ODE icin zaman adimi.
        t_total: ODE icin toplam zaman.
        transient_frac: Atilacak transient orani (0-1).
        n_samples: Her parametre degerinde toplanacak ornek sayisi.
        n_map: Map'ler icin toplam iterasyon (transient + ornek).
        progress_callback: progress(i+1, n_total) cagiri.

    Returns:
        list of (param_value, samples_array). samples_array bos olabilir.
    """
    results = []
    n_total = len(sweep_values)

    for i, val in enumerate(sweep_values):
        try:
            kwargs = _build_kwargs(system_name, base_params, sweep_param, float(val))
            ts, is_map = _generate_at(system_name, kwargs, t_total, dt, n_map)
            data = ts.data
            transient_n = int(transient_frac * len(data))
            tail = data[transient_n:]

            if is_map:
                # Map'te her x_n bir ornek; sadece sonu al
                if len(tail) > n_samples:
                    samples = tail[-n_samples:]
                else:
                    samples = tail
            else:
                # ODE'de lokal maksimum noktalari
                if len(tail) < 3:
                    samples = np.array([])
                else:
                    peaks = np.where(
                        (tail[1:-1] > tail[:-2]) & (tail[1:-1] > tail[2:])
                    )[0] + 1
                    peak_values = tail[peaks]
                    if len(peak_values) > n_samples:
                        # Son n_samples'i al (steady state'e en yakin)
                        samples = peak_values[-n_samples:]
                    else:
                        samples = peak_values
            results.append((float(val), np.asarray(samples, dtype=float)))
        except Exception:
            results.append((float(val), np.array([])))

        if progress_callback:
            progress_callback(i + 1, n_total)

    return results


# ---------------------------------------------------------------------------
# Lyapunov sweep
# ---------------------------------------------------------------------------

def lyapunov_sweep(
    system_name: str,
    base_params: Dict[str, float],
    sweep_param: str,
    sweep_values: np.ndarray,
    *,
    method: str = 'rosenstein',
    dt: float = 0.01,
    t_total: float = 200.0,
    transient_frac: float = 0.2,
    n_map: int = 5000,
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> List[Tuple[float, float]]:
    """
    Her parametre degerinde lambda1 hesaplar.

    method:
        'rosenstein' (default), 'kantz', 'wolf', 'benettin'

    'benettin' sadece ODE sistemler icindir (map'lerde NaN doner).
    """
    from analysis import (
        lyapunov_rosenstein, lyapunov_kantz, lyapunov_wolf, lyapunov_benettin,
        estimate_lyapunov_from_curve, estimate_theiler_window,
        compute_ami, find_first_minimum, compute_fnn, find_embedding_dimension,
    )
    from core import get_ode_system, ODE_SYSTEM_REGISTRY

    info = SYSTEM_INFO.get(system_name.lower())
    if info is None:
        raise ValueError(f"Unknown system: {system_name}")
    is_map = info['is_map']

    results = []
    n_total = len(sweep_values)

    for i, val in enumerate(sweep_values):
        try:
            kwargs = _build_kwargs(system_name, base_params, sweep_param, float(val))

            if method == 'benettin':
                # Sadece bilinen ODE sistemler
                if is_map or system_name.lower() not in ODE_SYSTEM_REGISTRY:
                    le = float('nan')
                else:
                    # ODE registry icin kwargs zaten generator-uyumlu (sigma, rho, beta vb.)
                    ode_func, default_y0, dim = get_ode_system(system_name, kwargs)
                    spec = lyapunov_benettin(
                        ode_func, default_y0,
                        t_span=(0.0, t_total), dt=dt, transient=2000, n_exponents=dim,
                    )
                    exps = spec['exponents']
                    le = float(exps[0]) if len(exps) > 0 else float('nan')
            else:
                # Veri uzerinden hesap
                ts, _ = _generate_at(system_name, kwargs, t_total, dt, n_map)
                data = ts.data
                transient_n = int(transient_frac * len(data))
                data = data[transient_n:]
                dt_eff = ts.dt

                if is_map:
                    tau = 1
                else:
                    ami = compute_ami(data, max_lag=100)
                    tau = max(1, find_first_minimum(ami))
                fnn = compute_fnn(data, tau=tau, max_dim=10)
                m = max(2, find_embedding_dimension(fnn, threshold=1.0))
                min_tsep = estimate_theiler_window(data, m=m, tau=tau, min_window=1)

                if method == 'wolf':
                    le = float(lyapunov_wolf(data, m=m, tau=tau, dt=dt_eff,
                                             min_tsep=min_tsep))
                elif method == 'kantz':
                    t_steps, div = lyapunov_kantz(data, m=m, tau=tau, dt=dt_eff,
                                                  min_tsep=min_tsep)
                    le = float(estimate_lyapunov_from_curve(t_steps, div))
                else:  # rosenstein default
                    t_steps, div = lyapunov_rosenstein(data, m=m, tau=tau, dt=dt_eff,
                                                       min_tsep=min_tsep)
                    le = float(estimate_lyapunov_from_curve(t_steps, div))
            results.append((float(val), le))
        except Exception:
            results.append((float(val), float('nan')))

        if progress_callback:
            progress_callback(i + 1, n_total)

    return results
