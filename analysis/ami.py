"""
Average Mutual Information (AMI) for delay estimation.

Vectorized implementation using NumPy for performance.
"""
import numpy as np


def compute_ami(data: np.ndarray, max_lag: int = None, bins: int = 64) -> np.ndarray:
    """
    Compute Average Mutual Information using vectorized NumPy operations.
    
    Args:
        data: 1D time series
        max_lag: maximum lag to compute (default: len(data)//10)
        bins: number of bins for histogram
    
    Returns:
        AMI values for lags 1 to max_lag
    """
    n = len(data)
    if max_lag is None:
        max_lag = n // 10
    
    max_lag = min(max_lag, n - 1)
    
    ami = np.zeros(max_lag)
    
    for lag in range(1, max_lag + 1):
        x = data[:-lag]
        y = data[lag:]
        
        # 2D histogram
        hist_xy, xedges, yedges = np.histogram2d(x, y, bins=bins, density=True)
        
        # Marginal histograms
        hist_x, _ = np.histogram(x, bins=xedges, density=True)
        hist_y, _ = np.histogram(y, bins=yedges, density=True)
        
        dx = xedges[1] - xedges[0]
        dy = yedges[1] - yedges[0]
        
        # Vectorized MI computation — no double loop
        # Outer product of marginals
        marginal_product = np.outer(hist_x, hist_y)
        
        # Mask where both joint and marginal are positive
        valid = (hist_xy > 0) & (marginal_product > 0)
        
        if np.any(valid):
            mi = np.sum(hist_xy[valid] * np.log(hist_xy[valid] / marginal_product[valid]))
            ami[lag - 1] = mi * dx * dy
        else:
            ami[lag - 1] = 0.0
    
    return ami


def find_first_minimum(ami: np.ndarray) -> int:
    """
    Find first local minimum in AMI

    Args:
        ami: AMI array

    Returns:
        lag of first minimum (1-indexed)
    """
    if len(ami) < 3:
        return 1

    for i in range(1, len(ami) - 1):
        if ami[i] < ami[i-1] and ami[i] < ami[i+1]:
            return i + 1

    # If no minimum found, return lag with global minimum
    return int(np.argmin(ami)) + 1


def estimate_tau_robust(data: np.ndarray,
                        max_lag_initial: int = 100,
                        max_lag_extended: int = 1000) -> int:
    """
    Robust tau estimate with auto-fallback for tau saturation.

    Bazi sistemlerde (ornek: Double Pendulum, slow rotational systems)
    standart max_lag=100 yetersiz kalir; AMI bu aralikta ilk minimumu
    bulamaz ve tau=max_lag'a "yapisir". Bu durumda max_lag genisletilir.

    Strateji:
    1. AMI(max_lag=max_lag_initial) -> first_minimum
    2. tau >= max_lag_initial - 1 (saturate) ise:
       AMI(max_lag=max_lag_extended) ile yeniden dene
    3. Hala saturate ise ACF 1/e gecisini kullan (fallback)

    Args:
        data: 1D zaman serisi
        max_lag_initial: ilk deneme icin max lag (default 100)
        max_lag_extended: saturate olursa kullanilacak genisletilmis max lag

    Returns:
        Tau (lag, 1-indexed)
    """
    ami = compute_ami(data, max_lag=max_lag_initial)
    tau = find_first_minimum(ami)

    # Saturate kontrolu: tau max_lag'a cok yakinsa AMI hâlâ azaliyor demektir
    if tau >= max_lag_initial - 1:
        max_lag_extended = min(max_lag_extended, len(data) - 1)
        if max_lag_extended > max_lag_initial:
            ami_ext = compute_ami(data, max_lag=max_lag_extended)
            tau = find_first_minimum(ami_ext)
            # Hala saturate ise ACF fallback (1/e veya zero-crossing)
            if tau >= max_lag_extended - 1:
                from .acf import compute_acf
                acf = compute_acf(data, max_lag=max_lag_extended)
                # Once zero-crossing dene
                zero_idx = np.where(np.diff(np.sign(acf)))[0]
                if len(zero_idx) > 0:
                    tau = int(zero_idx[0]) + 1
                else:
                    # 1/e gecisi
                    e_thresh = 1.0 / np.e
                    e_idx = np.where(acf < e_thresh)[0]
                    if len(e_idx) > 0:
                        tau = int(e_idx[0]) + 1

    return max(1, int(tau))
