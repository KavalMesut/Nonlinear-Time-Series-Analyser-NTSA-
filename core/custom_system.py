"""
Custom ODE and discrete map system generator
User can define their own systems via string expressions
"""
import numpy as np
from typing import Callable, Dict, Any, Tuple
from .timeseries import TimeSeries


def _get_sympy():
    """Lazy sympy import -- hata mesaji acik olsun."""
    try:
        import sympy as sp
        return sp
    except ImportError:
        raise ImportError(
            "sympy kurulu degil. Terminalde sunu calistirin:\n"
            "  pip install sympy\n"
            "Sonra uygulamayi yeniden baslatın."
        )


def parse_ode_system(expressions, var_names=None):
    """
    Parse symbolic ODE expressions and return a callable RHS function.

    Args:
        expressions: Dict like {'dx/dt': 'sigma*(y-x)', 'dy/dt': '...'}
        var_names: Optional list of variable names (default: auto from keys)

    Returns:
        Tuple of (rhs_callable, var_names_list)
    """
    import re
    sp = _get_sympy()
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations

    _math_funcs = {
        'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
        'exp': sp.exp, 'log': sp.log, 'sqrt': sp.sqrt,
        'pi': sp.pi, 'e': sp.E, 'abs': sp.Abs,
        'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh,
        'asin': sp.asin, 'acos': sp.acos, 'atan': sp.atan,
    }

    _all_identifiers = set()
    for expr_str in expressions.values():
        _all_identifiers.update(re.findall(r'\b[A-Za-z_]\w*\b', expr_str))

    if var_names is None:
        _key_vars = []
        for key in expressions.keys():
            m = re.match(r'd([A-Za-z_]\w*)/dt', key.strip())
            if m:
                _key_vars.append(m.group(1))
        if _key_vars:
            var_names = _key_vars
        else:
            _safe_locals = {n: (_math_funcs[n] if n in _math_funcs else sp.Symbol(n))
                            for n in _all_identifiers}
            all_syms = set()
            for expr_str in expressions.values():
                try:
                    expr = sp.sympify(expr_str, locals=_safe_locals)
                    all_syms.update(str(s) for s in expr.free_symbols)
                except Exception:
                    all_syms.update(re.findall(r'\b[A-Za-z_]\w*\b', expr_str))
            non_vars = set(_math_funcs.keys()) | {'t', 'dt'}
            var_names = sorted(list(all_syms - non_vars))

    # Build global dict: all identifiers as symbols, then math funcs override
    _pg = {
        'Symbol': sp.Symbol, 'Integer': sp.Integer, 'Float': sp.Float,
        'Rational': sp.Rational, 'I': sp.I, 'oo': sp.oo, 'nan': sp.nan,
        'true': sp.true, 'false': sp.false,
    }
    for _n in _all_identifiers:
        if _n not in _pg:
            _pg[_n] = sp.Symbol(_n)
    _pg['t'] = sp.Symbol('t')
    _pg.update(_math_funcs)

    parsed_exprs = {}
    for key, expr_str in expressions.items():
        _low = expr_str.lower()
        if any(w in _low for w in ['import', 'exec', 'eval', 'open', 'system', '__']):
            raise ValueError("Unsafe operation detected in: " + key)
        try:
            parsed_exprs[key] = parse_expr(
                expr_str, local_dict={}, global_dict=_pg,
                transformations=standard_transformations
            )
        except Exception as ex:
            raise ValueError("Failed to parse " + key + ": " + expr_str + "\nError: " + str(ex))

    # Lambdify: subs'ten ~100x hızlı, NaN/overflow riski yok
    # Parametre isimleri = identifiers - var_names - math funcs - 't'
    _param_names = [n for n in sorted(_all_identifiers)
                    if n not in var_names and n not in _math_funcs and n != 't']
    _lam_arg_names = list(var_names) + ['t'] + _param_names
    _lam_syms = [sp.Symbol(n) for n in _lam_arg_names]

    _lambdified = {}
    for key, expr in parsed_exprs.items():
        _lambdified[key] = sp.lambdify(_lam_syms, expr, modules='numpy')

    _n_vars = len(var_names)
    _expr_keys = list(expressions.keys())

    def rhs(t, y, **params):
        args = [float(y[i]) for i in range(_n_vars)]
        args.append(float(t))
        for pname in _param_names:
            args.append(float(params.get(pname, 0.0)))
        dy = np.zeros(_n_vars)
        for i, key in enumerate(_expr_keys):
            try:
                v = _lambdified[key](*args)
                dy[i] = float(v)
            except Exception:
                return np.full_like(y, np.nan)
        return dy

    # Expose expected param names so callers can warn on missing params
    rhs.param_names = _param_names

    return rhs, var_names


def parse_map_system(expression, var_names=None):
    """
    Parse symbolic discrete map expression.

    Args:
        expression: e.g. "4*x*(1-x)" or "1-a*x**2+y; b*x"
        var_names: Optional list of variable names

    Returns:
        Tuple of (map_callable, var_names_list)
    """
    import re
    sp = _get_sympy()
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations

    _math_funcs = {
        'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan,
        'exp': sp.exp, 'log': sp.log, 'sqrt': sp.sqrt,
        'pi': sp.pi, 'e': sp.E, 'abs': sp.Abs,
        'sinh': sp.sinh, 'cosh': sp.cosh, 'tanh': sp.tanh,
    }

    if ';' in expression:
        parts = [p.strip() for p in expression.split(';')]
    else:
        parts = [expression.strip()]
    var_count = len(parts)

    _all_identifiers = set()
    for part in parts:
        _all_identifiers.update(re.findall(r'\b[A-Za-z_]\w*\b', part))

    if var_names is None:
        _safe_locals = {n: (_math_funcs[n] if n in _math_funcs else sp.Symbol(n))
                        for n in _all_identifiers}
        all_syms = set()
        for part in parts:
            try:
                expr = sp.sympify(part, locals=_safe_locals)
                all_syms.update(str(s) for s in expr.free_symbols)
            except Exception:
                all_syms.update(re.findall(r'\b[A-Za-z_]\w*\b', part))
        non_vars = set(_math_funcs.keys()) | {'n', 'dt'}
        var_names = sorted(list(all_syms - non_vars))

    if len(var_names) != var_count:
        raise ValueError(
            "Expression has " + str(var_count) + " parts but " +
            str(len(var_names)) + " variable names provided"
        )

    _pg = {
        'Symbol': sp.Symbol, 'Integer': sp.Integer, 'Float': sp.Float,
        'Rational': sp.Rational, 'I': sp.I, 'oo': sp.oo, 'nan': sp.nan,
    }
    for _n in _all_identifiers:
        if _n not in _pg:
            _pg[_n] = sp.Symbol(_n)
    _pg.update(_math_funcs)

    parsed_parts = []
    for part in parts:
        if any(w in part.lower() for w in ['import', 'exec', 'eval', 'open', '__']):
            raise ValueError("Unsafe operation detected")
        try:
            parsed_parts.append(
                parse_expr(part, local_dict={}, global_dict=_pg,
                           transformations=standard_transformations)
            )
        except Exception as ex:
            raise ValueError("Failed to parse map: " + part + "\nError: " + str(ex))

    # Lambdify for map — same benefit as ODE: fast, no subs string-key issues
    _param_names_map = [n for n in sorted(_all_identifiers)
                        if n not in var_names and n not in _math_funcs]
    _lam_syms_map = [sp.Symbol(n) for n in list(var_names) + _param_names_map]

    _lambdified_map = [sp.lambdify(_lam_syms_map, expr, modules='numpy')
                       for expr in parsed_parts]
    _n_vars_map = len(var_names)

    def map_fn(x, **params):
        args = [float(x[i]) for i in range(_n_vars_map)]
        for pname in _param_names_map:
            args.append(float(params.get(pname, 0.0)))
        x_next = np.zeros_like(x, dtype=float)
        for i, fn in enumerate(_lambdified_map):
            try:
                x_next[i] = float(fn(*args))
            except Exception:
                return np.full_like(x, np.nan)
        return x_next

    # Expose expected param names so callers can warn on missing params
    map_fn.param_names = _param_names_map

    return map_fn, var_names



def integrate_custom_ode(rhs, y0, t_span=(0, 100), dt=0.01,
                         params=None, system_name='custom_ode',
                         output_var_idx=0, var_names=None):
    """
    Integrate custom ODE system using RK4.

    Args:
        rhs: Callable f(t, y, **params) -> dy/dt
        y0: Initial conditions
        t_span: (t_start, t_end)
        dt: Time step
        params: Parameter dict
        system_name: Metadata label
        output_var_idx: Which state variable to return as TimeSeries primary data
        var_names: List of variable names; all variables stored in metadata

    Returns:
        TimeSeries (selected variable); all variables in metadata['all_vars_data']
    """
    if params is None:
        params = {}

    y0 = np.asarray(y0, dtype=float)
    dim = len(y0)
    output_var_idx = max(0, min(output_var_idx, dim - 1))
    t_start, t_end = t_span
    n_steps = int((t_end - t_start) / dt) + 1

    y = np.zeros((n_steps, dim))
    y[0] = y0
    t = t_start

    nan_step = -1
    for i in range(1, n_steps):
        k1 = rhs(t, y[i-1], **params)
        k2 = rhs(t + dt/2, y[i-1] + dt*k1/2, **params)
        k3 = rhs(t + dt/2, y[i-1] + dt*k2/2, **params)
        k4 = rhs(t + dt, y[i-1] + dt*k3, **params)
        y[i] = y[i-1] + dt * (k1 + 2*k2 + 2*k3 + k4) / 6
        t += dt
        if np.any(np.isnan(y[i])) or np.any(np.abs(y[i]) > 1e15):
            nan_step = i
            # Kalan satırları NaN ile doldur ve erken dur
            y[i:] = np.nan
            break

    _names = var_names if (var_names and len(var_names) == dim) else ['x' + str(i) for i in range(dim)]
    all_vars_data = {name: y[:, i].copy() for i, name in enumerate(_names)}

    if nan_step > 0:
        raise ValueError(
            f"Sayısal kararsızlık: adım {nan_step}'de NaN/overflow oluştu.\n\n"
            f"Çözüm: dt değerini küçültün (şu an dt={dt}).\n"
            f"Lorenz ve kaotik sistemler için dt ≤ 0.05 önerilir (ideal: 0.01)."
        )

    return TimeSeries(
        data=y[:, output_var_idx], dt=dt,
        metadata={
            'system': system_name,
            'custom': True,
            'parameters': params,
            'output_var_idx': output_var_idx,
            'output_var_name': _names[output_var_idx],
            'var_names': _names,
            'all_vars_data': all_vars_data,
        }
    )


def iterate_custom_map(map_fn, x0, n_steps=5000, params=None,
                       system_name='custom_map'):
    """
    Iterate custom discrete map system.

    Args:
        map_fn: Callable f(x, **params) -> x_next
        x0: Initial conditions
        n_steps: Number of iterations
        params: Parameter dict
        system_name: Metadata label

    Returns:
        TimeSeries (first variable)
    """
    if params is None:
        params = {}

    x0 = np.asarray(x0, dtype=float)
    x = np.zeros((n_steps, len(x0)))
    x[0] = x0

    for i in range(1, n_steps):
        x[i] = map_fn(x[i-1], **params)

    return TimeSeries(
        data=x[:, 0], dt=1.0,
        metadata={'system': system_name, 'custom': True,
                  'parameters': params, 'discrete': True}
    )
