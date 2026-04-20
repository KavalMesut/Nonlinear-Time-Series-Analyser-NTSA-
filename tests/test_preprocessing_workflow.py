import os
import sys
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from PySide6.QtWidgets import QApplication

from analysis import estimate_theiler_window, lyapunov_kantz, estimate_lyapunov_from_curve
from core.preprocessing import denoise
from core.timeseries import TimeSeries
from core.generators import logistic_map
from ui.themes import ThemeManager
from ui.translations import TranslationManager
from ui.panels.preprocessing_panel import PreprocessingPanel
from ui.panels.parameter_estimation_panel import ParameterEstimationPanel
from ui.panels.content_panel import ContentPanel


class PreprocessingWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_difference_keeps_dt_and_shifts_time_origin(self):
        panel = PreprocessingPanel(TranslationManager())
        source = TimeSeries(np.array([1.0, 3.0, 6.0, 10.0]), dt=0.5, t0=2.0)
        result = np.diff(source.data)

        processed = panel._build_result_series(
            source,
            result,
            'difference',
            {'order': 1}
        )

        self.assertEqual(processed.dt, 0.5)
        self.assertEqual(processed.t0, 2.5)
        np.testing.assert_allclose(processed.time, np.array([2.5, 3.0, 3.5]))

    def test_window_keeps_original_sampling_and_selected_time_range(self):
        panel = PreprocessingPanel(TranslationManager())
        source = TimeSeries(np.arange(8, dtype=float), dt=0.25, t0=1.0)
        result = source.data[2:6]

        processed = panel._build_result_series(
            source,
            result,
            'window',
            {'start': 2, 'end': 6}
        )

        self.assertEqual(processed.dt, 0.25)
        self.assertEqual(processed.t0, 1.5)
        np.testing.assert_allclose(processed.time, np.array([1.5, 1.75, 2.0, 2.25]))

    def test_parameter_panel_resets_tau_and_m_for_new_data(self):
        panel = ParameterEstimationPanel(TranslationManager())
        panel.tau = 7
        panel.m = 4
        panel.tau_result_label.setText("τ = 7")
        panel.m_result_label.setText("m = 4")
        panel.estimate_m_button.setEnabled(True)

        panel.set_data(TimeSeries(np.arange(10, dtype=float), dt=1.0))

        self.assertIsNone(panel.tau)
        self.assertIsNone(panel.m)
        self.assertEqual(panel.tau_result_label.text(), "τ = ?")
        self.assertEqual(panel.m_result_label.text(), "m = ?")
        self.assertFalse(panel.estimate_m_button.isEnabled())

    def test_wavelet_denoise_requires_pywavelets(self):
        original_import = __import__

        def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "pywt":
                raise ImportError("missing pywt")
            return original_import(name, globals, locals, fromlist, level)

        with mock.patch("builtins.__import__", side_effect=fake_import):
            with self.assertRaisesRegex(ImportError, "PyWavelets"):
                denoise(np.arange(8, dtype=float), method='wavelet')

    def test_theiler_window_respects_embedding_floor(self):
        data = np.sin(np.linspace(0, 8 * np.pi, 400))
        min_window = estimate_theiler_window(data, m=3, tau=5)
        self.assertGreaterEqual(min_window, 15)

    def test_kantz_estimates_logistic_map_reasonably(self):
        ts = logistic_map(n=5000)
        data = ts.data[100:]
        t_steps, divergence = lyapunov_kantz(
            data, m=2, tau=1, dt=1.0, min_tsep=2, max_lag=8, max_samples=300, n_neighbors=10
        )
        le = estimate_lyapunov_from_curve(t_steps, divergence, fit_start=1, fit_end=6, auto_fit=False)
        self.assertTrue(np.isfinite(le))
        self.assertLess(abs(le - np.log(2)), 0.15)

    def test_content_panel_clears_chaos_state_after_preprocessing(self):
        panel = ContentPanel(TranslationManager(), ThemeManager())
        original = TimeSeries(np.arange(20, dtype=float), dt=0.1)
        processed = TimeSeries(np.arange(10, dtype=float), dt=0.2, t0=0.5)

        panel.on_data_loaded(original)
        panel.chaos_panel.set_data(original, tau=3, m=5)

        panel.on_data_preprocessed(processed)

        self.assertIs(panel.current_data, processed)
        self.assertIs(panel.chaos_panel.current_data, processed)
        self.assertIsNone(panel.chaos_panel.tau)
        self.assertIsNone(panel.chaos_panel.m)
        self.assertFalse(panel.chaos_panel.calc_lyap_button.isEnabled())
        self.assertEqual(panel.chaos_panel.tau_label.text(), "τ = ?")
        self.assertEqual(panel.chaos_panel.m_label.text(), "m = ?")


if __name__ == "__main__":
    unittest.main()
