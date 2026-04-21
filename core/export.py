"""
Export utilities for time series data and analysis results
"""
import json
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


def export_timeseries_csv(timeseries, filepath: str, include_metadata: bool = True) -> bool:
    """
    Zaman serisi verisini CSV formatında dışa aktar.
    
    Parameters
    ----------
    timeseries : TimeSeries
        Dışa aktarılacak zaman serisi
    filepath : str
        Hedef dosya yolu
    include_metadata : bool
        Metadata satırlarını ekle (dt, t0, etc.)
    
    Returns
    -------
    bool
        Başarılı ise True
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            # Metadata (yorum satırı olarak)
            if include_metadata:
                f.write(f"# Time Series Data Export\n")
                f.write(f"# Exported: {datetime.now().isoformat()}\n")
                f.write(f"# dt: {timeseries.dt}\n")
                f.write(f"# t0: {timeseries.t0}\n")
                f.write(f"# N: {len(timeseries.data)}\n")
                if hasattr(timeseries, 'metadata') and timeseries.metadata:
                    for key, value in timeseries.metadata.items():
                        f.write(f"# {key}: {value}\n")
                f.write("#\n")
            
            # Header
            f.write("time,value\n")
            
            # Data
            for t, val in zip(timeseries.time, timeseries.data):
                f.write(f"{t:.8f},{val:.8f}\n")
        
        return True
    except Exception as e:
        print(f"CSV export error: {e}")
        return False


def export_analysis_results_json(results: Dict[str, Any], filepath: str) -> bool:
    """
    Analiz sonuçlarını JSON formatında dışa aktar.
    
    Parameters
    ----------
    results : dict
        Analiz sonuçları dictionary'si
    filepath : str
        Hedef dosya yolu
    
    Returns
    -------
    bool
        Başarılı ise True
    """
    try:
        # NumPy array'leri list'e çevir
        serializable = _make_json_serializable(results)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2, ensure_ascii=False)
        
        return True
    except Exception as e:
        print(f"JSON export error: {e}")
        return False


def export_plot_png(plot_widget, filepath: str, width: int = 1920, height: int = 1080) -> bool:
    """
    PyQtGraph plot widget'ını PNG olarak dışa aktar.
    
    Parameters
    ----------
    plot_widget : PlotWidget
        PyQtGraph PlotWidget
    filepath : str
        Hedef dosya yolu
    width : int
        Görüntü genişliği (piksel)
    height : int
        Görüntü yüksekliği (piksel)
    
    Returns
    -------
    bool
        Başarılı ise True
    """
    try:
        from PySide6.QtCore import QSize
        from PySide6.QtGui import QImage, QPainter
        
        # Render widget to image
        size = QSize(width, height)
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(0)  # Transparent background
        
        painter = QPainter(image)
        plot_widget.render(painter)
        painter.end()
        
        # Save
        success = image.save(filepath, "PNG")
        return success
    except Exception as e:
        print(f"PNG export error: {e}")
        return False


def _make_json_serializable(obj):
    """
    Recursive function to convert NumPy types to Python native types.
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: _make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_make_json_serializable(item) for item in obj]
    else:
        return obj


def create_analysis_summary(timeseries, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tam analiz özeti oluştur (session kaydetmek için).
    
    Parameters
    ----------
    timeseries : TimeSeries
        Zaman serisi verisi
    analysis_results : dict
        Tüm analiz sonuçları
    
    Returns
    -------
    dict
        Tam analiz özeti
    """
    summary = {
        "export_timestamp": datetime.now().isoformat(),
        "timeseries": {
            "dt": timeseries.dt,
            "t0": timeseries.t0,
            "n_points": len(timeseries.data),
            "data": timeseries.data.tolist(),
            "time": timeseries.time.tolist(),
            "metadata": getattr(timeseries, 'metadata', {})
        },
        "analysis_results": _make_json_serializable(analysis_results)
    }
    
    return summary
