"""
Fast Fourier Transform and Power Spectrum
"""
import numpy as np


def compute_fft(data: np.ndarray, dt: float = 1.0, window: str = 'hann') -> tuple:
    """
    Compute FFT and power spectrum with windowing
    
    Args:
        data: 1D time series
        dt: sampling interval
        window: window function ('hann', 'hamming', 'blackman', 'none')
    
    Returns:
        (frequencies, power_spectrum)
    """
    n = len(data)
    
    # Apply window
    if window == 'hann':
        w = np.hanning(n)
    elif window == 'hamming':
        w = np.hamming(n)
    elif window == 'blackman':
        w = np.blackman(n)
    elif window == 'none':
        w = np.ones(n)
    else:
        raise ValueError(f"Unknown window: {window}")
    
    windowed_data = data * w
    
    # Compute FFT
    fft_result = np.fft.fft(windowed_data)
    
    # Power spectrum (one-sided)
    power = np.abs(fft_result[:n//2])**2
    
    # Frequencies
    frequencies = np.fft.fftfreq(n, dt)[:n//2]
    
    return frequencies, power
