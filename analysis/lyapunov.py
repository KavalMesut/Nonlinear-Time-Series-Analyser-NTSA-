"""
Lyapunov ustel tahmini.

Iki algoritma sunulur, secim kullaniciya aittir:

Wolf algoritmasi (Wolf et al., Physica 16D, 285-317, 1985)
  - Ayrik haritalarda iyi calisir ancak surekli ODE sistemlerinde
    replacement mekanizmasi nedeniyle sistematik olarak overestimate yapabilir.
    Bu Wolf'un bilinen ve belgelenmis bir ozelligidir.

Rosenstein algoritmasi (Rosenstein et al., 1993)
  - Surekli sistemlerde genellikle daha guvenilir sonuclar verir.
  - Map'lerde doyum (saturation) nedeniyle underestimate yapabilir.

Wolf implementasyonu orijinal MATLAB koduna (Alan Wolf / Taehyeun Park) sadiktir,
KD-Tree tabanli komsu arama ile Python'a uyarlanmistir.

Onemli tasarim kararlari (orijinale uygun):
- Ilk komsu aramada aci kisitlamasi YOK (iflag=0)
- Replacement aramada aci kisitlamasi VAR (iflag=1), abs(dot) ile kosinus
- Replacement basarisiz olursa, genisletilmis dismax ile yeniden arama (goto50)
- dismin/dismax gomulme uzayindaki mesafe dagilimdan otomatik kalibre edilir
"""
import numpy as np
from scipy.spatial import cKDTree

from .embedding import embed_timeseries
from .acf import compute_acf
from core.integrators import rk4_step


def _build_kdtree(embedded: np.ndarray) -> cKDTree:
    """Build a KD-Tree for fast neighbor lookup."""
    return cKDTree(embedded)


def estimate_theiler_window(data: np.ndarray, m: int, tau: int,
                            min_window: int = None,
                            max_lag: int = None) -> int:
    """
    Estimate a temporal separation window from the autocorrelation structure.

    Uses the first informative decorrelation event from the ACF:
    - first zero crossing, if present
    - otherwise first lag where ACF drops below 1/e
    - otherwise first local minimum

    The returned window is always at least `max(1, m*tau)`.
    """
    base_window = max(1, m * tau)
    if min_window is not None:
        base_window = max(base_window, int(min_window))

    n = len(data)
    if n < 8:
        return base_window

    if max_lag is None:
        max_lag = min(max(base_window * 8, 64), max(2, n // 4))
    max_lag = min(max_lag, n - 1)
    if max_lag < 2:
        return base_window

    acf = compute_acf(data, max_lag=max_lag)
    if len(acf) < 3:
        return base_window

    candidate = None

    zero_crossings = np.where(acf[1:] <= 0)[0]
    if len(zero_crossings) > 0:
        candidate = int(zero_crossings[0] + 1)
    else:
        below_e = np.where(acf[1:] <= np.exp(-1))[0]
        if len(below_e) > 0:
            candidate = int(below_e[0] + 1)
        else:
            for i in range(1, len(acf) - 1):
                if acf[i] <= acf[i - 1] and acf[i] <= acf[i + 1]:
                    candidate = i
                    break

    if candidate is None:
        return base_window
    return max(base_window, int(candidate))


def _estimate_distance_params(embedded: np.ndarray, tree: cKDTree,
                              min_tsep: int, n_sample: int = 2000) -> tuple:
    """
    Estimate appropriate dismin and dismax from the embedded space.
    
    Strategy: Use the attractor scale (std of embedded coordinates) to set
    dismax as a small fraction of the attractor size, similar to how Wolf
    sets dismax relative to the attractor (e.g., dismax=0.3 for Lorenz with
    attractor diameter ~40).
    
    dismin is set relative to dismax (dismin = dismax / 100).
    
    Returns:
        (dismin, dismax)
    """
    # Compute attractor scale as RMS of per-dimension standard deviations
    # This gives a characteristic length scale of the attractor
    std_per_dim = np.std(embedded, axis=0)
    attractor_scale = np.sqrt(np.sum(std_per_dim**2))
    
    # Wolf's Lorenz example: attractor_scale ≈ 15-20, dismax = 0.3
    # That's roughly 1.5-2% of attractor_scale
    # We use 2% as a good universal default
    dismax = attractor_scale * 0.02
    dismin = dismax / 100.0
    
    return max(dismin, 1e-12), max(dismax, 1e-8)


def _query_valid_neighbors(tree: cKDTree, embedded: np.ndarray,
                           reference_idx: int, min_tsep: int,
                           max_lag: int, n_neighbors: int,
                           initial_k: int = 64,
                           max_k_cap: int = 4096) -> np.ndarray:
    """
    Query valid spatial neighbors while excluding temporally-close samples.

    The query widens progressively until enough valid neighbors are found or
    a practical cap is reached.
    """
    n_points = len(embedded)
    if n_points <= 1:
        return np.array([], dtype=int)

    k_query = min(n_points, max(8, initial_k))
    point = embedded[reference_idx]

    while True:
        dists, idxs = tree.query(point, k=k_query)
        dists = np.atleast_1d(dists)
        idxs = np.atleast_1d(idxs)

        valid = []
        for idx, dist in zip(idxs, dists):
            idx = int(idx)
            if idx == reference_idx:
                continue
            if abs(idx - reference_idx) < min_tsep:
                continue
            if idx + max_lag >= n_points:
                continue
            if dist <= 0:
                continue
            valid.append(idx)
            if len(valid) >= n_neighbors:
                return np.array(valid, dtype=int)

        if k_query >= n_points or k_query >= max_k_cap:
            return np.array(valid, dtype=int)

        k_query = min(n_points, max_k_cap, k_query * 2)


def _find_neighbor_wolf(embedded: np.ndarray, tree: cKDTree,
                        reference_idx: int, min_tsep: int, evolve_steps: int,
                        dismin: float, dismax: float,
                        n_usable: int,
                        direction_vector: np.ndarray = None,
                        oldist: float = None,
                        max_angle_deg: float = 30.0,
                        iflag: int = 0) -> tuple:
    """
    Find a valid neighbor following Wolf's search logic.
    
    Args:
        embedded: embedded phase space points
        tree: KD-Tree for fast neighbor search
        reference_idx: index of the fiducial point
        min_tsep: minimum temporal separation
        evolve_steps: evolution steps
        dismin: minimum allowed distance (absolute)
        dismax: maximum allowed distance (absolute)
        n_usable: last usable index in the time series
        direction_vector: separation vector for angle-preserving replacement
        oldist: old pair distance (for angle computation)
        max_angle_deg: maximum angle for replacement (degrees)
        iflag: 0 = no angle check (initial search), 1 = angle check (replacement)
    
    Returns:
        (best_point_idx, best_distance, best_angle) or (-1, inf, 180) if not found
    """
    n_points = len(embedded)
    reference = embedded[reference_idx]
    
    # Query KD-Tree for candidates within dismax
    candidate_indices = tree.query_ball_point(reference, dismax)
    
    if len(candidate_indices) == 0:
        return -1, np.inf, 180.0
    
    candidate_indices = np.array(candidate_indices)
    
    # Filter: temporal separation from fiducial point (Wolf search.m line 101)
    temporal_mask = np.abs(candidate_indices - reference_idx) >= min_tsep
    # Filter: candidate must not be within 2*evolve of end-of-data (Wolf search.m line 104)
    usable_mask = candidate_indices <= n_usable - 2 * evolve_steps
    # Filter: minimum distance and non-zero
    candidate_vectors = embedded[candidate_indices] - reference
    candidate_distances = np.linalg.norm(candidate_vectors, axis=1)
    dist_mask = (candidate_distances >= dismin) & (candidate_distances > 0)
    
    combined_mask = temporal_mask & usable_mask & dist_mask
    
    if not np.any(combined_mask):
        return -1, np.inf, 180.0
    
    filtered_indices = candidate_indices[combined_mask]
    filtered_distances = candidate_distances[combined_mask]
    filtered_vectors = candidate_vectors[combined_mask]
    
    # Wolf's search uses progressive narrowing: both bstdis and thbest
    # are initialized to dismax and thmax, then each accepted candidate
    # tightens BOTH bounds. A candidate must beat the current best in
    # BOTH distance AND angle (search.m lines 119, 132-138).
    
    if iflag == 1 and direction_vector is not None and oldist is not None and oldist > 0:
        dir_norm = np.linalg.norm(direction_vector)
        if dir_norm > 1e-18:
            dots = np.abs(filtered_vectors @ direction_vector)
            cosines = dots / (filtered_distances * dir_norm)
            cosines = np.clip(cosines, 0.0, 1.0)
            angles = np.degrees(np.arccos(cosines))
            
            # Progressive narrowing: iterate candidates sorted by distance,
            # accepting only if both distance < bstdis AND angle < thbest
            bstdis = dismax
            thbest = max_angle_deg
            best_point = -1
            best_d = np.inf
            best_a = 180.0
            
            # Sort by distance ascending (Wolf iterates through box structure,
            # but the progressive narrowing logic is order-dependent)
            sort_order = np.argsort(filtered_distances)
            for si in sort_order:
                d = filtered_distances[si]
                a = angles[si]
                if d >= bstdis:
                    continue
                if a >= thbest:
                    continue
                # This candidate beats both bounds — accept and narrow
                bstdis = d
                thbest = a
                best_point = int(filtered_indices[si])
                best_d = float(d)
                best_a = float(a)
            
            if best_point >= 0:
                return best_point, best_d, best_a
            else:
                return -1, np.inf, 180.0
    
    # iflag == 0: no angle check, just pick closest (Wolf: tdist < bstdis)
    # Also enforce distance < dismax (bstdis initialized to dismax)
    dist_ok = filtered_distances < dismax
    if not np.any(dist_ok):
        # All within dismax from KD-Tree query, but check strict <
        best_idx = np.argmin(filtered_distances)
        return int(filtered_indices[best_idx]), float(filtered_distances[best_idx]), -1.0
    
    best_idx = np.argmin(filtered_distances)
    return int(filtered_indices[best_idx]), float(filtered_distances[best_idx]), -1.0


def lyapunov_wolf(data: np.ndarray, m: int, tau: int,
                  dt: float = 1.0,
                  initial_neighbor_distance: float = None,
                  replacement_threshold: float = None,
                  max_iterations: int = None,
                  min_tsep: int = None,
                  evolve_steps: int = 1,
                  min_neighbor_distance: float = None,
                  replacement_angle_deg: float = 30.0) -> float:
    """
    Estimate the largest Lyapunov exponent using Wolf's algorithm.
    
    Follows Wolf et al., Physica 16D, 285-317 (1985).
    
    Args:
        data: 1D time series array
        m: embedding dimension
        tau: time delay
        dt: time step between samples
        initial_neighbor_distance: dismax for neighbor search. If None, auto-calibrated.
        replacement_threshold: distance above which replacement is triggered. If None, auto-set.
        max_iterations: maximum number of evolution steps
        min_tsep: minimum temporal separation (Theiler window). Default: max(evolve_steps, m*tau).
        evolve_steps: number of steps to evolve before checking replacement
        min_neighbor_distance: dismin - minimum neighbor distance. If None, auto-calibrated.
        replacement_angle_deg: max angle for replacement (degrees). Default: 30.
    
    Returns:
        Largest Lyapunov exponent in nats per time unit.
    """
    embedded = embed_timeseries(data, m, tau)
    n_points = len(embedded)

    if n_points <= evolve_steps + 1:
        return np.nan

    # Wolf's temporal separation: abs(runner - oldpnt) < evolve (search.m line 101)
    # For scalar experimental data, a larger Theiler window is often needed to
    # avoid selecting same-orbit neighbors that bias the exponent upward.
    if min_tsep is None:
        min_tsep = estimate_theiler_window(
            data, m, tau, min_window=max(evolve_steps, m * tau)
        )

    if max_iterations is None:
        max_iterations = n_points

    # Build KD-Tree
    tree = _build_kdtree(embedded)

    # Auto-calibrate distance parameters from embedded space
    if min_neighbor_distance is None or initial_neighbor_distance is None:
        auto_dismin, auto_dismax = _estimate_distance_params(embedded, tree, min_tsep)
        if min_neighbor_distance is None:
            min_neighbor_distance = auto_dismin
        if initial_neighbor_distance is None:
            initial_neighbor_distance = auto_dismax

    if replacement_threshold is None:
        replacement_threshold = initial_neighbor_distance

    # Wolf: datuse = datcnt - (ndim-1)*tau - evolve (1-indexed)
    # oldpnt >= datuse means stop. Max valid oldpnt = datuse - 1.
    # In 0-indexed: n_usable = n_points - 1 - (m-1)*tau - evolve_steps - 1
    # But embedded already accounts for (m-1)*tau, so:
    # n_usable = n_points - evolve_steps - 1  (but -1 more for 0-index correction)
    n_usable = n_points - evolve_steps - 1

    lyapunov_sum = 0.0
    iterations = 0
    current_idx = 0

    # === MAIN LOOP (Wolf's goto50 equivalent) ===
    while current_idx <= n_usable:
        # --- Find initial neighbor (iflag=0, no angle constraint) ---
        search_dismax = initial_neighbor_distance
        neighbor_idx = -1
        
        while neighbor_idx < 0:
            neighbor_idx, current_dist, _ = _find_neighbor_wolf(
                embedded, tree, current_idx, min_tsep, evolve_steps,
                min_neighbor_distance, search_dismax, n_usable,
                iflag=0
            )
            if neighbor_idx < 0:
                search_dismax *= 2.0
                if search_dismax > np.std(embedded[:, 0]) * 100:
                    break
        
        if neighbor_idx < 0:
            current_idx += evolve_steps
            continue

        disold = current_dist

        # === EVOLUTION LOOP (Wolf's goto60 equivalent) ===
        while True:
            current_idx += evolve_steps
            neighbor_idx += evolve_steps
            
            if current_idx > n_usable:
                break
            
            if neighbor_idx >= n_points:
                current_idx -= evolve_steps
                break
            
            disnew = np.linalg.norm(embedded[current_idx] - embedded[neighbor_idx])
            
            # Wolf: SUM = SUM + log(disnew/disold) — no filter (fet.m line 75)
            # disnew==0 would give -inf but is extremely rare in practice
            if disold > 0 and disnew > 0:
                lyapunov_sum += np.log(disnew / disold)
            elif disold > 0:
                # disnew == 0: degenerate case, use a very small value
                lyapunov_sum += np.log(1e-18 / disold)
            iterations += 1
            
            if iterations >= max_iterations:
                break
            
            # Check if replacement is needed
            if disnew <= replacement_threshold:
                disold = disnew
                continue
            
            # --- Replacement search (iflag=1, with angle constraint) ---
            direction = embedded[current_idx] - embedded[neighbor_idx]
            
            best_neighbor, best_dist, _ = _find_neighbor_wolf(
                embedded, tree, current_idx, min_tsep, evolve_steps,
                min_neighbor_distance, initial_neighbor_distance, n_usable,
                direction_vector=direction,
                oldist=disnew,
                max_angle_deg=replacement_angle_deg,
                iflag=1
            )
            
            if best_neighbor >= 0:
                neighbor_idx = best_neighbor
                disold = best_dist
            else:
                # Wolf's goto50: replacement failed, break to find new initial neighbor
                break
        
        if iterations >= max_iterations:
            break

    if iterations == 0:
        return np.nan

    total_time = iterations * evolve_steps * dt
    return lyapunov_sum / total_time


def lyapunov_wolf_detailed(data: np.ndarray, m: int, tau: int,
                           dt: float = 1.0,
                           initial_neighbor_distance: float = None,
                           replacement_threshold: float = None,
                           max_iterations: int = None,
                           min_tsep: int = None,
                           evolve_steps: int = 1,
                           min_neighbor_distance: float = None,
                           replacement_angle_deg: float = 30.0) -> dict:
    """
    Same as lyapunov_wolf but returns detailed results including:
    - le: Lyapunov exponent
    - std: standard deviation of per-step estimates
    - convergence: relative change in last 20% of running estimate
    - le_per_step: array of per-step log(disnew/disold) values
    - running_le: running Lyapunov estimate at each step
    """
    embedded = embed_timeseries(data, m, tau)
    n_points = len(embedded)
    
    nan_result = {'le': np.nan, 'std': np.nan, 'convergence': np.nan,
                  'le_per_step': np.array([]), 'running_le': np.array([])}

    if n_points <= evolve_steps + 1:
        return nan_result

    # Wolf's temporal separation: abs(runner - oldpnt) < evolve
    if min_tsep is None:
        min_tsep = estimate_theiler_window(
            data, m, tau, min_window=max(evolve_steps, m * tau)
        )
    if max_iterations is None:
        max_iterations = n_points

    tree = _build_kdtree(embedded)

    if min_neighbor_distance is None or initial_neighbor_distance is None:
        auto_dismin, auto_dismax = _estimate_distance_params(embedded, tree, min_tsep)
        if min_neighbor_distance is None:
            min_neighbor_distance = auto_dismin
        if initial_neighbor_distance is None:
            initial_neighbor_distance = auto_dismax

    if replacement_threshold is None:
        replacement_threshold = initial_neighbor_distance

    n_usable = n_points - evolve_steps - 1

    lyapunov_sum = 0.0
    iterations = 0
    current_idx = 0
    le_per_step = []
    running_le = []

    while current_idx <= n_usable:
        search_dismax = initial_neighbor_distance
        neighbor_idx = -1
        
        while neighbor_idx < 0:
            neighbor_idx, current_dist, _ = _find_neighbor_wolf(
                embedded, tree, current_idx, min_tsep, evolve_steps,
                min_neighbor_distance, search_dismax, n_usable, iflag=0
            )
            if neighbor_idx < 0:
                search_dismax *= 2.0
                if search_dismax > np.std(embedded[:, 0]) * 100:
                    break
        
        if neighbor_idx < 0:
            current_idx += evolve_steps
            continue

        disold = current_dist

        while True:
            current_idx += evolve_steps
            neighbor_idx += evolve_steps
            
            if current_idx > n_usable:
                break
            if neighbor_idx >= n_points:
                current_idx -= evolve_steps
                break
            
            disnew = np.linalg.norm(embedded[current_idx] - embedded[neighbor_idx])
            
            # Wolf: SUM = SUM + log(disnew/disold) — no filter (fet.m line 75)
            if disold > 0 and disnew > 0:
                log_ratio = np.log(disnew / disold)
            elif disold > 0:
                log_ratio = np.log(1e-18 / disold)
            else:
                log_ratio = 0.0
            lyapunov_sum += log_ratio
            iterations += 1
            le_per_step.append(log_ratio)
            total_time = iterations * evolve_steps * dt
            running_le.append(lyapunov_sum / total_time)
            
            if iterations >= max_iterations:
                break
            
            if disnew <= replacement_threshold:
                disold = disnew
                continue
            
            direction = embedded[current_idx] - embedded[neighbor_idx]
            best_neighbor, best_dist, _ = _find_neighbor_wolf(
                embedded, tree, current_idx, min_tsep, evolve_steps,
                min_neighbor_distance, initial_neighbor_distance, n_usable,
                direction_vector=direction, oldist=disnew,
                max_angle_deg=replacement_angle_deg, iflag=1
            )
            
            if best_neighbor >= 0:
                neighbor_idx = best_neighbor
                disold = best_dist
            else:
                break
        
        if iterations >= max_iterations:
            break

    if iterations == 0:
        return nan_result

    total_time = iterations * evolve_steps * dt
    le = lyapunov_sum / total_time
    
    le_arr = np.array(le_per_step)
    running_arr = np.array(running_le)
    
    step_le_values = le_arr / (evolve_steps * dt)
    std = float(np.std(step_le_values))
    
    if len(running_arr) >= 10:
        last_20 = running_arr[int(0.8 * len(running_arr)):]
        convergence = float(np.std(last_20) / (np.abs(np.mean(last_20)) + 1e-18))
    else:
        convergence = np.nan
    
    return {
        'le': le,
        'std': std,
        'convergence': convergence,
        'le_per_step': le_arr,
        'running_le': running_arr
    }


def lyapunov_rosenstein(data: np.ndarray, m: int, tau: int,
                        dt: float = 1.0,
                        min_tsep: int = None, max_lag: int = None,
                        max_samples: int = 5000) -> tuple:
    """
    Estimate largest Lyapunov exponent using Rosenstein's algorithm.
    
    Uses KD-Tree for fast nearest neighbor search and sampling for performance.

    Args:
        data: 1D time series
        m: embedding dimension
        tau: time delay
        dt: time step
        min_tsep: Theiler window (default: m * tau)
        max_lag: maximum lag for divergence tracking
        max_samples: maximum number of fiducial points to sample

    Returns:
        (time_steps, mean_divergence)
    """
    embedded = embed_timeseries(data, m, tau)
    n_points = len(embedded)

    if min_tsep is None:
        min_tsep = estimate_theiler_window(data, m, tau)

    if max_lag is None:
        max_lag = min(n_points // 10, 300)

    max_lag = min(max_lag, n_points - 1)

    tree = _build_kdtree(embedded)
    
    n_fiducial = min(max_samples, n_points - max_lag)
    if n_fiducial <= 0:
        return np.arange(max_lag) * dt, np.full(max_lag, np.nan)
    
    if n_fiducial < n_points - max_lag:
        fiducial_indices = np.linspace(0, n_points - max_lag - 1, n_fiducial, dtype=int)
    else:
        fiducial_indices = np.arange(n_points - max_lag)

    divergence_sums = np.zeros(max_lag)
    divergence_counts = np.zeros(max_lag)

    # Find nearest neighbors for all fiducial points at once
    # Query enough neighbors to find one outside Theiler window
    k_query = min(max(32, 2 * min_tsep + 20), n_points)
    all_dists, all_idxs = tree.query(embedded[fiducial_indices], k=k_query)

    # Build neighbor index array
    nn_indices = np.full(len(fiducial_indices), -1, dtype=int)
    for si, i in enumerate(fiducial_indices):
        for j in range(k_query):
            idx = int(all_idxs[si, j])
            if abs(idx - i) >= min_tsep and idx + max_lag < n_points and all_dists[si, j] > 0:
                nn_indices[si] = idx
                break

        if nn_indices[si] >= 0:
            continue

        # Fallback: search the full tree if the bounded query did not find a valid
        # neighbor outside the Theiler window.
        dists_full, idxs_full = tree.query(embedded[i], k=n_points)
        for idx, dist in zip(np.atleast_1d(idxs_full), np.atleast_1d(dists_full)):
            idx = int(idx)
            if abs(idx - i) >= min_tsep and idx + max_lag < n_points and dist > 0:
                nn_indices[si] = idx
                break
    
    valid_mask = nn_indices >= 0
    valid_fid = fiducial_indices[valid_mask]
    valid_nn = nn_indices[valid_mask]
    
    if len(valid_fid) == 0:
        return np.arange(max_lag) * dt, np.full(max_lag, np.nan)

    # Vectorized divergence computation for each lag
    for k in range(max_lag):
        fi = valid_fid + k
        ni = valid_nn + k
        # Check bounds
        in_bounds = (fi < n_points) & (ni < n_points)
        if not np.any(in_bounds):
            break
        fi_ok = fi[in_bounds]
        ni_ok = ni[in_bounds]
        diffs = embedded[fi_ok] - embedded[ni_ok]
        dists = np.linalg.norm(diffs, axis=1)
        pos = dists > 0
        if np.any(pos):
            divergence_sums[k] = np.sum(np.log(dists[pos]))
            divergence_counts[k] = np.sum(pos)

    mean_divergence = np.full(max_lag, np.nan)
    valid_k = divergence_counts > 0
    mean_divergence[valid_k] = divergence_sums[valid_k] / divergence_counts[valid_k]

    time_steps = np.arange(max_lag) * dt
    return time_steps, mean_divergence


def lyapunov_kantz(data: np.ndarray, m: int, tau: int,
                   dt: float = 1.0,
                   min_tsep: int = None, max_lag: int = None,
                   max_samples: int = 1000, n_neighbors: int = 20,
                   min_neighbors: int = 5) -> tuple:
    """
    Estimate largest Lyapunov exponent using Kantz's divergence method.

    Returns the average log-divergence curve; slope fitting is handled by the
    same helper used for Rosenstein.
    """
    embedded = embed_timeseries(data, m, tau)
    n_points = len(embedded)

    if min_tsep is None:
        min_tsep = estimate_theiler_window(data, m, tau)

    if max_lag is None:
        max_lag = min(n_points // 10, 300)
    max_lag = min(max_lag, n_points - 1)

    if n_points <= 2 or max_lag <= 1:
        return np.arange(max_lag) * dt, np.full(max_lag, np.nan)

    tree = _build_kdtree(embedded)

    n_fiducial = min(max_samples, n_points - max_lag)
    if n_fiducial <= 0:
        return np.arange(max_lag) * dt, np.full(max_lag, np.nan)

    if n_fiducial < n_points - max_lag:
        fiducial_indices = np.linspace(0, n_points - max_lag - 1, n_fiducial, dtype=int)
    else:
        fiducial_indices = np.arange(n_points - max_lag)

    neighbor_sets = []
    valid_fiducials = []
    for idx in fiducial_indices:
        neighbors = _query_valid_neighbors(
            tree, embedded, int(idx), min_tsep, max_lag, n_neighbors
        )
        if len(neighbors) >= min_neighbors:
            valid_fiducials.append(int(idx))
            neighbor_sets.append(neighbors)

    if not valid_fiducials:
        return np.arange(max_lag) * dt, np.full(max_lag, np.nan)

    divergence_sums = np.zeros(max_lag)
    divergence_counts = np.zeros(max_lag)

    for fiducial_idx, neighbors in zip(valid_fiducials, neighbor_sets):
        for k in range(max_lag):
            fi = fiducial_idx + k
            ni = neighbors + k
            in_bounds = (fi < n_points) & (ni < n_points)
            if not np.any(in_bounds):
                break
            ni_ok = ni[in_bounds]
            diffs = embedded[fi] - embedded[ni_ok]
            dists = np.linalg.norm(diffs, axis=1)
            pos = dists > 0
            if np.any(pos):
                logs = np.log(dists[pos])
                divergence_sums[k] += np.sum(logs)
                divergence_counts[k] += len(logs)

    mean_divergence = np.full(max_lag, np.nan)
    valid_k = divergence_counts > 0
    mean_divergence[valid_k] = divergence_sums[valid_k] / divergence_counts[valid_k]

    time_steps = np.arange(max_lag) * dt
    return time_steps, mean_divergence


def estimate_lyapunov_from_curve(time_steps: np.ndarray, divergence: np.ndarray,
                                 fit_start: int = None, fit_end: int = None,
                                 auto_fit: bool = True) -> float:
    """
    Estimate a Lyapunov exponent from a divergence curve using a linear fit.
    
    If auto_fit=True and fit_start/fit_end are not given, automatically finds
    the most linear region using a sliding window R² maximization.
    The fit region starts from index 0 (or 1 if index 0 is transient).
    """
    valid = ~np.isnan(divergence)
    time_valid = time_steps[valid]
    div_valid = divergence[valid]

    if len(time_valid) < 2:
        return np.nan

    if fit_start is not None or fit_end is not None:
        if fit_start is None:
            fit_start = 0
        if fit_end is None:
            fit_end = len(time_valid)
        fit_start = min(fit_start, len(time_valid) - 2)
        fit_end = min(fit_end, len(time_valid))
        if fit_end <= fit_start + 1:
            return np.nan
        coeffs = np.polyfit(time_valid[fit_start:fit_end], div_valid[fit_start:fit_end], 1)
        return coeffs[0]
    
    if auto_fit and len(time_valid) >= 5:
        return _auto_fit_linear_region(time_valid, div_valid)[0]
    
    coeffs = np.polyfit(time_valid, div_valid, 1)
    return coeffs[0]


def _auto_fit_linear_region(time_valid: np.ndarray, div_valid: np.ndarray) -> tuple:
    """
    Find the best linear region in the divergence curve for Lyapunov estimation.
    
    Two-phase approach:
    1. Full curve fit (lag 1 to end). If R² >= 0.98, accept (no saturation).
    2. Otherwise, detect saturation using rolling slope ratio with adaptive
       window size, then fit the pre-saturation region.
    
    Returns: (slope, r2, start_idx, end_idx)
    """
    n = len(time_valid)
    if n < 5:
        coeffs = np.polyfit(time_valid, div_valid, 1)
        return coeffs[0], np.nan, 0, n
    
    start_skip = 1 if n > 5 else 0
    fit_t = time_valid[start_skip:]
    fit_d = div_valid[start_skip:]
    n_fit = len(fit_t)
    
    if n_fit < 3:
        coeffs = np.polyfit(time_valid, div_valid, 1)
        return coeffs[0], np.nan, 0, n
    
    # Phase 1: Full curve fit
    full_c = np.polyfit(fit_t, fit_d, 1)
    full_f = np.polyval(full_c, fit_t)
    full_sr = np.sum((fit_d - full_f) ** 2)
    full_st = np.sum((fit_d - np.mean(fit_d)) ** 2)
    full_r2 = 1.0 - full_sr / full_st if full_st > 1e-30 else 0.0
    
    if full_r2 >= 0.98 and full_c[0] > 0:
        return full_c[0], float(full_r2), start_skip, n
    
    # Phase 2: Rolling slope ratio saturation detection
    # Ilk birkac noktadan baslangic egimi hesapla, sonra kayan pencere ile
    # egimin %25'in altina dustugu yeri bul (doyuma ulasti).
    # Birden fazla pencere boyutu deneyerek en iyi R^2 veren fit araligini sec.
    init_len = max(3, min(5, n_fit // 10 + 3))
    c_init = np.polyfit(fit_t[:init_len], fit_d[:init_len], 1)
    initial_slope = c_init[0]
    
    if initial_slope <= 0:
        return full_c[0], float(full_r2), start_skip, n
    
    # Birden fazla pencere boyutu dene, her biri icin saturation noktasi bul
    best_fit_r2 = -1.0
    best_fit_result = (full_c[0], float(full_r2), start_skip, n)
    
    win_sizes = set()
    for frac in [10, 15, 20, 25]:
        ws = max(3, n_fit // frac)
        win_sizes.add(ws)
    win_sizes = sorted(win_sizes)
    
    for win_size in win_sizes:
        saturation_idx = n_fit
        for i in range(init_len, n_fit - win_size + 1):
            local_c = np.polyfit(fit_t[i:i + win_size], fit_d[i:i + win_size], 1)
            ratio = local_c[0] / initial_slope
            if ratio < 0.25:
                saturation_idx = i
                break
        
        saturation_idx = max(saturation_idx, init_len)
        fit_end = min(saturation_idx, n_fit)
        
        if fit_end < 3:
            continue
        
        c = np.polyfit(fit_t[:fit_end], fit_d[:fit_end], 1)
        f = np.polyval(c, fit_t[:fit_end])
        sr = np.sum((fit_d[:fit_end] - f) ** 2)
        st = np.sum((fit_d[:fit_end] - np.mean(fit_d[:fit_end])) ** 2)
        r2 = 1.0 - sr / st if st > 1e-30 else 0.0
        
        if c[0] > 0 and r2 > best_fit_r2:
            best_fit_r2 = r2
            best_fit_result = (c[0], float(r2), start_skip, start_skip + fit_end)
    
    if best_fit_result[0] > 0:
        return best_fit_result
    
    return full_c[0], float(full_r2), start_skip, n


def estimate_lyapunov_from_curve_detailed(time_steps: np.ndarray, 
                                           divergence: np.ndarray) -> dict:
    """
    Returns detailed fit information including R² value.
    
    Returns:
        dict with keys: 'le', 'r2', 'fit_start', 'fit_end'
    """
    valid = ~np.isnan(divergence)
    time_valid = time_steps[valid]
    div_valid = divergence[valid]

    if len(time_valid) < 5:
        le = estimate_lyapunov_from_curve(time_steps, divergence)
        return {'le': le, 'r2': np.nan, 'fit_start': 0, 'fit_end': len(time_valid)}

    slope, r2, start, end = _auto_fit_linear_region(time_valid, div_valid)

    return {
        'le': slope,
        'r2': r2,
        'fit_start': start,
        'fit_end': end
    }


# =====================================================================
# FULL LYAPUNOV SPECTRUM — Sano-Sawada (1985) / Eckmann-Ruelle (1985)
# Gomme uzayinda lokal Jacobian + ridge regresyon + QR ortonormalizasyon
# ile tum m adet Lyapunov ustelini hesaplar.
#
# Onceki implementasyonda tespit edilen hatalar ve duzeltmeler:
#   1) Jacobian tahmini: standart lstsq yerine ridge regresyon (daha
#      kararli, kotu kosullu Jacobian'larda daha az varyans).
#   2) Gecersiz Jacobian (komsusuz adim) yerine None dondurulup skip:
#      np.eye(m) ile doldurmak lambda = 0 yonunde baskiya yol acar.
#   3) Zaman normalizasyonu: her gomme adimi 1 ornek = dt saniye.
#      tau sadece gomme ici komsu gecikmesi, iterasyon adim boyutu degil.
#   4) Son siralamayi kaldirdik: QR ust-ucgen yapi sayesinde diag(R)[0]
#      zaten en buyuk buyume hizini takip eder; ancak gurultulu veri icin
#      son siralama birakildi (farkli olculerde birikimli baskiyi onler).
# =====================================================================

def _estimate_jacobian_ridge(embedded: np.ndarray, tree: cKDTree,
                             idx: int, m: int,
                             k_neighbors: int,
                             min_tsep: int,
                             ridge_alpha: float = 1e-6):
    """
    Ridge regresyon ile lokal Jacobian tahmini.

    Bir adim sonraki gomme vektoru sapmasini mevcut sapmayla iliskilendirir:
        dy(n+1) ≈ J * dy(n)
    Cozum: J^T = (dx^T dx + alpha I)^{-1} dx^T dy

    Args:
        embedded: gomulu faz uzayi, shape (n_points, m)
        tree: KD-Tree
        idx: referans nokta indeksi
        m: gomme boyutu
        k_neighbors: kullanilacak komsu sayisi
        min_tsep: minimum zamansal ayrim (Theiler penceresi)
        ridge_alpha: ridge duzenleyici katsayi

    Returns:
        m x m Jacobian matrisi, ya da None (yetersiz komsu)
    """
    n_points = len(embedded)

    if idx + 1 >= n_points:
        return None

    # Theiler filtreli komsu ara — yeterli havuz birakmak icin 3x sorgula
    k_query = min(k_neighbors * 3 + min_tsep + 10, n_points)
    dists, idxs = tree.query(embedded[idx], k=k_query)

    valid = []
    for j in range(len(idxs)):
        ni = int(idxs[j])
        if ni == idx:
            continue
        if abs(ni - idx) < min_tsep:
            continue
        if ni + 1 >= n_points:
            continue
        if dists[j] < 1e-14:   # sayisal kopya / esit nokta atla
            continue
        valid.append(ni)
        if len(valid) >= k_neighbors:
            break

    # En az m komsu lazim; aksi halde iyi sartlı degil, adimi atla
    if len(valid) < m:
        return None

    valid_arr = np.array(valid)
    dx = embedded[valid_arr] - embedded[idx]              # (k, m)
    dy = embedded[valid_arr + 1] - embedded[idx + 1]      # (k, m)

    # Ridge: (dx^T dx + alpha*I) J^T = dx^T dy
    A = dx.T @ dx + ridge_alpha * np.eye(m)   # (m, m)
    B = dx.T @ dy                              # (m, m)
    try:
        J_T = np.linalg.solve(A, B)           # (m, m)
        return J_T.T
    except np.linalg.LinAlgError:
        return None


def lyapunov_spectrum(data: np.ndarray, m: int, tau: int,
                      dt: float = 1.0,
                      n_exponents: int = None,
                      min_tsep: int = None,
                      transient_frac: float = 0.10,
                      k_neighbors: int = None,
                      ridge_alpha: float = 1e-6) -> dict:
    """
    Full Lyapunov spektrumu — Sano-Sawada (1985) / Eckmann-Ruelle (1986).

    Gomme uzayinda ridge regresyon tabanli lokal Jacobian tahmini ve
    periyodik QR ortonormalizasyonu (Gram-Schmidt) ile tum m adet
    Lyapunov ustelini hesaplar.

    Onceki implementasyona gore temel degisiklikler:
    - np.eye fallback kaldirildi: yetersiz komsuda adim atlanir (skip),
      boylece sifir baskisi olmaz.
    - Ridge regresyon: kotu kosullu Jacobian'larda lstsq'dan cok daha
      kararli; kucuk alpha degerleri ls'ye yakinsir.
    - Transient varsayilani %5 → %10 (kisa seriler icin daha guvenli).

    Args:
        data: 1D zaman serisi
        m: gomme boyutu
        tau: zaman gecikmesi
        dt: ornekleme araligi (saniye)
        n_exponents: hesaplanacak ustel sayisi (varsayilan: m)
        min_tsep: Theiler penceresi (varsayilan: m*tau)
        transient_frac: atlanacak bas kisim orani (0-1)
        k_neighbors: Jacobian icin komsu sayisi (varsayilan: max(2m+2, 10))
        ridge_alpha: ridge duzenleyici (varsayilan: 1e-6)

    Returns:
        dict:
            'exponents'           – shape (n_exponents,), buyukten kucuge [nats/s]
            'exponents_convergence' – shape (n_checkpoints, n_exponents)
            'kaplan_yorke_dim'    – float
            'kolmogorov_sinai'    – float [nats/s]
            'n_steps'             – kullanilan adim sayisi
            'n_skipped'           – atlanan adim sayisi (komsu bulunamadi)
    """
    embedded = embed_timeseries(data, m, tau)
    n_points = len(embedded)

    if n_exponents is None:
        n_exponents = m
    n_exponents = min(n_exponents, m)

    if min_tsep is None:
        min_tsep = max(m * tau, 1)

    if k_neighbors is None:
        k_neighbors = max(2 * m + 2, 10)

    _nan_result = {
        'exponents': np.full(n_exponents, np.nan),
        'exponents_convergence': np.array([]),
        'kaplan_yorke_dim': np.nan,
        'kolmogorov_sinai': np.nan,
        'n_steps': 0,
        'n_skipped': 0,
    }

    tree = _build_kdtree(embedded)

    start_idx = max(1, int(n_points * transient_frac))
    end_idx = n_points - 2   # idx+1 icin yer birak

    if end_idx <= start_idx + m:
        return _nan_result

    # Baslangic ortogonal bazisi
    Q = np.eye(m, n_exponents)   # (m, n_exponents)
    lyap_sums = np.zeros(n_exponents)
    n_steps = 0
    n_skipped = 0
    convergence = []

    for idx in range(start_idx, end_idx):
        J = _estimate_jacobian_ridge(
            embedded, tree, idx, m,
            k_neighbors=k_neighbors,
            min_tsep=min_tsep,
            ridge_alpha=ridge_alpha,
        )

        if J is None:
            # Yetersiz komsu: bu adimi atla, bias ekleme
            n_skipped += 1
            continue

        # Ortogonal baziyi Jacobian ile ilerlet ve yeniden ortonormalize et
        M = J @ Q                                      # (m, n_exponents)
        Q, R = np.linalg.qr(M, mode='reduced')        # Q:(m,ne), R:(ne,ne)

        # Buyume oranlarini topla (log|diag(R)|)
        diag = np.maximum(np.abs(np.diag(R)), 1e-300)
        lyap_sums += np.log(diag)
        n_steps += 1

        if n_steps % 100 == 0:
            convergence.append((lyap_sums / (n_steps * dt)).copy())

    if n_steps < 10:
        return _nan_result

    exponents = lyap_sums / (n_steps * dt)
    # QR ust-ucgen yapisindan dolayi sira genellikle buyukten kucuge gelir,
    # ama gurultulu veride garantilemek icin son siralama yapilir.
    exponents = np.sort(exponents)[::-1]

    ky_dim = _kaplan_yorke_dimension(exponents)
    ks_entropy = float(np.sum(exponents[exponents > 0]))
    conv_arr = np.array(convergence) if convergence else np.array([])

    return {
        'exponents': exponents,
        'exponents_convergence': conv_arr,
        'kaplan_yorke_dim': ky_dim,
        'kolmogorov_sinai': ks_entropy,
        'n_steps': n_steps,
        'n_skipped': n_skipped,
    }


def kaplan_yorke_dimension(exponents: np.ndarray) -> float:
    """
    Public wrapper for Kaplan-Yorke dimension.

    Args:
        exponents: Lyapunov eksponenleri, buyukten kucuge siralanmis

    Returns:
        D_KY float
    """
    return _kaplan_yorke_dimension(exponents)


# ---------------------------------------------------------------------------
# Benettin (1980) — ODE icin altin standart Lyapunov spektrumu
# ---------------------------------------------------------------------------

def _numerical_jacobian(ode_func, t, y, eps=1e-7):
    """Merkezi farklarla sayisal Jacobian (J[i,j] = df_i/dy_j)."""
    n = len(y)
    J = np.empty((n, n))
    for j in range(n):
        e = np.zeros(n)
        e[j] = eps
        f_plus = np.asarray(ode_func(t, y + e))
        f_minus = np.asarray(ode_func(t, y - e))
        J[:, j] = (f_plus - f_minus) / (2.0 * eps)
    return J


def lyapunov_benettin(ode_func,
                      y0,
                      t_span=(0.0, 100.0),
                      dt: float = 0.01,
                      transient: int = 2000,
                      n_exponents: int = None,
                      qr_interval: int = 1,
                      jacobian_func=None,
                      jacobian_eps: float = 1e-7) -> dict:
    """
    Benettin et al. (1980) Lyapunov spektrumu — ODE icin altin standart.

    Trajektori (y) + variational denklem (Q, n x n_exponents) eszamanli RK4
    ile entegre edilir. Periyodik QR ortonormalizasyonuyla biriken log(diag(R))
    degerleri toplam zamana bolunerek ustel tahmini elde edilir.

    Embedding YOK: gercek Jacobian kullanildigi icin Sano-Sawada/Eckmann-Ruelle'in
    lokal Jacobian tahmin hatasi yoktur. CSV verisi ile calismaz; sadece denklem
    bilindigi durumlarda kullanilir (built-in sistemler, Custom ODE).

    Args:
        ode_func: f(t, y) -> dy/dt fonksiyonu, dim n
        y0: baslangic kosulu, shape (n,)
        t_span: (t_start, t_end)
        dt: zaman adimi
        transient: Q hesabi baslamadan once atlanacak adim sayisi
        n_exponents: hesaplanacak ustel sayisi (varsayilan: n, yani tam spektrum)
        qr_interval: kac adimda bir QR yapilsin (1 = her adim, daha guvenli)
        jacobian_func: opsiyonel J(t, y) -> n x n. None ise sayisal merkezi fark.
        jacobian_eps: sayisal Jacobian icin perturbasyon

    Returns:
        dict:
            'exponents'           – buyukten kucuge sirali (n_exponents,)
            'exponents_convergence' – her QR'de cari tahmin (n_qr, n_exponents)
            'kaplan_yorke_dim'    – D_KY
            'kolmogorov_sinai'    – pozitif ustellerin toplami (h_KS)
            'n_steps'             – Benettin'in cevirdigi adim sayisi (transient sonrasi)
            'method'              – 'Benettin'
    """
    y = np.asarray(y0, dtype=float).copy()
    n = y.size
    if n_exponents is None:
        n_exponents = n
    n_exponents = max(1, min(int(n_exponents), n))

    t_start, t_end = t_span
    n_steps_total = int((t_end - t_start) / dt)
    transient = int(max(0, transient))
    if transient >= n_steps_total:
        raise ValueError(f"transient ({transient}) >= total steps ({n_steps_total})")

    # 1. Transient: sadece y'yi entegre et, Q hesaplama
    t = float(t_start)
    for _ in range(transient):
        y = rk4_step(ode_func, t, y, dt)
        t += dt

    # 2. Q'yu identity olarak baslat
    Q = np.eye(n, n_exponents, dtype=float)

    def jac_at(tt, yy):
        if jacobian_func is not None:
            return np.asarray(jacobian_func(tt, yy), dtype=float)
        return _numerical_jacobian(ode_func, tt, yy, eps=jacobian_eps)

    log_diag_sum = np.zeros(n_exponents)
    convergence_list = []
    n_active = n_steps_total - transient

    # 3. Birlestirilmis RK4 + periyodik QR
    for step in range(n_active):
        # k1
        dy1 = np.asarray(ode_func(t, y))
        dQ1 = jac_at(t, y) @ Q
        # k2
        y2 = y + 0.5 * dt * dy1
        Q2 = Q + 0.5 * dt * dQ1
        dy2 = np.asarray(ode_func(t + 0.5 * dt, y2))
        dQ2 = jac_at(t + 0.5 * dt, y2) @ Q2
        # k3
        y3 = y + 0.5 * dt * dy2
        Q3 = Q + 0.5 * dt * dQ2
        dy3 = np.asarray(ode_func(t + 0.5 * dt, y3))
        dQ3 = jac_at(t + 0.5 * dt, y3) @ Q3
        # k4
        y4 = y + dt * dy3
        Q4 = Q + dt * dQ3
        dy4 = np.asarray(ode_func(t + dt, y4))
        dQ4 = jac_at(t + dt, y4) @ Q4

        y = y + (dt / 6.0) * (dy1 + 2.0 * dy2 + 2.0 * dy3 + dy4)
        Q = Q + (dt / 6.0) * (dQ1 + 2.0 * dQ2 + 2.0 * dQ3 + dQ4)
        t += dt

        # Periyodik QR — Q'yu yeniden ortonormalle, R'nin diagonalini biriktir
        if (step + 1) % qr_interval == 0:
            Q_new, R = np.linalg.qr(Q)
            # numpy QR isaret konvansiyonu: R diagonalini pozitife zorla
            sign = np.sign(np.diag(R))
            sign[sign == 0] = 1.0
            Q = Q_new * sign  # her sutuna isaretini uygula (broadcast)
            R_diag = np.abs(np.diag(R))
            R_diag = np.maximum(R_diag, 1e-300)  # log(0) korumasi
            log_diag_sum += np.log(R_diag)

            elapsed_t = (step + 1) * dt
            convergence_list.append(log_diag_sum / elapsed_t)

    total_t = n_active * dt
    if total_t <= 0:
        raise ValueError("Benettin: total integration time <= 0")
    exponents = log_diag_sum / total_t
    # Buyukten kucuge sirala
    order = np.argsort(exponents)[::-1]
    exponents_sorted = exponents[order]

    # Convergence dizisini ayni siralamaya goturmuyoruz (zamansal akış icin orijinal kalsin)
    convergence_arr = np.array(convergence_list) if convergence_list else np.empty((0, n_exponents))

    ky_dim = _kaplan_yorke_dimension(exponents_sorted)
    ks_entropy = float(np.sum(exponents_sorted[exponents_sorted > 0]))

    return {
        'exponents': exponents_sorted,
        'exponents_convergence': convergence_arr,
        'kaplan_yorke_dim': ky_dim,
        'kolmogorov_sinai': ks_entropy,
        'n_steps': n_active,
        'method': 'Benettin',
    }


def _kaplan_yorke_dimension(exponents: np.ndarray) -> float:
    """
    Kaplan-Yorke boyutu hesapla.
    
    D_KY = j + (sum_{i=1}^{j} lambda_i) / |lambda_{j+1}|
    
    j: kumulatif toplamin hala pozitif oldugu en buyuk indeks.
    """
    n = len(exponents)
    if n == 0 or exponents[0] <= 0:
        return 0.0
    
    cumsum = np.cumsum(exponents)
    
    # j: cumsum[j] >= 0 olan en buyuk indeks
    j = -1
    for i in range(n):
        if cumsum[i] >= 0:
            j = i
        else:
            break
    
    if j < 0:
        return 0.0
    if j >= n - 1:
        return float(n)
    
    # D_KY = (j+1) + cumsum[j] / |exponents[j+1]|
    if abs(exponents[j + 1]) < 1e-15:
        return float(j + 1)
    
    return float(j + 1) + cumsum[j] / abs(exponents[j + 1])
