"""
Core module: time series data structure and generation
"""
from .timeseries import TimeSeries
from .generators import (
    logistic_map,
    henon_map,
    generate_lorenz,
    generate_rossler,
    generate_chua,
    generate_chen,
    generate_duffing,
    generate_double_pendulum,
    tent_map,
    sine_map,
    ikeda_map,
    generate_sine,
    generate_white_noise
)
from .integrators import integrate_ode, rk4_step
from .loaders import load_csv, load_txt

__all__ = [
    'TimeSeries',
    'logistic_map',
    'henon_map',
    'generate_lorenz',
    'generate_rossler',
    'generate_chua',
    'generate_chen',
    'generate_duffing',
    'generate_double_pendulum',
    'tent_map',
    'sine_map',
    'ikeda_map',
    'generate_sine',
    'generate_white_noise',
    'integrate_ode',
    'rk4_step',
    'load_csv',
    'load_txt'
]
