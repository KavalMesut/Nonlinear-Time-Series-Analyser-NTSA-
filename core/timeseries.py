"""
Time series data structure and operations
"""
import numpy as np
from typing import Dict, Any, Optional


class TimeSeries:
    """Core time series data structure"""
    
    def __init__(self, data: np.ndarray, dt: float = 1.0, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize TimeSeries
        
        Args:
            data: 1D numpy array of time series values
            dt: time step between samples
            metadata: optional metadata dictionary
        """
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        
        if data.ndim != 1:
            raise ValueError("Data must be 1-dimensional")
        
        self.data = data
        self.dt = float(dt)
        self.metadata = metadata if metadata is not None else {}
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __repr__(self) -> str:
        return f"TimeSeries(length={len(self)}, dt={self.dt})"
    
    @property
    def time(self) -> np.ndarray:
        """Generate time array"""
        return np.arange(len(self)) * self.dt
    
    def subset(self, start: int, end: int) -> 'TimeSeries':
        """Create a subset of the time series"""
        return TimeSeries(
            data=self.data[start:end],
            dt=self.dt,
            metadata={**self.metadata, 'subset': (start, end)}
        )
