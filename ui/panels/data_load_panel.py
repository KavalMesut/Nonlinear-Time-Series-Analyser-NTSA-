"""
Data loading panel with drag-drop and file browser support
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QGroupBox, QFileDialog,
    QFormLayout, QRadioButton, QButtonGroup, QTextEdit, QSpinBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import os
import ast
import operator
import numpy as np


def _safe_eval_number(expr_str: str) -> float:
    """
    Güvenli sayısal ifade değerlendirici.
    8/3, 2**3, 1e-3, -0.5 gibi basit aritmetik ifadeleri kabul eder.
    """
    _ops = {
        ast.Add:  operator.add,
        ast.Sub:  operator.sub,
        ast.Mult: operator.mul,
        ast.Div:  operator.truediv,
        ast.Pow:  operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _eval(node):
        if isinstance(node, ast.Constant):
            return float(node.value)
        elif isinstance(node, ast.BinOp):
            return _ops[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return _ops[type(node.op)](_eval(node.operand))
        else:
            raise ValueError(f"Unsupported expression type: {ast.dump(node)}")

    tree = ast.parse(expr_str.strip(), mode='eval')
    return float(_eval(tree.body))


class DataLoadPanel(QWidget):
    """Data loading panel with drag-drop and file selection"""

    data_loaded = Signal(object)  # Emits TimeSeries object

    def __init__(self, translation_manager):
        super().__init__()
        self.tm = translation_manager
        self.setAcceptDrops(True)
        self._last_ode_ts = None   # Son ODE entegrasyon sonucu (yeniden hesaplama olmadan değişken seçimi için)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        # Scroll area — denklem sayısı arttıkça panel aşağı uzasın
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        outer_layout.addWidget(scroll)

        _content = QWidget()
        scroll.setWidget(_content)

        layout = QVBoxLayout(_content)
        layout.setContentsMargins(10, 10, 10, 10)

        # ── Radio button stilleri ────────────────────────────────────────
        self.radio_style_inactive = """
            QRadioButton {
                background-color: #2a2a2a;
                border: 1px solid #3f3f3f;
                border-radius: 5px;
                padding: 8px 16px;
                padding-left: 16px;
                font-size: 10pt;
                color: #808080;
            }
            QRadioButton::indicator { width: 0; height: 0; border: none; background: none; }
        """
        self.radio_style_active = """
            QRadioButton {
                background-color: #50C878;
                border: 1px solid #3fa862;
                border-radius: 5px;
                padding: 8px 16px;
                padding-left: 16px;
                font-size: 10pt;
                color: #ffffff;
                font-weight: bold;
            }
            QRadioButton::indicator { width: 0; height: 0; border: none; background: none; }
        """

        # ── Kaynak seçimi (Dosya / Sistem Oluştur) ───────────────────────
        source_group = QGroupBox(self.tm('data_source'))
        source_layout = QVBoxLayout()
        source_layout.setSpacing(8)

        self.source_group = QButtonGroup()
        self.file_radio = QRadioButton(self.tm('data_load_file'))
        self.generate_radio = QRadioButton(self.tm('data_generate'))
        self.file_radio.setChecked(True)
        self.file_radio.setStyleSheet(self.radio_style_active)
        self.generate_radio.setStyleSheet(self.radio_style_inactive)

        self.source_group.addButton(self.file_radio, 0)
        self.source_group.addButton(self.generate_radio, 1)

        self.file_radio.toggled.connect(self.on_source_changed)
        self.generate_radio.toggled.connect(self.on_source_changed)

        source_layout.addWidget(self.file_radio)
        source_layout.addWidget(self.generate_radio)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # ── Dosya yükleme grubu ─────────────────────────────────────────
        self.file_group = QGroupBox(self.tm('data_load_file'))
        file_layout = QVBoxLayout()

        self.drop_label = QLabel(self.tm('data_load_file') + '\n\n' +
                                 '📁 ' + self.tm('data_browse') + '\n' +
                                 '🔽 ' + self.tm('data_drag_drop'))
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setMinimumHeight(100)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #666;
                border-radius: 5px;
                background-color: rgba(255, 255, 255, 0.05);
                font-size: 11pt;
            }
        """)
        file_layout.addWidget(self.drop_label)

        file_path_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText(self.tm('data_file_path'))
        self.file_path_input.setReadOnly(True)
        file_path_layout.addWidget(self.file_path_input)

        self.browse_button = QPushButton(self.tm('data_browse'))
        self.browse_button.clicked.connect(self.browse_file)
        file_path_layout.addWidget(self.browse_button)
        file_layout.addLayout(file_path_layout)

        file_params_layout = QFormLayout()
        self.dt_file_input = QLineEdit()
        self.dt_file_input.setText("1.0")
        self.dt_file_input.setPlaceholderText("0.001 - 100.0")
        file_params_layout.addRow(self.tm('data_dt') + ':', self.dt_file_input)
        file_layout.addLayout(file_params_layout)

        self.file_group.setLayout(file_layout)
        layout.addWidget(self.file_group)

        # ── Sistem Oluştur grubu ────────────────────────────────────────
        self.generate_group = QGroupBox(self.tm('data_generate'))
        generate_layout = QVBoxLayout()
        generate_layout.setSpacing(8)

        # Üç seçenek: ODE | Discrete Map | Test Sistemleri
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(6)
        self.ode_radio = QRadioButton(self.tm("data_ode"))
        self.map_radio = QRadioButton(self.tm("data_discrete_map"))
        self.test_systems_radio = QRadioButton(self.tm("data_test_systems"))
        self.ode_radio.setChecked(True)
        self.ode_radio.setStyleSheet(self.radio_style_active)
        self.map_radio.setStyleSheet(self.radio_style_inactive)
        self.test_systems_radio.setStyleSheet(self.radio_style_inactive)

        self.ode_radio.toggled.connect(self.on_generate_mode_changed)
        self.map_radio.toggled.connect(self.on_generate_mode_changed)
        self.test_systems_radio.toggled.connect(self.on_generate_mode_changed)

        mode_layout.addWidget(self.ode_radio)
        mode_layout.addWidget(self.map_radio)
        mode_layout.addWidget(self.test_systems_radio)
        mode_layout.addStretch()
        generate_layout.addLayout(mode_layout)

        # ── ODE bölümü ──────────────────────────────────────────────────
        self.ode_section = QWidget()
        ode_sec_layout = QVBoxLayout(self.ode_section)
        ode_sec_layout.setContentsMargins(0, 4, 0, 0)
        ode_sec_layout.setSpacing(6)

        ode_count_layout = QHBoxLayout()
        ode_count_layout.setSpacing(12)
        ode_count_label = QLabel(self.tm("data_eq_count") + ":")
        ode_count_label.setMinimumWidth(120)
        self.ode_eq_count_spinbox = QSpinBox()
        self.ode_eq_count_spinbox.setMinimum(1)
        self.ode_eq_count_spinbox.setMaximum(6)
        self.ode_eq_count_spinbox.setValue(3)
        self.ode_eq_count_spinbox.setMinimumWidth(100)
        self.ode_eq_count_spinbox.valueChanged.connect(self.on_ode_equation_count_changed)
        ode_count_layout.addWidget(ode_count_label)
        ode_count_layout.addWidget(self.ode_eq_count_spinbox)
        ode_count_layout.addStretch()
        ode_sec_layout.addLayout(ode_count_layout)

        self.ode_equations_container = QWidget()
        self.ode_equations_layout = QVBoxLayout(self.ode_equations_container)
        self.ode_equations_layout.setContentsMargins(10, 0, 0, 0)
        self.ode_equations_layout.setSpacing(8)
        self.ode_equations_inputs = []
        ode_sec_layout.addWidget(self.ode_equations_container)

        # Çıktı değişkeni seçici (tek denklemde gizli)
        self.ode_output_var_row = QWidget()
        ode_out_layout = QHBoxLayout(self.ode_output_var_row)
        ode_out_layout.setContentsMargins(0, 0, 0, 0)
        ode_out_label = QLabel(self.tm("data_output_var") + ":")
        ode_out_label.setMinimumWidth(120)
        self.ode_output_var_combo = QComboBox()
        self.ode_output_var_combo.setMinimumWidth(100)
        ode_out_layout.addWidget(ode_out_label)
        ode_out_layout.addWidget(self.ode_output_var_combo)
        ode_out_layout.addStretch()
        self.ode_output_var_row.setVisible(False)
        ode_sec_layout.addWidget(self.ode_output_var_row)

        # Combo değişince yeniden entegrasyon yapmadan grafiği güncelle
        self.ode_output_var_combo.currentIndexChanged.connect(self.on_output_var_changed)

        generate_layout.addWidget(self.ode_section)

        # ── Discrete Map bölümü ─────────────────────────────────────────
        self.map_section = QWidget()
        map_sec_layout = QVBoxLayout(self.map_section)
        map_sec_layout.setContentsMargins(0, 4, 0, 0)
        map_sec_layout.setSpacing(6)

        map_count_layout = QHBoxLayout()
        map_count_layout.setSpacing(12)
        map_count_label = QLabel(self.tm("data_eq_count") + ":")
        map_count_label.setMinimumWidth(120)
        self.map_eq_count_spinbox = QSpinBox()
        self.map_eq_count_spinbox.setMinimum(1)
        self.map_eq_count_spinbox.setMaximum(3)
        self.map_eq_count_spinbox.setValue(1)
        self.map_eq_count_spinbox.setMinimumWidth(100)
        self.map_eq_count_spinbox.valueChanged.connect(self.on_map_equation_count_changed)
        map_count_layout.addWidget(map_count_label)
        map_count_layout.addWidget(self.map_eq_count_spinbox)
        map_count_layout.addStretch()
        map_sec_layout.addLayout(map_count_layout)

        self.map_equations_container = QWidget()
        self.map_equations_layout = QVBoxLayout(self.map_equations_container)
        self.map_equations_layout.setContentsMargins(10, 0, 0, 0)
        self.map_equations_layout.setSpacing(8)
        self.map_equations_inputs = []
        map_sec_layout.addWidget(self.map_equations_container)

        generate_layout.addWidget(self.map_section)
        self.map_section.setVisible(False)

        # ── ODE + Map ortak parametreler ────────────────────────────────
        self.custom_params_section = QWidget()
        cp_layout = QVBoxLayout(self.custom_params_section)
        cp_layout.setContentsMargins(0, 4, 0, 0)
        cp_layout.setSpacing(6)

        cp_layout.addWidget(QLabel("─" * 60))

        param_layout = QHBoxLayout()
        param_label = QLabel(self.tm("data_parameters") + ":")
        self.param_input = QLineEdit()
        self.param_input.setPlaceholderText("s=10, r=28, b=8/3")
        param_layout.addWidget(param_label)
        param_layout.addWidget(self.param_input)
        cp_layout.addLayout(param_layout)

        points_layout = QHBoxLayout()
        points_label = QLabel(self.tm("data_n_points") + ":")
        self.custom_n_points = QLineEdit()
        self.custom_n_points.setText("5000")
        self.custom_n_points.setMaximumWidth(100)
        points_layout.addWidget(points_label)
        points_layout.addWidget(self.custom_n_points)
        points_layout.addStretch()
        cp_layout.addLayout(points_layout)

        dt_layout = QHBoxLayout()
        dt_label = QLabel(self.tm("data_timestep") + ":")
        self.custom_dt = QLineEdit()
        self.custom_dt.setText("0.01")
        self.custom_dt.setMaximumWidth(100)
        dt_layout.addWidget(dt_label)
        dt_layout.addWidget(self.custom_dt)
        dt_layout.addStretch()
        cp_layout.addLayout(dt_layout)

        generate_layout.addWidget(self.custom_params_section)

        # ── Test Sistemleri bölümü ───────────────────────────────────────
        self.test_section = QWidget()
        test_sec_layout = QVBoxLayout(self.test_section)
        test_sec_layout.setContentsMargins(0, 4, 0, 0)
        test_sec_layout.setSpacing(6)

        test_form = QFormLayout()

        self.system_combo = QComboBox()
        self.system_combo.addItem(self.tm('data_lorenz'), 'lorenz')
        self.system_combo.addItem(self.tm('data_rossler'), 'rossler')
        self.system_combo.addItem('Chua', 'chua')
        self.system_combo.addItem('Chen', 'chen')
        self.system_combo.addItem('Duffing', 'duffing')
        self.system_combo.addItem(self.tm('data_logistic'), 'logistic')
        self.system_combo.addItem('Hénon Map', 'henon')
        self.system_combo.addItem('Tent Map', 'tent')
        self.system_combo.addItem(self.tm('data_sine'), 'sine')
        self.system_combo.addItem('Ikeda Map', 'ikeda')
        test_form.addRow(self.tm('data_system_type') + ':', self.system_combo)

        self.n_points_input = QLineEdit()
        self.n_points_input.setText("5000")
        self.n_points_input.setPlaceholderText("100 - 1000000")
        test_form.addRow(self.tm('data_points') + ':', self.n_points_input)

        self.dt_gen_input = QLineEdit()
        self.dt_gen_input.setText("0.01")
        self.dt_gen_input.setPlaceholderText("0.001 - 10.0")
        test_form.addRow(self.tm('data_dt') + ':', self.dt_gen_input)

        test_sec_layout.addLayout(test_form)
        generate_layout.addWidget(self.test_section)
        self.test_section.setVisible(False)

        self.generate_group.setLayout(generate_layout)
        layout.addWidget(self.generate_group)

        # ── Yükle butonu ────────────────────────────────────────────────
        self.load_button = QPushButton(self.tm('data_load_button'))
        self.load_button.clicked.connect(self.load_data)
        self.load_button.setMinimumHeight(40)
        layout.addWidget(self.load_button)
        layout.addStretch()

        # Başlangıç durumu
        self.on_source_changed()
        self.on_ode_equation_count_changed(self.ode_eq_count_spinbox.value())
        self.on_map_equation_count_changed(self.map_eq_count_spinbox.value())

    # ────────────────────────────────────────────────────────────────────
    # Radio buton stilleri
    # ────────────────────────────────────────────────────────────────────
    def _update_radio_styles(self):
        # Kaynak grubu
        if self.file_radio.isChecked():
            self.file_radio.setStyleSheet(self.radio_style_active)
            self.generate_radio.setStyleSheet(self.radio_style_inactive)
        else:
            self.file_radio.setStyleSheet(self.radio_style_inactive)
            self.generate_radio.setStyleSheet(self.radio_style_active)

        # Mod grubu (ODE / Map / Test)
        self.ode_radio.setStyleSheet(
            self.radio_style_active if self.ode_radio.isChecked() else self.radio_style_inactive)
        self.map_radio.setStyleSheet(
            self.radio_style_active if self.map_radio.isChecked() else self.radio_style_inactive)
        self.test_systems_radio.setStyleSheet(
            self.radio_style_active if self.test_systems_radio.isChecked() else self.radio_style_inactive)

    # ────────────────────────────────────────────────────────────────────
    # Olay işleyicileri
    # ────────────────────────────────────────────────────────────────────
    def on_source_changed(self):
        is_file = self.file_radio.isChecked()
        self.file_group.setVisible(is_file)
        self.generate_group.setVisible(not is_file)
        self._update_radio_styles()

    def on_generate_mode_changed(self):
        is_ode  = self.ode_radio.isChecked()
        is_map  = self.map_radio.isChecked()
        is_test = self.test_systems_radio.isChecked()

        self.ode_section.setVisible(is_ode)
        self.map_section.setVisible(is_map)
        self.custom_params_section.setVisible(is_ode or is_map)
        self.test_section.setVisible(is_test)
        self._update_radio_styles()

    def on_ode_equation_count_changed(self, count: int):
        # Denklem sayısı değişince cache'i sıfırla — eski entegrasyon geçersiz
        self._last_ode_ts = None
        while self.ode_equations_layout.count():
            item = self.ode_equations_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self._clear_layout(item.layout())
        self.ode_equations_inputs.clear()

        var_names = ['x', 'y', 'z', 'u', 'v', 'w']
        for i in range(count):
            label = QLabel(f"d{var_names[i]}/dt =")
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"e.g.: sigma*({var_names[(i+1)%count]}-{var_names[i]})")
            input_field.setMinimumHeight(30)
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(label, 0)
            row_layout.addWidget(input_field, 1)
            self.ode_equations_layout.addLayout(row_layout)
            self.ode_equations_inputs.append(input_field)

        if hasattr(self, 'ode_output_var_combo'):
            self.ode_output_var_combo.clear()
            for i in range(count):
                self.ode_output_var_combo.addItem(var_names[i], i)
            self.ode_output_var_row.setVisible(count > 1)

    def on_map_equation_count_changed(self, count: int):
        while self.map_equations_layout.count():
            item = self.map_equations_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self._clear_layout(item.layout())
        self.map_equations_inputs.clear()

        var_names = ['x', 'y', 'z']
        for i in range(count):
            label = QLabel(f"{var_names[i]}_(n+1) =")
            input_field = QLineEdit()
            if count == 1:
                input_field.setPlaceholderText("e.g.: 4*x*(1-x)")
            else:
                input_field.setPlaceholderText(
                    f"e.g.: 1-a*{var_names[i]}**2+{var_names[(i+1)%count]}")
            input_field.setMinimumHeight(30)
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.addWidget(label, 0)
            row_layout.addWidget(input_field, 1)
            self.map_equations_layout.addLayout(row_layout)
            self.map_equations_inputs.append(input_field)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            elif item.layout():
                self._clear_layout(item.layout())

    # ────────────────────────────────────────────────────────────────────
    # Dosya sürükleme
    # ────────────────────────────────────────────────────────────────────
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tm('data_load_file'), '',
            'Data Files (*.csv *.txt *.dat);;All Files (*.*)'
        )
        if file_path:
            self.file_path_input.setText(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_label.setStyleSheet("""
                QLabel { border: 2px dashed #0e639c; border-radius: 5px;
                         background-color: rgba(14,99,156,0.2); font-size: 11pt; }
            """)

    def dragLeaveEvent(self, event):
        self.drop_label.setStyleSheet("""
            QLabel { border: 2px dashed #666; border-radius: 5px;
                     background-color: rgba(255,255,255,0.05); font-size: 11pt; }
        """)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if os.path.isfile(file_path):
                self.file_path_input.setText(file_path)
                self.file_radio.setChecked(True)
                event.acceptProposedAction()
        self.drop_label.setStyleSheet("""
            QLabel { border: 2px dashed #666; border-radius: 5px;
                     background-color: rgba(255,255,255,0.05); font-size: 11pt; }
        """)

    # ────────────────────────────────────────────────────────────────────
    # Veri yükleme
    # ────────────────────────────────────────────────────────────────────
    def load_data(self):
        try:
            if self.file_radio.isChecked():
                file_path = self.file_path_input.text()
                if not file_path:
                    return
                from core.loaders import load_csv, load_txt
                ext = os.path.splitext(file_path)[1].lower()
                try:
                    dt = float(self.dt_file_input.text())
                    if dt <= 0 or dt > 100:
                        raise ValueError()
                except ValueError:
                    dt = 1.0
                ts = load_csv(file_path, dt=dt) if ext == '.csv' else load_txt(file_path, dt=dt)
                self.data_loaded.emit(ts)

            elif self.test_systems_radio.isChecked():
                system_type = self.system_combo.currentData()
                try:
                    n_points = int(self.n_points_input.text())
                    if n_points < 100 or n_points > 1000000:
                        raise ValueError()
                except ValueError:
                    n_points = 5000
                try:
                    dt = float(self.dt_gen_input.text())
                    if dt <= 0 or dt > 10:
                        raise ValueError()
                except ValueError:
                    dt = 0.01

                from core.generators import (
                    generate_lorenz, generate_rossler, generate_chua, generate_chen,
                    generate_duffing, logistic_map, henon_map, tent_map,
                    generate_sine, ikeda_map
                )
                system_map = {
                    'lorenz':   lambda: generate_lorenz(t_span=(0, n_points*dt), dt=dt),
                    'rossler':  lambda: generate_rossler(t_span=(0, n_points*dt), dt=dt),
                    'chua':     lambda: generate_chua(t_span=(0, n_points*dt), dt=dt),
                    'chen':     lambda: generate_chen(t_span=(0, n_points*dt), dt=dt),
                    'duffing':  lambda: generate_duffing(t_span=(0, n_points*dt), dt=dt),
                    'logistic': lambda: logistic_map(n=n_points),
                    'henon':    lambda: henon_map(n=n_points),
                    'tent':     lambda: tent_map(n=n_points),
                    'sine':     lambda: generate_sine(n=n_points, dt=dt),
                    'ikeda':    lambda: ikeda_map(n=n_points),
                }
                ts = system_map.get(
                    system_type,
                    lambda: generate_lorenz(t_span=(0, n_points*dt), dt=dt)
                )()
                self.data_loaded.emit(ts)

            else:
                # ODE veya Discrete Map
                try:
                    # Parametreleri parse et
                    param_str = self.param_input.text()
                    params = {}
                    if param_str.strip():
                        for item in param_str.split(','):
                            if '=' not in item:
                                continue
                            key, val = item.split('=', 1)
                            try:
                                params[key.strip()] = _safe_eval_number(val.strip())
                            except Exception:
                                from PySide6.QtWidgets import QMessageBox
                                QMessageBox.critical(
                                    self, "Parameter Error",
                                    f"Could not parse value for parameter '{key.strip()}': {val.strip()}\n"
                                    "Valid formats: 10, 2.666, 8/3, 2**3, 1e-3"
                                )
                                return

                    n_points = int(self.custom_n_points.text())
                    dt = float(self.custom_dt.text())

                    from core.custom_system import (
                        parse_ode_system, parse_map_system,
                        integrate_custom_ode, iterate_custom_map
                    )

                    if self.ode_radio.isChecked():
                        expressions = {}
                        var_names = ['x', 'y', 'z', 'u', 'v', 'w']
                        for i, field in enumerate(self.ode_equations_inputs):
                            expr_text = field.text().strip()
                            if not expr_text:
                                from PySide6.QtWidgets import QMessageBox
                                QMessageBox.warning(self, "Missing Equation",
                                                    f"Equation {i+1} cannot be empty.")
                                return
                            expressions[f"d{var_names[i]}/dt"] = expr_text

                        rhs, var_names_parsed = parse_ode_system(expressions)

                        # Eksik parametre uyarısı
                        missing = [p for p in getattr(rhs, 'param_names', []) if p not in params]
                        if missing:
                            from PySide6.QtWidgets import QMessageBox
                            reply = QMessageBox.warning(
                                self, "Missing Parameters",
                                "Parameters used in equations but not provided:\n\n"
                                f"  {', '.join(missing)}\n\n"
                                "They will be treated as 0, results may be incorrect.\n"
                                "Do you want to continue anyway?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No
                            )
                            if reply == QMessageBox.No:
                                return

                        y0 = np.array([0.1 * (i + 1) for i in range(len(var_names_parsed))])
                        output_idx = 0
                        if len(var_names_parsed) > 1 and hasattr(self, 'ode_output_var_combo'):
                            combo_data = self.ode_output_var_combo.currentData()
                            output_idx = combo_data if combo_data is not None else 0

                        ts = integrate_custom_ode(rhs, y0, t_span=(0, n_points*dt),
                                                  dt=dt, params=params, system_name='custom_ode',
                                                  output_var_idx=output_idx,
                                                  var_names=var_names_parsed)
                        # Tüm değişkenler hesaplandı; combo değişince yeniden entegrasyon yapmadan kullan
                        self._last_ode_ts = ts

                    else:
                        # Discrete Map
                        if not self.map_equations_inputs:
                            from PySide6.QtWidgets import QMessageBox
                            QMessageBox.warning(self, "Error", "No map equation defined.")
                            return

                        all_map_var_names = ['x', 'y', 'z']
                        expressions = []
                        for i, field in enumerate(self.map_equations_inputs):
                            expr_text = field.text().strip()
                            if not expr_text:
                                from PySide6.QtWidgets import QMessageBox
                                QMessageBox.warning(self, "Missing Equation",
                                                    f"Map equation {i+1} cannot be empty.")
                                return
                            expressions.append(expr_text)

                        actual_map_var_names = all_map_var_names[:len(expressions)]
                        map_fn, var_names_parsed = parse_map_system(
                            "; ".join(expressions), var_names=actual_map_var_names
                        )

                        missing_map = [p for p in getattr(map_fn, 'param_names', []) if p not in params]
                        if missing_map:
                            from PySide6.QtWidgets import QMessageBox
                            reply = QMessageBox.warning(
                                self, "Missing Parameters",
                                "Parameters used in map but not provided:\n\n"
                                f"  {', '.join(missing_map)}\n\n"
                                "They will be treated as 0, results may be incorrect.\n"
                                "Do you want to continue anyway?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No
                            )
                            if reply == QMessageBox.No:
                                return

                        x0 = np.ones(len(var_names_parsed)) * 0.5
                        ts = iterate_custom_map(map_fn, x0, n_steps=n_points,
                                               params=params, system_name='custom_map')

                    self.data_loaded.emit(ts)

                except Exception as e:
                    import traceback
                    from PySide6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "System Error",
                                         f"Error: {str(e)}\n\n{traceback.format_exc()}")

        except Exception:
            pass

    def on_output_var_changed(self):
        """Çıktı değişkeni seçilince yeniden entegrasyon yapmadan grafiği güncelle."""
        if self._last_ode_ts is None:
            return
        combo_data = self.ode_output_var_combo.currentData()
        if combo_data is None:
            return
        meta = dict(self._last_ode_ts.metadata)
        var_names = meta.get('var_names', [])
        all_vars = meta.get('all_vars_data', {})
        output_idx = combo_data
        if output_idx >= len(var_names):
            return
        var_name = var_names[output_idx]
        if var_name not in all_vars:
            return
        from core.timeseries import TimeSeries
        meta['output_var_idx'] = output_idx
        meta['output_var_name'] = var_name
        new_ts = TimeSeries(data=all_vars[var_name], dt=self._last_ode_ts.dt, metadata=meta)
        self.data_loaded.emit(new_ts)

    def refresh_ui(self):
        self.file_radio.setText(self.tm('data_load_file'))
        self.generate_radio.setText(self.tm('data_generate'))
        self.file_group.setTitle(self.tm('data_load_file'))
        self.generate_group.setTitle(self.tm('data_generate'))
        self.browse_button.setText(self.tm('data_browse'))
        self.load_button.setText(self.tm('data_load_button'))
        self.ode_radio.setText(self.tm('data_ode'))
        self.map_radio.setText(self.tm('data_discrete_map'))
        self.test_systems_radio.setText(self.tm('data_test_systems'))
        self.drop_label.setText(
            self.tm('data_load_file') + '\n\n'
            + '\U0001f4c1 ' + self.tm('data_browse') + '\n'
            + '\U0001f53d ' + self.tm('data_drag_drop')
        )
