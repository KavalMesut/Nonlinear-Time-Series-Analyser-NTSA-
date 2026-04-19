"""
Time-delay embedding

Uses numpy stride_tricks for zero-copy embedding construction.
"""
import numpy as np


def embed_timeseries(data: np.ndarray, m: int, tau: int) -> np.ndarray:
    """
    Create time-delay embedding using stride tricks for zero-copy performance.
    
    Args:
        data: 1D time series
        m: embedding dimension
        tau: time delay
    
    Returns:
        embedded array of shape (n_points, m)
        where n_points = len(data) - (m-1)*tau
    """
    data = np.ascontiguousarray(data, dtype=np.float64)
    n = len(data)
    n_points = n - (m - 1) * tau
    
    if n_points < 1:
        raise ValueError(f"Not enough data points for embedding (m={m}, tau={tau})")
    
    if tau == 1 and m > 1:
        # Optimal case: use stride_tricks for zero-copy
        from numpy.lib.stride_tricks import as_strided
        itemsize = data.strides[0]
        return as_strided(data, shape=(n_points, m), strides=(itemsize, itemsize))
    
    # General case: construct with index array
    indices = np.arange(m) * tau  # [0, tau, 2*tau, ..., (m-1)*tau]
    row_indices = np.arange(n_points)[:, np.newaxis] + indices[np.newaxis, :]
    return data[row_indices]
