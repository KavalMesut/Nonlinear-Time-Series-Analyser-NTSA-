"""
Numerical integrators for differential equations
"""
import numpy as np
from typing import Callable, Tuple
from .timeseries import TimeSeries


def rk4_step(f: Callable, t: float, y: np.ndarray, dt: float) -> np.ndarray:
    """Single Runge-Kutta 4th order integration step."""
    k1 = f(t, y)
    k2 = f(t + dt/2, y + dt*k1/2)
    k3 = f(t + dt/2, y + dt*k2/2)
    k4 = f(t + dt, y + dt*k3)
    return y + (dt/6) * (k1 + 2*k2 + 2*k3 + k4)


def integrate_ode(f: Callable, y0: np.ndarray, t_span: Tuple[float, float],
                  dt: float, system_name: str = "ode",
                  params: dict = None) -> TimeSeries:
    """
    Integrate ODE system using RK4.

    Args:
        f: derivative function dy/dt = f(t, y)
        y0: initial conditions
        t_span: (t_start, t_end)
        dt: time step
        system_name: name for metadata
        params: dict of system parameters to store in metadata

    Returns:
        TimeSeries object (first variable only)
    """
    t_start, t_end = t_span
    n_steps = int((t_end - t_start) / dt)
    y = np.copy(y0)
    t = t_start
    data = np.zeros(n_steps)
    data[0] = y[0]
    for i in range(1, n_steps):
        y = rk4_step(f, t, y, dt)
        t += dt
        data[i] = y[0]
    metadata = {"system": system_name, "y0": y0.tolist(), "t_span": t_span}
    if params:
        metadata["params"] = params
    return TimeSeries(data=data, dt=dt, metadata=metadata)


def integrate_ode_full(f: Callable, y0: np.ndarray, t_span: Tuple[float, float],
                       dt: float) -> np.ndarray:
    """
    Integrate ODE system using RK4 and return the full state trajectory.

    Unlike integrate_ode (which returns only the first variable as TimeSeries),
    this function returns all state variables at every time step.
    Required for Poincare sections and Lyapunov spectrum computation.

    Args:
        f: derivative function dy/dt = f(t, y)
        y0: initial conditions, shape (dim,)
        t_span: (t_start, t_end)
        dt: time step

    Returns:
        trajectory: np.ndarray of shape (n_steps, dim)
    """
    t_start, t_end = t_span
    n_steps = int((t_end - t_start) / dt)
    dim = len(y0)
    trajectory = np.zeros((n_steps, dim))
    trajectory[0] = y0
    y = np.copy(y0).astype(float)
    t = t_start
    for i in range(1, n_steps):
        y = rk4_step(f, t, y, dt)
        t += dt
        trajectory[i] = y
    return trajectory


# ---------------------------------------------------------------------------
# Built-in ODE systems
# ---------------------------------------------------------------------------

def lorenz_system(sigma: float = 10.0, rho: float = 28.0, beta: float = 8.0/3.0):
    """Lorenz system."""
    def f(t: float, y: np.ndarray) -> np.ndarray:
        x, y_val, z = y
        return np.array([sigma*(y_val-x), x*(rho-z)-y_val, x*y_val-beta*z])
    return f


def rossler_system(a: float = 0.2, b: float = 0.2, c: float = 5.7):
    """Rossler system."""
    def f(t: float, y: np.ndarray) -> np.ndarray:
        x, y_val, z = y
        return np.array([-y_val-z, x+a*y_val, b+z*(x-c)])
    return f


def chua_system(alpha: float = 15.6, beta: float = 28.0,
                m0: float = -1.143, m1: float = -0.714):
    """Chua circuit (piecewise linear)."""
    def f(t: float, y: np.ndarray) -> np.ndarray:
        x, y_val, z = y
        h = m1*x + 0.5*(m0-m1)*(abs(x+1) - abs(x-1))
        return np.array([alpha*(y_val-x-h), x-y_val+z, -beta*y_val])
    return f


def chen_system(a: float = 35.0, b: float = 3.0, c: float = 28.0):
    """Chen system."""
    def f(t: float, y: np.ndarray) -> np.ndarray:
        x, y_val, z = y
        return np.array([a*(y_val-x), (c-a)*x - x*z + c*y_val, x*y_val - b*z])
    return f


def duffing_system(alpha: float = -1.0, beta: float = 1.0,
                   delta: float = 0.3, gamma: float = 0.37, omega: float = 1.2):
    """Forced Duffing Oscillator."""
    def f(t: float, y: np.ndarray) -> np.ndarray:
        y1, y2 = y
        return np.array([
            y2,
            -delta*y2 - alpha*y1 - beta*y1**3 + gamma*np.cos(omega*t)
        ])
    return f


def double_pendulum_system(m1: float = 1.0, m2: float = 1.0,
                            l1: float = 1.0, l2: float = 1.0,
                            g: float = 9.81):
    """Double pendulum system. State: [theta1, theta2, omega1, omega2]."""
    def f(t: float, y: np.ndarray) -> np.ndarray:
        th1, th2, w1, w2 = y
        d = th1 - th2
        den1 = (m1+m2)*l1 - m2*l1*np.cos(d)**2
        den2 = (l2/l1)*den1
        dw1 = (m2*l1*w1**2*np.sin(d)*np.cos(d)
               + m2*g*np.sin(th2)*np.cos(d)
               + m2*l2*w2**2*np.sin(d)
               - (m1+m2)*g*np.sin(th1)) / den1
        dw2 = (-m2*l2*w2**2*np.sin(d)*np.cos(d)
               + (m1+m2)*g*np.sin(th1)*np.cos(d)
               - (m1+m2)*g*np.sin(th2)
               - m2*l1*w1**2*np.sin(d)) / den2
        return np.array([w1, w2, dw1, dw2])
    return f
