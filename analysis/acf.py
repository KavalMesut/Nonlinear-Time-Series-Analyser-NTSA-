"""
Autocorrelation Function (ACF)
"""
import numpy as np


def compute_acf(data: np.ndarray, max_lag: int = None) -> np.ndarray:
    """
    Compute autocorrelation function
    
    Args:
        data: 1D time series
        max_lag: maximum lag to compute (default: len(data)//2)
    
    Returns:
        ACF values for lags 0 to max_lag
    """
    n = len(data)
    if max_lag is None:
        max_lag = n // 2
    
    max_lag = min(max_lag, n - 1)
    
    data = data - np.mean(data)
    c0 = np.dot(data, data) / n
    
    acf = np.zeros(max_lag + 1)
    acf[0] = 1.0
    
    for lag in range(1, max_lag + 1):
        c_lag = np.dot(data[:-lag], data[lag:]) / n
        acf[lag] = c_lag / c0
    
    return acf
