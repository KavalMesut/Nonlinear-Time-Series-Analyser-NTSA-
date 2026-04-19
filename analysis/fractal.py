"""
Fractal dimension estimation (Correlation dimension)

Uses scipy.spatial.distance.pdist for vectorized pairwise distance computation.
"""
import numpy as np
from scipy.spatial.distance import pdist
from .embedding import embed_timeseries


def correlation_sum(embedded: np.ndarray, r: float, max_points: int = 5000) -> float:
    """
    Compute correlation sum for given radius using vectorized pdist.
    
    Args:
        embedded: embedded time series (n_points, m)
        r: radius
        max_points: maximum number of points to use (subsampling for large datasets)
    
    Returns:
        correlation sum C(r)
    """
    n = len(embedded)
    
    # Subsample if too many points
    if n > max_points:
        indices = np.linspace(0, n - 1, max_points, dtype=int)
        embedded = embedded[indices]
        n = max_points
    
    # Vectorized pairwise distances
    dists = pdist(embedded, metric='euclidean')
    
    # Count pairs within radius r
    count = np.sum(dists < r)
    
    # Normalize
    c_r = 2.0 * count / (n * (n - 1))
    
    return c_r


def correlation_dimension(data: np.ndarray, m: int, tau: int, 
                         r_min: float = None, r_max: float = None,
                         n_radii: int = 50, max_points: int = 5000) -> tuple:
    """
    Estimate correlation dimension
    
    Args:
        data: 1D time series
        m: embedding dimension
        tau: time delay
        r_min: minimum radius (default: auto)
        r_max: maximum radius (default: auto)
        n_radii: number of radii to test
        max_points: max points for distance computation
    
    Returns:
        (radii, correlation_sums)
    """
    embedded = embed_timeseries(data, m, tau)
    n = len(embedded)
    
    # Subsample for distance estimation
    if n > max_points:
        indices = np.linspace(0, n - 1, max_points, dtype=int)
        sample = embedded[indices]
    else:
        sample = embedded
    
    # Determine radius range from pairwise distances
    if r_min is None or r_max is None:
        dists = pdist(sample[:min(len(sample), 1000)], metric='euclidean')
        if r_min is None:
            r_min = np.percentile(dists, 5)
        if r_max is None:
            r_max = np.percentile(dists, 50)
    
    if r_min <= 0:
        r_min = r_max * 0.001
    
    # Logarithmic spacing
    radii = np.logspace(np.log10(r_min), np.log10(r_max), n_radii)
    
    # Compute all pairwise distances once
    all_dists = pdist(sample, metric='euclidean')
    n_sample = len(sample)
    
    # Compute correlation sum for each radius
    c_r = np.zeros(n_radii)
    for i, r in enumerate(radii):
        count = np.sum(all_dists < r)
        c_r[i] = 2.0 * count / (n_sample * (n_sample - 1))
    
    return radii, c_r


def estimate_dimension_from_correlation(radii: np.ndarray, c_r: np.ndarray,
                                       fit_start: int = None, fit_end: int = None) -> float:
    """
    Estimate dimension from correlation sum using log-log slope
    
    Args:
        radii: radius array
        c_r: correlation sum array
        fit_start: start index for fit
        fit_end: end index for fit
    
    Returns:
        correlation dimension estimate
    """
    # Remove zeros
    valid = c_r > 0
    if not np.any(valid):
        return np.nan
        
    log_r = np.log(radii[valid])
    log_c = np.log(c_r[valid])
    
    if fit_start is None:
        fit_start = 0
    if fit_end is None:
        fit_end = len(log_r)
    
    if fit_end <= fit_start + 1:
        return np.nan
    
    # Linear fit in log-log space
    coeffs = np.polyfit(log_r[fit_start:fit_end], log_c[fit_start:fit_end], 1)
    
    return coeffs[0]
