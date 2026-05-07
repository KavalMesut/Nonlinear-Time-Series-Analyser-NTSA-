# Nonlinear Time Series Analyser (NTSA)

A desktop application for nonlinear analysis of chaotic time series. Provides data loading, parameter estimation (AMI + FNN), Lyapunov exponent computation (Wolf & Rosenstein), and correlation dimension analysis in a unified pipeline.

## Features

- **10 Chaotic System Generators**: Lorenz, Rössler, Chua, Chen, Duffing, Logistic, Hénon, Tent, Sine, Ikeda
- **12 Preprocessing Functions**: Normalize, detrend, outlier removal, smooth, difference, resample, filter, log/boxcox transform, windowing, denoise
- **Automatic Parameter Estimation**: AMI (time delay tau) and FNN (embedding dimension m) data-driven selection
- **Phase Space Visualization**: 2D/3D phase space, return map, attractor structure
- **Wolf Lyapunov Algorithm**: Faithful implementation of original MATLAB code (KD-Tree based neighbor search). Reference: [Wolf Lyapunov Exponent Estimation (MathWorks)](https://www.mathworks.com/matlabcentral/fileexchange/48084-wolf-lyapunov-exponent-estimation-from-a-time-series?s_tid=FX_rc2_behav)
- **Rosenstein Lyapunov Algorithm**: Auto-fit largest Lyapunov exponent calculation with multiple window sizes
- **Full Lyapunov Spectrum**: Sano-Sawada (1985) / Eckmann-Ruelle (1986) method — local Jacobians estimated from the embedding space via ridge regression + periodic QR re-orthonormalization; yields all m exponents, Kaplan-Yorke dimension, and Kolmogorov-Sinai entropy
- **Poincaré Section**: Axis-aligned hyperplane intersection in the embedded phase space with linear interpolation; **live slider** lets you sweep the section value in real time without re-embedding; configurable axis and crossing direction (+/−/both)
- **Correlation Dimension**: Grassberger-Procaccia algorithm
- **Linear Analysis**: ACF, PACF, FFT (Hann/Hamming/Blackman windows)
- **Export/Session Management**: CSV/PNG/JSON export, save/load analysis state (.tsa/.json)
- **Split Plot Panel**: Top/bottom plot comparison, 20 plot history, auto-range
- **Pipeline Engine**: Dependency-resolved, cached analysis chain
- **PySide6 Interface**: PyQtGraph-based visualization
- **Performance**: scipy KD-Tree, vectorized operations (~43 seconds / 10 system validation)

## UI Features - Step Icons

The left sidebar displays 7 analysis steps with custom-designed icons:

1. **📦 Data Loading** - Box with upload arrows and 3 dots (file transfer)
2. **🔽 Preprocessing** - Filter funnel (data cleaning & transformation)
3. **📊 Linear Analysis** - Bar chart (statistical analysis)
4. **🎚️ Parameter Estimation** - Dual sliders τ and m (embedding parameters)
5. **🌀 Phase Space** - 3D orbital trajectory (phase space embedding)
6. **🌊 Chaos Analysis** - Lorenz attractor pattern (nonlinear dynamics)
7. **📄 Results** - Document icon (final analysis output)

Each step is locked until its dependencies complete. Icons change color based on step state (locked → unlocked → active → completed).

## Validation Results

Validation across 10 chaotic systems (7/10 systems with <10% error):

| System | Analytical LE | Computed LE | Error % | Method |
|--------|------------|---------------|--------|--------|
| Lorenz | 0.9056 | 1.0044 | 10.9% | Rosenstein |
| Rössler | 0.0714 | 0.0579 | 19.0% | Rosenstein |
| Chua | 0.33 | 0.3619 | 9.7% | Rosenstein |
| Chen | 2.027 | 1.9179 | 5.4% | Rosenstein |
| Duffing | 0.16 | 0.0834 | 47.9% | Rosenstein |
| Logistic (r=4) | 0.6931 | 0.6927 | 0.1% | Rosenstein |
| Hénon | 0.4200 | 0.4200 | 0.0% | Rosenstein |
| Tent | 0.6931 | 0.6948 | 0.2% | Rosenstein |
| Sine | 0.6931 | 0.6889 | 0.6% | Rosenstein |
| Ikeda | 0.51 | 0.4858 | 4.7% | Rosenstein |

## Installation

```bash
pip install -r requirements.txt
```

**Requirements**: Python >= 3.8, numpy, scipy >= 1.7.0, PySide6, pyqtgraph

## Quick Start

```python
from core.generators import generate_lorenz
from analysis.ami import compute_ami, find_first_minimum
from analysis.fnn import compute_fnn, find_embedding_dimension
from analysis.lyapunov import lyapunov_rosenstein, lyapunov_wolf

# Generate Lorenz time series
ts = generate_lorenz(dt=0.01, n_steps=10000, transient=2000)
data = ts.data

# Parameter estimation (data-driven)
ami_values = compute_ami(data, max_lag=100)
tau = find_first_minimum(ami_values)

fnn_values = compute_fnn(data, tau=tau, max_dim=10)
m = find_embedding_dimension(fnn_values, threshold=1.0)

# Rosenstein Lyapunov exponent
time_steps, divergence = lyapunov_rosenstein(data, m=m, tau=tau, dt=ts.dt)
# Wolf Lyapunov exponent
le_wolf = lyapunov_wolf(data, m=m, tau=tau, dt=ts.dt)

print(f"tau={tau}, m={m}")
print(f"Rosenstein LE: {divergence:.4f}")
print(f"Wolf LE: {le_wolf:.4f}")
```

### Launching the UI

```bash
python main.py
```

## Project Structure

```
tseriesanalyser/
├── core/                   # Data structures and generators
│   ├── timeseries.py       # TimeSeries class
│   ├── generators.py       # 10 chaotic system generators
│   ├── integrators.py      # RK4 integrator + ODE systems
│   ├── loaders.py          # CSV/TXT file loader
│   ├── preprocessing.py    # 12 preprocessing functions
│   ├── export.py           # CSV/PNG/JSON export
│   └── session.py          # Analysis session save/load
├── analysis/               # Analysis algorithms
│   ├── ami.py              # Average Mutual Information (tau estimation)
│   ├── fnn.py              # False Nearest Neighbors (m estimation)
│   ├── embedding.py        # Time-delay embedding
│   ├── lyapunov.py         # Wolf + Rosenstein Lyapunov exponents
│   ├── fractal.py          # Correlation dimension
│   ├── acf.py              # Autocorrelation
│   ├── pacf.py             # Partial autocorrelation
│   └── fft.py              # Fourier transform
├── pipeline/               # Analysis pipeline engine
│   ├── node.py             # Node class (dependency tracking)
│   └── engine.py           # Pipeline executor
├── ui/                     # PySide6 user interface
├── tests/                  # Validation tests
│   ├── test_validation.py         # 10 system scientific validation
│   ├── test_wolf_matlab_match.py  # Wolf MATLAB compatibility test
│   └── test_preprocessing_workflow.py  # Preprocessing & UI tests
├── examples/               # Example scripts
├── documents/              # Wolf MATLAB reference files
├── main.py                 # Application entry point
├── CLAUDE.md               # Developer guidelines (Turkish)
├── ROADMAP.md              # Project specification (Turkish)
├── README.md               # This file (English)
├── README(tr).md           # Turkish translation (git-ignored)
└── requirements.txt        # Dependencies
```

## UI Features

### Split Plot Panel
The right-side plot panel is now split into two sections:

**Top Panel (Active Plot)**
- Displays current analysis result automatically
- Auto-range: Plot automatically fits the viewport

**Bottom Panel (Comparison)**
- Select a previous graph from dropdown menu
- Compare different analyses side-by-side
- 20 plot history retained

**Use Cases:**
- Compare AMI result with Lyapunov curve
- View preprocessing before/after data side-by-side
- Compare Wolf vs Rosenstein algorithm results
- Examine ACF and PACF simultaneously

### Auto-Range
All plots automatically fit to viewport (PyQtGraph autoRange). Manual zoom/pan still available.

### Phase Space Visualization (Step 5)
Visualizes phase space created by time-delay embedding:

**2D Phase Space:**
- x(t) vs x(t+τ) trajectory plot
- Start (red) and end (green) points
- Shows attractor structure in 2D

**3D Phase Space:**
- x(t), x(t+τ), x(t+2τ)
- XY projection, Z color-coded (blue→red)
- Lorenz butterfly, Rössler spiral visualization

**Return Map:**
- x(t) vs x(t+1) scatter plot
- y=x diagonal reference line
- Chaotic/periodic structure analysis

τ and m parameters automatically come from Step 4, manual override available.

### Chaos Analysis (Step 6)

**Lyapunov Exponent:**
- Wolf algorithm (KD-Tree, faithful MATLAB port) or Rosenstein algorithm
- Result displayed as λ₁ with qualitative interpretation (chaotic / weak chaos / periodic / stable)

**Full Lyapunov Spectrum:**
- Sano-Sawada / Eckmann-Ruelle method (local Jacobians + QR re-orthonormalization)
- Reports all m exponents, Kaplan-Yorke dimension D_KY, and Kolmogorov-Sinai entropy h_KS

**Poincaré Section (live slider):**
- Select the embedding axis (0 … m−1) and drag the slider to sweep the section plane in real time
- Embedding is cached on data load — only the fast crossing-detection step reruns on each slider tick (150 ms debounce)
- Direction: upward crossings (+), downward (−), or both
- N crossing points shown live; plot updates without clicking Calculate

**Correlation Dimension:**
- Grassberger-Procaccia, log-log slope estimation over configurable fit range

### Data Summary Panel

Every loaded time series (file or generated) shows a compact summary above the data table:

| Field | Example |
|---|---|
| Length | 10,000 points |
| dt | 0.01 |
| Total Duration | 100.00 |
| System | lorenz |
| **Parameters** | **sigma=10, rho=28, beta=2.6667** |
| Statistics | Min=… Max=… Mean=… Std=… |

Parameters are populated automatically for all 10 built-in systems and for custom ODE/Map systems.

## Export and Session Management

### Export Features
- **CSV Export**: Export time series data with metadata
- **PNG Export**: Save plots at high resolution (1920x1080)
- **JSON Export**: Export all analysis results in portable format

### Session Management
- **Save (.tsa)**: Binary pickle format — fast and compact
- **Save (.json)**: Human-readable JSON — portable, text-based
- **Session Contents**:
  - Time series data (original + processed)
  - Parameters (tau, m)
  - All analysis results (AMI, FNN, ACF, Lyapunov, etc.)
  - Preprocessing history
  - Metadata and timestamps

### Usage
```python
# Create and save session
from core.session import AnalysisSession

session = AnalysisSession()
session.set_timeseries(my_timeseries)
session.set_parameters(tau=10, m=3)
session.save_pickle("my_analysis.tsa")  # or .json

# Load session
loaded = AnalysisSession.load_pickle("my_analysis.tsa")
print(loaded.tau, loaded.m)
```

## Custom ODE / Discrete Map Systems

The **Custom ODE/Map** panel lets you define your own dynamical system using symbolic expressions, without writing any code.

### ODE Systems (Continuous)

Enter one equation per variable in the form `dx/dt = ...`. Supports up to 6 coupled equations.

**Example — Lorenz System:**
```
dx/dt = s*(y-x)
dy/dt = x*(r-z)-y
dz/dt = x*y-b*z
Parameters: s=10, r=28, b=8/3
```

**Example — Van der Pol Oscillator:**
```
dx/dt = y
dy/dt = mu*(1-x**2)*y-x
Parameters: mu=1.5
```

### Discrete Map Systems

Enter one expression per variable separated by `;`.

**Example — Logistic Map:**
```
x_(n+1) = r*x*(1-x)
Parameters: r=3.9
```

**Example — Hénon Map:**
```
x_(n+1) = 1-a*x**2+y
y_(n+1) = b*x
Parameters: a=1.4, b=0.3
```

### Supported Math Functions

`sin`, `cos`, `tan`, `exp`, `log`, `sqrt`, `abs`, `sinh`, `cosh`, `tanh`, `asin`, `acos`, `atan`, `pi`, `e`

### Parameter Format

Parameters are entered as comma-separated `name=value` pairs. The following value formats are all accepted:

| Format | Example | Result |
|--------|---------|--------|
| Integer | `10` | 10.0 |
| Decimal | `2.666` | 2.666 |
| Fraction | `8/3` | 2.6666… |
| Power | `2**3` | 8.0 |
| Scientific notation | `1e-3` | 0.001 |
| Negative | `-0.5` | -0.5 |

**Valid parameter string examples:**
```
s=10, r=28, b=8/3
alpha=1e-3, beta=2**4, gamma=-0.5
mu=1.5
```

### Time Step (dt) Recommendations

RK4 integration requires a sufficiently small `dt` to remain stable. If NaN values appear in the results, reduce `dt`:

| System type | Recommended dt |
|-------------|---------------|
| Lorenz, Rössler, Chen | ≤ 0.05 (ideal: 0.01) |
| Chua, Duffing | ≤ 0.01 |
| Slow / linear systems | 0.05 – 0.1 |
| Discrete maps | dt = 1 (fixed) |

If the integration diverges, the application will show an error message specifying at which step NaN occurred, along with a recommendation to reduce `dt`.

## Technical Notes

- **Parameter selection is data-driven**: tau and m values are automatically computed via AMI and FNN; no manual defaults embedded.
- **Wolf algorithm** faithfully follows original MATLAB implementation (Alan Wolf, 1985). Wolf tends to overestimate by design — a known characteristic of the algorithm.
- **Rosenstein auto-fit** uses full curve R² >= 0.98 validation + multi-window rolling slope saturation detection.
- **LE stability test**: Variations in m±1 and tau±10% yield CV (coefficient of variation) < 0.20 → result considered reliable. 8/10 systems are stable.
- **KD-Tree** (scipy.spatial.cKDTree) used for neighbor searches in Wolf and Rosenstein algorithms.

## Validation and Test Strategy

This project uses a two-level validation approach:

### 1. Scientific Validation (test_validation.py)
**Purpose**: Test algorithm correctness against literature references.

```bash
python tests/test_validation.py
```

- Tests Wolf, Rosenstein, and Kantz algorithms on **10 chaotic systems**
- Compares against **literature LE values** (e.g., Lorenz 0.9056 nats/s)
- Uses **data-driven parameter selection** (AMI + FNN auto-finds tau and m)
- Performs **stability analysis** (m±1, tau±10% variations with CV<0.20 check)
- **Result**: 7/10 systems <10% error, 10/10 systems <20% error

**Why needed?** Demonstrates algorithms work correctly and produce reliable results across different dynamical systems.

### 2. MATLAB Compatibility Tests (test_wolf_matlab_match.py)
**Purpose**: Verify Wolf was correctly translated from original MATLAB code.

```bash
python tests/test_wolf_matlab_match.py
```

**Test #1: Lorenz (Data2.lor)**
- Wolf's own data file (16384 points, σ=10, ρ=28, β=8/3)
- **Identical parameters**: `tau=10, m=3, dt=0.01, evolve=20, dismin=0.001, dismax=0.3, thmax=30°`
- **Result**: Python 2.01 bits/s | Wolf ~2.1 bits/s | **Difference: 4.1%** ✅

**Test #2: Logistic Map**
- 512 iterations, x(n+1) = 4x(n)(1-x(n))
- **Identical parameters**: `tau=1, m=2, evolve=3, dismin=0.0001, dismax=0.05`
- **Result**: Python 1.00 bits/iter | Wolf 0.98 | Theory 1.0 | **Difference: 2.2% (Wolf), 0.1% (Theory)** ✅

**Why needed?**
- Wolf algorithm was translated from MATLAB → must verify correctness
- 2-4% difference acceptable: different nearest-neighbor implementations (MATLAB grid vs Python KDTree)
- Wolf documentation uses "approximately"
- Test #2: 0.1% error vs theory → mathematics is correct

**Difference between tests:**
- `test_validation.py` → **Scientific correctness** (literature comparison, data-driven parameters)
- `test_wolf_matlab_match.py` → **Implementation correctness** (MATLAB comparison, fixed parameters)

## License

MIT

