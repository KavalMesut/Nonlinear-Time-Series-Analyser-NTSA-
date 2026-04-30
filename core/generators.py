"""
Time series generators: chaotic systems and maps
"""
import numpy as np
from typing import Tuple
from .timeseries import TimeSeries


def logistic_map(r: float = 4.0, x0: float = 0.1, n: int = 1000) -> TimeSeries:
    """
    Generate logistic map time series
    
    x[n+1] = r * x[n] * (1 - x[n])
    
    Args:
        r: control parameter (typically 0-4)
        x0: initial condition
        n: number of points
    
    Returns:
        TimeSeries object
    """
    data = np.zeros(n)
    data[0] = x0
    
    for i in range(1, n):
        data[i] = r * data[i-1] * (1 - data[i-1])
    
    metadata = {
        'system': 'logistic_map',
        'r': r,
        'x0': x0
    }
    
    return TimeSeries(data=data, dt=1.0, metadata=metadata)


def henon_map(a: float = 1.4, b: float = 0.3, x0: float = 0.1, 
              y0: float = 0.1, n: int = 1000) -> TimeSeries:
    """
    Generate Hénon map time series
    
    x[n+1] = 1 - a * x[n]^2 + y[n]
    y[n+1] = b * x[n]
    
    Standard parameters: a=1.4, b=0.3 → chaotic (Lyapunov ≈ 0.42)
    
    Args:
        a: control parameter (typically 1.4)
        b: control parameter (typically 0.3)
        x0: initial x condition
        y0: initial y condition
        n: number of points
    
    Returns:
        TimeSeries object (returns x coordinate only)
    """
    x = np.zeros(n)
    y = np.zeros(n)
    
    x[0] = x0
    y[0] = y0
    
    for i in range(1, n):
        x[i] = 1 - a * x[i-1]**2 + y[i-1]
        y[i] = b * x[i-1]
    
    metadata = {
        'system': 'henon_map',
        'a': a,
        'b': b,
        'x0': x0,
        'y0': y0
    }
    
    return TimeSeries(data=x, dt=1.0, metadata=metadata)


def generate_lorenz(y0: np.ndarray = None, t_span: Tuple[float, float] = (0, 100), 
                    dt: float = 0.01, sigma: float = 10.0, rho: float = 28.0, 
                    beta: float = 8.0/3.0) -> TimeSeries:
    """
    Generate Lorenz attractor time series
    
    Args:
        y0: initial conditions [x0, y0, z0]
        t_span: time span
        dt: time step
        sigma, rho, beta: Lorenz parameters
    
    Returns:
        TimeSeries of x-coordinate
    """
    from .integrators import integrate_ode, lorenz_system
    
    if y0 is None:
        y0 = np.array([1.0, 1.0, 1.0])
    
    f = lorenz_system(sigma=sigma, rho=rho, beta=beta)
    return integrate_ode(f, y0, t_span, dt, system_name="lorenz",
                         params={'sigma': sigma, 'rho': rho, 'beta': round(beta, 4)})


def generate_rossler(y0: np.ndarray = None, t_span: Tuple[float, float] = (0, 100), 
                     dt: float = 0.01, a: float = 0.2, b: float = 0.2, 
                     c: float = 5.7) -> TimeSeries:
    """
    Generate Rössler attractor time series
    """
    from .integrators import integrate_ode, rossler_system
    
    if y0 is None:
        y0 = np.array([1.0, 1.0, 1.0])
    
    f = rossler_system(a=a, b=b, c=c)
    return integrate_ode(f, y0, t_span, dt, system_name="rossler",
                         params={'a': a, 'b': b, 'c': c})


def generate_chua(y0: np.ndarray = None, t_span: Tuple[float, float] = (0, 100),
                  dt: float = 0.01, alpha: float = 15.6, beta: float = 28.0) -> TimeSeries:
    """Generate Chua's circuit time series"""
    from .integrators import integrate_ode, chua_system
    if y0 is None:
        y0 = np.array([0.7, 0.0, 0.0])
    f = chua_system(alpha=alpha, beta=beta)
    return integrate_ode(f, y0, t_span, dt, system_name="chua",
                         params={'alpha': alpha, 'beta': beta})


def generate_chen(y0: np.ndarray = None, t_span: Tuple[float, float] = (0, 100),
                  dt: float = 0.01, a: float = 35.0, b: float = 3.0, c: float = 28.0) -> TimeSeries:
    """Generate Chen's system time series"""
    from .integrators import integrate_ode, chen_system
    if y0 is None:
        y0 = np.array([-0.1, 0.5, -0.6])
    f = chen_system(a=a, b=b, c=c)
    return integrate_ode(f, y0, t_span, dt, system_name="chen",
                         params={'a': a, 'b': b, 'c': c})


def generate_duffing(y0: np.ndarray = None, t_span: Tuple[float, float] = (0, 500),
                     dt: float = 0.01, delta: float = 0.3, gamma: float = 0.5, 
                     omega: float = 1.2) -> TimeSeries:
    """Generate forced Duffing oscillator time series (chaotic regime: gamma=0.5)"""
    from .integrators import integrate_ode, duffing_system
    if y0 is None:
        y0 = np.array([1.0, 0.0])
    f = duffing_system(delta=delta, gamma=gamma, omega=omega)
    return integrate_ode(f, y0, t_span, dt, system_name="duffing",
                         params={'delta': delta, 'gamma': gamma, 'omega': omega})


def generate_double_pendulum(y0: np.ndarray = None, t_span: Tuple[float, float] = (0, 200),
                             dt: float = 0.01, m1: float = 1.0, m2: float = 1.0,
                             l1: float = 1.0, l2: float = 1.0, g: float = 9.81) -> TimeSeries:
    """Cift sarkac zaman serisi (kaotik rejim: theta1=theta2=pi/2, LE~0.5)"""
    from .integrators import integrate_ode, double_pendulum_system
    if y0 is None:
        y0 = np.array([np.pi / 2, np.pi / 2, 0.0, 0.0])
    f = double_pendulum_system(m1=m1, m2=m2, l1=l1, l2=l2, g=g)
    return integrate_ode(f, y0, t_span, dt, system_name="double_pendulum",
                         params={'m1': m1, 'm2': m2, 'l1': l1, 'l2': l2, 'g': g})


def tent_map(mu: float = 2.0, x0: float = 0.501, n: int = 1000) -> TimeSeries:
    """Generate Tent map time series.
    
    Uses Bernoulli shift (binary) representation to avoid floating-point collapse.
    For mu=2, the tent map is conjugate to the Bernoulli shift, which allows
    exact computation without precision loss.
    """
    if mu == 2.0:
        # Use random initial condition with high precision and iterate
        # with perturbation to prevent floating-point collapse
        rng = np.random.RandomState(42)
        data = np.zeros(n)
        data[0] = x0
        for i in range(1, n):
            x = mu * min(data[i-1], 1.0 - data[i-1])
            # Add tiny perturbation to prevent collapse to zero
            if x == 0.0 or x == 1.0:
                x = rng.uniform(0.01, 0.99)
            data[i] = x
    else:
        data = np.zeros(n)
        data[0] = x0
        for i in range(1, n):
            data[i] = mu * min(data[i-1], 1 - data[i-1])
    return TimeSeries(data=data, dt=1.0, metadata={'system': 'tent_map', 'mu': mu})


def sine_map(lambda_param: float = 1.0, x0: float = 0.1, n: int = 1000) -> TimeSeries:
    """Generate Sine map time series"""
    data = np.zeros(n)
    data[0] = x0
    for i in range(1, n):
        data[i] = lambda_param * np.sin(np.pi * data[i-1])
    return TimeSeries(data=data, dt=1.0, metadata={'system': 'sine_map', 'lambda': lambda_param})


def ikeda_map(u: float = 0.9, n: int = 1000) -> TimeSeries:
    """Generate Ikeda map time series"""
    x = np.zeros(n)
    y = np.zeros(n)
    x[0], y[0] = 0.1, 0.1
    for i in range(1, n):
        tn = 0.4 - 6.0 / (1.0 + x[i-1]**2 + y[i-1]**2)
        x[i] = 1.0 + u * (x[i-1] * np.cos(tn) - y[i-1] * np.sin(tn))
        y[i] = u * (x[i-1] * np.sin(tn) + y[i-1] * np.cos(tn))
    return TimeSeries(data=x, dt=1.0, metadata={'system': 'ikeda_map', 'u': u})



def generate_sine(amplitude: float = 1.0, frequency: float = 1.0, 
                  n: int = 1000, dt: float = 0.01) -> TimeSeries:
    """Generate sine wave for testing"""
    t = np.arange(n) * dt
    data = amplitude * np.sin(2 * np.pi * frequency * t)
    
    metadata = {
        'system': 'sine',
        'amplitude': amplitude,
        'frequency': frequency
    }
    
    return