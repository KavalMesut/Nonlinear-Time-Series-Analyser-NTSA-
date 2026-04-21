"""
Session management — analiz durumunu kaydet/yükle
"""
import json
import pickle
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from core.timeseries import TimeSeries
from core.export import _make_json_serializable
import numpy as np


class AnalysisSession:
    """
    Analiz oturumu — tüm veri ve sonuçları depolar.
    """
    
    def __init__(self):
        self.created_at = datetime.now().isoformat()
        self.modified_at = self.created_at
        
        # Data
        self.timeseries: Optional[TimeSeries] = None
        self.original_timeseries: Optional[TimeSeries] = None  # Preprocessing öncesi
        
        # Analysis parameters
        self.tau: Optional[int] = None
        self.m: Optional[int] = None
        
        # Analysis results
        self.ami_results: Optional[Dict] = None
        self.fnn_results: Optional[Dict] = None
        self.acf_results: Optional[Dict] = None
        self.pacf_results: Optional[Dict] = None
        self.fft_results: Optional[Dict] = None
        self.lyapunov_results: Optional[Dict] = None
        self.correlation_dim_results: Optional[Dict] = None
        
        # Preprocessing history
        self.preprocessing_steps: list = []
        
        # Metadata
        self.metadata: Dict[str, Any] = {}
    
    def set_timeseries(self, ts: TimeSeries, is_original: bool = True):
        """Zaman serisini kaydet."""
        self.timeseries = ts
        if is_original:
            self.original_timeseries = ts
        self.modified_at = datetime.now().isoformat()
    
    def set_parameters(self, tau: int, m: int):
        """Analiz parametrelerini kaydet."""
        self.tau = tau
        self.m = m
        self.modified_at = datetime.now().isoformat()
    
    def add_preprocessing_step(self, operation: str, params: Dict):
        """Preprocessing adımını kaydet."""
        self.preprocessing_steps.append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'parameters': params
        })
        self.modified_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Session'ı dictionary'e çevir (JSON export için)."""
        data = {
            'version': '1.0',
            'created_at': self.created_at,
            'modified_at': self.modified_at,
            'metadata': self.metadata,
            'preprocessing_steps': self.preprocessing_steps,
            'parameters': {
                'tau': self.tau,
                'm': self.m
            }
        }
        
        # Timeseries
        if self.timeseries:
            data['timeseries'] = {
                'data': self.timeseries.data.tolist(),
                'time': self.timeseries.time.tolist(),
                'dt': self.timeseries.dt,
                't0': self.timeseries.t0,
                'metadata': getattr(self.timeseries, 'metadata', {})
            }
        
        if self.original_timeseries and self.original_timeseries is not self.timeseries:
            data['original_timeseries'] = {
                'data': self.original_timeseries.data.tolist(),
                'time': self.original_timeseries.time.tolist(),
                'dt': self.original_timeseries.dt,
                't0': self.original_timeseries.t0,
                'metadata': getattr(self.original_timeseries, 'metadata', {})
            }
        
        # Analysis results
        results = {}
        if self.ami_results:
            results['ami'] = _make_json_serializable(self.ami_results)
        if self.fnn_results:
            results['fnn'] = _make_json_serializable(self.fnn_results)
        if self.acf_results:
            results['acf'] = _make_json_serializable(self.acf_results)
        if self.pacf_results:
            results['pacf'] = _make_json_serializable(self.pacf_results)
        if self.fft_results:
            results['fft'] = _make_json_serializable(self.fft_results)
        if self.lyapunov_results:
            results['lyapunov'] = _make_json_serializable(self.lyapunov_results)
        if self.correlation_dim_results:
            results['correlation_dim'] = _make_json_serializable(self.correlation_dim_results)
        
        if results:
            data['analysis_results'] = results
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisSession':
        """Dictionary'den session oluştur."""
        session = cls()
        
        session.created_at = data.get('created_at', session.created_at)
        session.modified_at = data.get('modified_at', session.modified_at)
        session.metadata = data.get('metadata', {})
        session.preprocessing_steps = data.get('preprocessing_steps', [])
        
        # Parameters
        params = data.get('parameters', {})
        session.tau = params.get('tau')
        session.m = params.get('m')
        
        # Timeseries
        if 'timeseries' in data:
            ts_data = data['timeseries']
            session.timeseries = TimeSeries(
                data=np.array(ts_data['data']),
                dt=ts_data['dt'],
                t0=ts_data.get('t0', 0.0)
            )
            session.timeseries.metadata = ts_data.get('metadata', {})
        
        if 'original_timeseries' in data:
            ts_data = data['original_timeseries']
            session.original_timeseries = TimeSeries(
                data=np.array(ts_data['data']),
                dt=ts_data['dt'],
                t0=ts_data.get('t0', 0.0)
            )
            session.original_timeseries.metadata = ts_data.get('metadata', {})
        elif session.timeseries:
            session.original_timeseries = session.timeseries
        
        # Analysis results
        results = data.get('analysis_results', {})
        session.ami_results = results.get('ami')
        session.fnn_results = results.get('fnn')
        session.acf_results = results.get('acf')
        session.pacf_results = results.get('pacf')
        session.fft_results = results.get('fft')
        session.lyapunov_results = results.get('lyapunov')
        session.correlation_dim_results = results.get('correlation_dim')
        
        return session
    
    def save_json(self, filepath: str) -> bool:
        """Session'ı JSON dosyasına kaydet."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Session save error (JSON): {e}")
            return False
    
    @classmethod
    def load_json(cls, filepath: str) -> Optional['AnalysisSession']:
        """JSON dosyasından session yükle."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception as e:
            print(f"Session load error (JSON): {e}")
            return None
    
    def save_pickle(self, filepath: str) -> bool:
        """Session'ı pickle dosyasına kaydet (daha hızlı, binary)."""
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(self, f, protocol=pickle.HIGHEST_PROTOCOL)
            return True
        except Exception as e:
            print(f"Session save error (pickle): {e}")
            return False
    
    @classmethod
    def load_pickle(cls, filepath: str) -> Optional['AnalysisSession']:
        """Pickle dosyasından session yükle."""
        try:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Session load error (pickle): {e}")
            return None
