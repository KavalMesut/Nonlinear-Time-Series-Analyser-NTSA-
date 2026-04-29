"""
Example: Complete analysis workflow for Lorenz system
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.generators import generate_lorenz
from analysis import (
    compute_acf,
    compute_pacf,
    compute_fft,
    compute_ami, find_first_minimum,
    compute_fnn, find_embedding_dimension,
    embed_timeseries,
    lyapunov_rosenstein, estimate_lyapunov_from_curve,
    correlation_dimension, estimate_dimension_from_correlation
)
import numpy as np

print("=" * 70)
print("COMPLETE ANALYSIS EXAMPLE: LORENZ ATTRACTOR")
print("=" * 70)

# 1. Generate time series
print("\n[1] Generating Lorenz time series...")
ts = generate_lorenz(t_span=(0, 100), dt=0.01, sigma=10.0, rho=28.0, beta=8.0/3.0)
print(f"    Generated {len(ts)} points (dt={ts.dt})")
print(f"    Metadata: {ts.metadata}")

# Remove transient
data = ts.data[2000:]
print(f"    After removing transient: {len(data)} points")

# 2. Linear analysis
print("\n[2] Linear Analysis")
print("    " + "-" * 66)

# ACF
acf = compute_acf(data, max_lag=100)
print(f"    ACF computed: {len(acf)} lags")
print(f"    ACF[0]={acf[0]:.4f}, ACF[1]={acf[1]:.4f}, ACF[10]={acf[10]:.4f}")

# PACF
pacf = compute_pacf(data, max_lag=50)
print(f"    PACF computed: {len(pacf)} lags")

# FFT
freqs, power = compute_fft(data, dt=ts.dt, window='hann')
dominant_freq_idx = np.argmax(power[1:]) + 1  # Skip DC component
print(f"    FFT computed: {len(freqs)} frequencies")
print(f"    Dominant frequency: {freqs[dominant_freq_idx]:.4f} Hz")

# 3. Nonlinear parameter estimation
print("\n[3] Nonlinear Parameter Estimation")
print("    " + "-" * 66)

# Estimate tau using AMI
ami = compute_ami(data, max_lag=100)
tau = find_first_minimum(ami)
print(f"    AMI first minimum at tau={tau}")
print(f"    AMI values: {ami[:5]}")

# Estimate m using FNN
fnn = compute_fnn(data, tau=tau, max_dim=10)
m = find_embedding_dimension(fnn, threshold=1.0)
print(f"    FNN percentage by dimension:")
for i, f in enumerate(fnn[:6], start=1):
    print(f"      m={i}: {f:.2f}%")
print(f"    Optimal embedding dimension: m={m}")

# 4. Phase space reconstruction
print("\n[4] Phase Space Reconstruction")
print("    " + "-" * 66)
embedded = embed_timeseries(data, m=m, tau=tau)
print(f"    Embedded space: {embedded.shape}")
print(f"    First 3 points:")
for i in range(min(3, len(embedded))):
    print(f"      {embedded[i]}")

# 5. Chaos analysis
print("\n[5] Chaos Analysis")
print("    " + "-" * 66)

# Lyapunov exponent
time_steps, divergence = lyapunov_rosenstein(data, m=m, tau=tau, max_lag=50)
lyap = estimate_lyapunov_from_curve(time_steps, divergence, fit_start=2, fit_end=30)
print(f"    Lyapunov exponent: {lyap:.4f}")
print(f"    Expected value: ~0.9")
print(f"    Divergence curve (first 10 points):")
for i in range(min(10, len(divergence))):
    if not np.isnan(divergence[i]):
        print(f"      t={time_steps[i]:2d}: {divergence[i]:.4f}")

# Correlation dimension (simplified for speed)
print("\n    Computing correlation dimension...")
radii, c_r = correlation_dimension(data, m=min(m, 3), tau=tau, n_radii=20)
dim = estimate_dimension_from_correlation(radii, c_r, fit_start=5, fit_end=15)
print(f"    Correlation dimension: {dim:.4f}")
print(f"    Expected: ~2.06 (Lorenz attractor)")

# 6. Summary
print("\n" + "=" * 70)
print("ANALYSIS SUMMARY")
print("=" * 70)
print(f"System:              Lorenz attractor")
print(f"Data points:         {len(data)}")
print(f"Sampling interval:   {ts.dt}")
print(f"Time delay (τ):      {tau}")
print(f"Embedding dim (m):   {m}")
print(f"Lyapunov exponent:   {lyap:.4f}")
print(f"Correlation dim:     {dim:.4f}")
print("=" * 70)
print("\nAnalysis complete!")
