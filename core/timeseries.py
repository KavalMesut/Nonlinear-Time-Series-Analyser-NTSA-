"""
Time series data structure and operations
"""
import numpy as np
from typing import Dict, Any, Optional


class TimeSeries:
    """Core time series data structure"""
    
    def __init__(
        self,
        data: np.ndarray,
        dt: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        t0: float = 0.0
    ):
        """
        Initialize TimeSeries
        
        Args:
            data: 1D numpy array of time series values
            dt: time step between samples
            metadata: optional metadata dictionary
            t0: start time for the first sample
        """
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        
        if data.ndim != 1:
            raise ValueError("Data must be 1-dimensional")
        
        self.data = data
        self.dt = float(dt)
        self.t0 = float(t0)
        self.metadata = metadata if metadata is not None else {}
        self._custom_time = None  # For custom time arrays
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __repr__(self) -> str:
        return f"TimeSeries(length={len(self)}, dt={self.dt}, t0={self.t0})"
    
    @property
    def time(self) -> np.ndarray:
        """Generate time array"""
        if self._custom_time is not None:
            return self._custom_time
        return self.t0 + np.arange(len(self)) * self.dt
    
    @time.setter
    def time(self, value: np.ndarray):
        """Set custom time array"""
        if not isinstance(value, np.ndarray):
            value = np.array(value)
        if len(value) != len(self.data):
            raise ValueError(f"Time array length ({len(value)}) must match data length ({len(self.data)})")
        self._custom_time = value
    
    def subset(self, start: int, end: int) -> 'TimeSeries':
        """Create a subset of the time series"""
        start = max(0, start)
        end = min(len(self), end)
        return TimeSeries(
            data=self.data[start:end],
            dt=self.dt,
            metadata={**self.metadata, 'subset': (start, end)},
            t0=self.t0 + start * self.dt
        )
