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
