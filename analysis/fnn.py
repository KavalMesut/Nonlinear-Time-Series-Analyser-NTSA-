"""
False Nearest Neighbors (FNN) for embedding dimension estimation.

Uses scipy.spatial.cKDTree for O(n log n) neighbor search.
"""
import numpy as np
from scipy.spatial import cKDTree

from .embedding import embed_timeseries


def compute_fnn(data: np.ndarray, tau: int, max_dim: int = 10,
                rtol: float = 10.0, atol: float = 2.0,
                min_tsep: int = None, max_samples: int = 2000) -> np.ndarray:
    """
    Compute False Nearest Neighbor percentages using the Kennel et al. criteria.
    Uses KD-Tree for fast neighbor search.

    Args:
        data: 1D time series
        tau: time delay
        max_dim: maximum embedding dimension to test
        rtol: relative tolerance for the added-coordinate test
        atol: absolute tolerance relative to the data standard deviation
        min_tsep: Theiler window in samples. Defaults to tau.
        max_samples: number of fiducial points to test per dimension

    Returns:
        FNN percentages for dimensions 1..max_dim
    """
    data = np.asarray(data, dtype=np.float64)
    n = len(data)
    fnn_percent = np.full(max_dim, np.nan)

    if min_tsep is None:
        min_tsep = max(1, tau)

    std_data = float(np.std(data))
    if std_data == 0:
        return np.zeros(max_dim)

    for m in range(1, max_dim + 1):
        n_points_next = n - m * tau
        if n_points_next < 2:
            break

        embedded_m = embed_timeseries(data, m, tau)[:n_points_next]
        
        # Build KD-Tree for this embedding
        tree = cKDTree(embedded_m)

        if n_points_next > max_samples:
            sample_indices = np.linspace(0, n_points_next - 1, max_samples, dtype=int)
        else:
            sample_indices = np.arange(n_points_next)

        false_neighbors = 0
        valid_points = 0

        # Query 2 nearest neighbors (first is self at distance 0)
        # We need enough neighbors to skip temporally close ones
        k_query = min(min_tsep + 2, n_points_next)
        dists_all, idxs_all = tree.query(embedded_m[sample_indices], k=k_query)

        for si, i in enumerate(sample_indices):
            # Find nearest neighbor respecting Theiler window
            nn_idx = -1
            nn_dist = np.inf
            for j in range(k_query):
                idx = idxs_all[si, j]
                d = dists_all[si, j]
                if abs(idx - i) >= min_tsep and d > 0:
                    nn_idx = idx
                    nn_dist = d
                    break
            
            if nn_idx < 0 or not np.isfinite(nn_dist) or nn_dist == 0:
                continue

            delta_next = abs(data[i + m * tau] - data[nn_idx + m * tau])
            nn_dist_next = np.sqrt(nn_dist ** 2 + delta_next ** 2)

            rel_increase = delta_next / nn_dist
            abs_ratio = nn_dist_next / std_data

            if rel_increase > rtol or abs_ratio > atol:
                false_neighbors += 1

            valid_points += 1

        if valid_points > 0:
            fnn_percent[m - 1] = 100.0 * false_neighbors / valid_points

    return fnn_percent


def find_embedding_dimension(fnn_percent: np.ndarray, threshold: float = 1.0) -> int:
    """
    Find the first embedding dimension whose FNN percentage falls below threshold.
    """
    for m, fnn in enumerate(fnn_percent, start=1):
        if np.isfinite(fnn) and fnn < threshold:
            return m

    finite = np.isfinite(fnn_percent)
    if not np.any(finite):
        return len(fnn_percent)

    return int(np.where(finite)[0][-1] + 1)
