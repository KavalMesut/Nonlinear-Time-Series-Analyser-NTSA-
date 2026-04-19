"""
Partial Autocorrelation Function (PACF)
"""
import numpy as np
from .acf import compute_acf


def compute_pacf(data: np.ndarray, max_lag: int = None) -> np.ndarray:
    """
    Compute partial autocorrelation function using Durbin-Levinson
    
    Args:
        data: 1D time series
        max_lag: maximum lag to compute (default: len(data)//2)
    
    Returns:
        PACF values for lags 0 to max_lag
    """
    n = len(data)
    if max_lag is None:
        max_lag = n // 2
    
    max_lag = min(max_lag, n - 1)
    
    # Get ACF
    acf = compute_acf(data, max_lag)
    
    # Durbin-Levinson recursion
    pacf = np.zeros(max_lag + 1)
    pacf[0] = 1.0
    
    if max_lag == 0:
        return pacf
    
    pacf[1] = acf[1]
    
    phi = np.zeros((max_lag + 1, max_lag + 1))
    phi[1, 1] = acf[1]
    
    for k in range(2, max_lag + 1):
        # Calculate phi[k, k]
        numerator = acf[k]
        for j in range(1, k):
            numerator -= phi[k-1, j] * acf[k-j]
        
        denominator = 1.0
        for j in range(1, k):
            denominator -= phi[k-1, j] * acf[j]
        
        phi[k, k] = numerator / denominator
        pacf[k] = phi[k, k]
        
        # Update phi[k, j] for j < k
        for j in range(1, k):
            phi[k, j] = phi[k-1, j] - phi[k, k] * phi[k-1, k-j]
    
    return pacf
