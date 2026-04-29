"""
Data loaders for external files
"""
import numpy as np
from pathlib import Path
from .timeseries import TimeSeries


def load_csv(filepath: str, column: int = 0, dt: float = 1.0, 
             skip_header: int = 0, delimiter: str = ',') -> TimeSeries:
    """
    Load time series from CSV file
    
    Args:
        filepath: path to CSV file
        column: column index to load (0-based)
        dt: time step
        skip_header: number of header rows to skip
        delimiter: column delimiter
    
    Returns:
        TimeSeries object
    """
    data = np.loadtxt(filepath, delimiter=delimiter, skiprows=skip_header, usecols=column)
    
    metadata = {
        'source': str(Path(filepath).name),
        'column': column
    }
    
    return TimeSeries(data=data, dt=dt, metadata=metadata)


def load_txt(filepath: str, dt: float = 1.0, skip_header: int = 0) -> TimeSeries:
    """
    Load time series from TXT file (single column)
    
    Args:
        filepath: path to TXT file
        dt: time step
        skip_header: number of header rows to skip
    
    Returns:
        TimeSeries object
    """
    data = np.loadtxt(filepath, skiprows=skip_header)
    
    metadata = {
        'source': str(Path(filepath).name)
    }
    
    return TimeSeries(data=data, dt=dt, metadata=metadata)
