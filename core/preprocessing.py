"""
On isleme (preprocessing) fonksiyonlari.
Zaman serisi verisine uygulanabilecek tum on isleme adimlari.
"""
import numpy as np
from scipy import signal, interpolate, stats
from typing import Optional, Tuple


def normalize(data: np.ndarray, method: str = 'minmax') -> np.ndarray:
    """
    Veriyi normalize eder.
    
    Args:
        data: 1D numpy array
        method: 'minmax' (0-1) veya 'zscore' (ortalama=0, std=1)
    
    Returns:
        Normalize edilmis veri
    """
    if method == 'minmax':
        dmin, dmax = data.min(), data.max()
        if dmax - dmin == 0:
            return np.zeros_like(data)
        return (data - dmin) / (dmax - dmin)
    elif method == 'zscore':
        std = data.std()
        if std == 0:
            return np.zeros_like(data)
        return (data - data.mean()) / std
    else:
        raise ValueError(f"Bilinmeyen normalize yontemi: {method}")


def detrend(data: np.ndarray, method: str = 'linear', poly_order: int = 2) -> np.ndarray:
    """
    Trend cikarma.
    
    Args:
        data: 1D numpy array
        method: 'linear', 'polynomial', 'mean'
        poly_order: polinom derecesi (sadece 'polynomial' icin)
    
    Returns:
        Trendi cikarilmis veri
    """
    if method == 'linear':
        return signal.detrend(data, type='linear')
    elif method == 'polynomial':
        x = np.arange(len(data))
        coeffs = np.polyfit(x, data, poly_order)
        trend = np.polyval(coeffs, x)
        return data - trend
    elif method == 'mean':
        return data - data.mean()
    else:
        raise ValueError(f"Bilinmeyen detrend yontemi: {method}")


def interpolate_missing(data: np.ndarray, method: str = 'linear') -> np.ndarray:
    """
    Eksik degerleri (NaN) doldurur.
    
    Args:
        data: 1D numpy array (NaN iceriyor olabilir)
        method: 'linear', 'spline', 'nearest'
    
    Returns:
        NaN'lar doldurulmus veri
    """
    nan_mask = np.isnan(data)
    if not nan_mask.any():
        return data.copy()
    
    x = np.arange(len(data))
    valid = ~nan_mask
    
    if valid.sum() < 2:
        return data.copy()
    
    if method == 'linear':
        f = interpolate.interp1d(x[valid], data[valid], kind='linear',
                                  fill_value='extrapolate')
    elif method == 'spline':
        f = interpolate.interp1d(x[valid], data[valid], kind='cubic',
                                  fill_value='extrapolate')
    elif method == 'nearest':
        f = interpolate.interp1d(x[valid], data[valid], kind='nearest',
                                  fill_value='extrapolate')
    else:
        raise ValueError(f"Bilinmeyen interpolasyon yontemi: {method}")
    
    result = data.copy()
    result[nan_mask] = f(x[nan_mask])
    return result


def remove_outliers(data: np.ndarray, method: str = 'iqr',
                     threshold: float = 1.5) -> np.ndarray:
    """
    Aykiri degerleri tespit edip interpolasyonla doldurur.
    
    Args:
        data: 1D numpy array
        method: 'iqr' veya 'zscore'
        threshold: IQR icin carpan (varsayilan 1.5), zscore icin esik (varsayilan 3.0)
    
    Returns:
        Aykiri degerleri temizlenmis veri
    """
    result = data.copy()
    
    if method == 'iqr':
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        outlier_mask = (data < lower) | (data > upper)
    elif method == 'zscore':
        z = np.abs(stats.zscore(data))
        outlier_mask = z > threshold
    else:
        raise ValueError(f"Bilinmeyen outlier yontemi: {method}")
    
    if outlier_mask.any():
        result[outlier_mask] = np.nan
        result = interpolate_missing(result, method='linear')
    
    return result


def smooth(data: np.ndarray, method: str = 'moving_avg',
           window_size: int = 5, poly_order: int = 3) -> np.ndarray:
    """
    Yumusatma (smoothing).
    
    Args:
        data: 1D numpy array
        method: 'moving_avg' veya 'savgol'
        window_size: pencere boyutu (tek sayi olmali)
        poly_order: Savitzky-Golay polinom derecesi
    
    Returns:
        Yumusatilmis veri
    """
    # Pencere boyutu tek sayi olmali
    if window_size % 2 == 0:
        window_size += 1
    window_size = max(3, window_size)
    
    if method == 'moving_avg':
        kernel = np.ones(window_size) / window_size
        # Kenarlari korumak icin 'same' modu
        return np.convolve(data, kernel, mode='same')
    elif method == 'savgol':
        poly_order = min(poly_order, window_size - 1)
        return signal.savgol_filter(data, window_size, poly_order)
    else:
        raise ValueError(f"Bilinmeyen smoothing yontemi: {method}")


def difference(data: np.ndarray, order: int = 1) -> np.ndarray:
    """
    Fark alma (differencing) — durağanlık sağlama.
    
    Args:
        data: 1D numpy array
        order: fark derecesi (1 veya 2)
    
    Returns:
        Fark alinmis veri
    """
    result = data.copy()
    for _ in range(order):
        result = np.diff(result)
    return result


def resample_data(data: np.ndarray, factor: float,
                   method: str = 'interpolate') -> np.ndarray:
    """
    Yeniden örnekleme (resampling).
    
    Args:
        data: 1D numpy array
        factor: ornekleme faktoru (>1 upsample, <1 downsample)
        method: 'interpolate' veya 'decimate'
    
    Returns:
        Yeniden orneklenmis veri
    """
    n_original = len(data)
    n_new = max(2, int(n_original * factor))
    
    if method == 'interpolate':
        x_old = np.linspace(0, 1, n_original)
        x_new = np.linspace(0, 1, n_new)
        f = interpolate.interp1d(x_old, data, kind='cubic')
        return f(x_new)
    elif method == 'decimate':
        if factor >= 1:
            # Upsample icin interpolate kullan
            x_old = np.linspace(0, 1, n_original)
            x_new = np.linspace(0, 1, n_new)
            f = interpolate.interp1d(x_old, data, kind='cubic')
            return f(x_new)
        else:
            # Downsample — anti-aliasing filtre uygula
            q = max(2, int(1.0 / factor))
            return signal.decimate(data, q)
    else:
        raise ValueError(f"Bilinmeyen resampling yontemi: {method}")


def filter_data(data: np.ndarray, filter_type: str = 'lowpass',
                cutoff: float = 0.1, order: int = 4,
                fs: float = 1.0, highcut: Optional[float] = None) -> np.ndarray:
    """
    Dijital filtreleme (Butterworth).
    
    Args:
        data: 1D numpy array
        filter_type: 'lowpass', 'highpass', 'bandpass'
        cutoff: kesim frekansi (normalize, 0-0.5*fs arasi)
        order: filtre derecesi
        fs: ornekleme frekansi
        highcut: bandpass icin ust kesim frekansi
    
    Returns:
        Filtrelenmis veri
    """
    nyq = 0.5 * fs
    
    if filter_type == 'lowpass':
        wn = min(cutoff / nyq, 0.99)
        b, a = signal.butter(order, wn, btype='low')
    elif filter_type == 'highpass':
        wn = min(cutoff / nyq, 0.99)
        wn = max(wn, 0.01)
        b, a = signal.butter(order, wn, btype='high')
    elif filter_type == 'bandpass':
        if highcut is None:
            highcut = cutoff * 2
        low = max(cutoff / nyq, 0.01)
        high = min(highcut / nyq, 0.99)
        if low >= high:
            high = min(low + 0.01, 0.99)
        b, a = signal.butter(order, [low, high], btype='band')
    else:
        raise ValueError(f"Bilinmeyen filtre tipi: {filter_type}")
    
    return signal.filtfilt(b, a, data)


def log_transform(data: np.ndarray) -> np.ndarray:
    """
    Logaritmik donusum. Negatif degerleri offset ile kaydirarak isler.
    
    Args:
        data: 1D numpy array
    
    Returns:
        Log donusumu uygulanmis veri
    """
    offset = 0.0
    if data.min() <= 0:
        offset = abs(data.min()) + 1.0
    return np.log(data + offset)


def boxcox_transform(data: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Box-Cox donusumu. Veri pozitif olmali (otomatik kaydirma yapilir).
    
    Args:
        data: 1D numpy array
    
    Returns:
        (donusturulmus veri, lambda parametresi) tuple'i
    """
    offset = 0.0
    if data.min() <= 0:
        offset = abs(data.min()) + 1.0
    transformed, lmbda = stats.boxcox(data + offset)
    return transformed, lmbda


def window_crop(data: np.ndarray, start: int, end: int) -> np.ndarray:
    """
    Veriyi belirli bir zaman aralığına kirpar (windowing).
    
    Args:
        data: 1D numpy array
        start: baslangic indeksi
        end: bitis indeksi
    
    Returns:
        Kirpilmis veri
    """
    start = max(0, start)
    end = min(len(data), end)
    return data[start:end].copy()


def denoise(data: np.ndarray, method: str = 'wavelet',
            level: int = 3, wavelet: str = 'db4',
            threshold_mode: str = 'soft') -> np.ndarray:
    """
    Gurultu ayiklama (denoising).
    
    Args:
        data: 1D numpy array
        method: 'wavelet' veya 'median'
        level: wavelet dekompozisyon seviyesi
        wavelet: wavelet tipi (pywt isimlendirmesi)
        threshold_mode: 'soft' veya 'hard'
    
    Returns:
        Gurultusu azaltilmis veri
    """
    if method == 'wavelet':
        try:
            import pywt
        except ImportError:
            raise ImportError(
                "Wavelet denoising requires PyWavelets. Install 'PyWavelets' to use this method."
            )
        
        # Wavelet dekompozisyon
        coeffs = pywt.wavedec(data, wavelet, level=level)
        
        # Evrensel esik (VisuShrink)
        sigma = np.median(np.abs(coeffs[-1])) / 0.6745
        threshold = sigma * np.sqrt(2 * np.log(len(data)))
        
        # Detay katsayilarina esikleme uygula (approximation haric)
        denoised_coeffs = [coeffs[0]]
        for c in coeffs[1:]:
            if threshold_mode == 'soft':
                denoised_coeffs.append(pywt.threshold(c, threshold, mode='soft'))
            else:
                denoised_coeffs.append(pywt.threshold(c, threshold, mode='hard'))
        
        return pywt.waverec(denoised_coeffs, wavelet)[:len(data)]
    
    elif method == 'median':
        return _median_denoise(data, kernel_size=5)
    else:
        raise ValueError(f"Bilinmeyen denoise yontemi: {method}")


def _median_denoise(data: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    """Median filtre ile gurultu azaltma"""
    return signal.medfilt(data, kernel_size=kernel_size)
