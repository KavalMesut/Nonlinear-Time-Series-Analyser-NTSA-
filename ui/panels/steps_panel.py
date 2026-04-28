"""
Steps panel - left sidebar showing analysis steps
"""
import math
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QFont, QPainter, QPen, QBrush, QPainterPath, QColor


# ── Lorenz attractor (precomputed at import) ───────────────────────────────

def _lorenz_pts(n_transient=600, n_record=4000, dt=0.012, sub=5):
    x, y, z = 0.1, 0.0, 0.0
    s, r, b = 10.0, 28.0, 8.0 / 3.0
    for _ in range(n_transient):
        x += s*(y-x)*dt; y += (x*(r-z)-y)*dt; z += (x*y-b*z)*dt
    pts = []
    for i in range(n_record):
        x += s*(y-x)*dt; y += (x*(r-z)-y)*dt; z += (x*y-b*z)*dt
        if i % sub == 0:
            pts.append((x, z))
    xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
    x0, x1 = min(xs), max(xs); z0, z1 = min(zs), max(zs)
    xr = x1-x0 or 1; zr = z1-z0 or 1
    return [((px-x0)/xr, (pz-z0)/zr) for px, pz in pts]


_LORENZ = _lorenz_pts()


# ── Custom icon widget ─────────────────────────────────────────────────────

class StepIconWidget(QWidget):
    """Circular badge with custom-painted scientific icon per step."""

    def __init__(self, step_index: int, size: int = 40):
        super().__init__()
        self.step_index = step_index
        self._completed = False
        self.setFixedSize(size, size)
        self.setStyleSheet("background-color: transparent;")
        self._fg = QColor('#808080')
        self._bg = QColor('#2a2a2a')

    def set_colors(self, fg: str, bg: str):
        self._fg = QColor(fg)
        self._bg = QColor(bg)
        self.update()

    def set_completed(self, completed: bool):
        self._completed = completed
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        sz = self.width()

        # Circle background
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(self._bg))
        p.drawEllipse(1, 1, sz - 2, sz - 2)
        p.setBrush(Qt.NoBrush)

        m = sz * 0.19
        rect = QRectF(m, m, sz - 2*m, sz - 2*m)

        if self._completed:
            pen = QPen(self._fg, 2.3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.setPen(pen)
            cx, cy = sz / 2.0, sz / 2.0
            path = QPainterPath()
            path.moveTo(cx - 6, cy + 0.5)
            path.lineTo(cx - 2, cy + 5)
            path.lineTo(cx + 7, cy - 6)
            p.drawPath(path)
        else:
            pen = QPen(self._fg, 1.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            p.setPen(pen)
            draw_fn = getattr(self, f'_icon_{self.step_index}', None)
            if draw_fn:
                draw_fn(p, rect)
        p.end()

    # ── Step 0: Data Loading (Upload) ────────────────────────────────────
    def _icon_0(self, p: QPainter, r: QRectF):
        x, y, w, h = r.x(), r.y(), r.width(), r.height()

        thick = QPen(p.pen()); thick.setWidthF(1.4); p.setPen(thick)

        # Box (kutu) - SVG: x=3, y=14, width=18, height=6, rx=2
        box_x = x + w * 0.125
        box_y = y + h * 0.583
        box_w = w * 0.75
        box_h = h * 0.25
        box_radius = w * 0.083

        box_rect = QRectF(box_x, box_y, box_w, box_h)
        p.drawRoundedRect(box_rect, box_radius, box_radius)

        # Upward arrow line - SVG: M12 3V14
        arrow_x = x + w * 0.5
        arrow_y_top = y + h * 0.125
        arrow_y_bottom = y + h * 0.583

        p.drawLine(QPointF(arrow_x, arrow_y_top), QPointF(arrow_x, arrow_y_bottom))

        # Arrow head - SVG: M8 7L12 3L16 7
        arrow_left_x = x + w * 0.333
        arrow_left_y = y + h * 0.292
        arrow_tip_x = arrow_x
        arrow_tip_y = arrow_y_top
        arrow_right_x = x + w * 0.667
        arrow_right_y = y + h * 0.292

        arrow_head = QPainterPath()
        arrow_head.moveTo(arrow_left_x, arrow_left_y)
        arrow_head.lineTo(arrow_tip_x, arrow_tip_y)
        arrow_head.lineTo(arrow_right_x, arrow_right_y)
        p.drawPath(arrow_head)

        # 3 dots in box - SVG: circles at (9,17), (12,17), (15,17) with r=0.9
        dot_y = y + h * 0.708
        dot_radius = h * 0.038
        dot_x_positions = [x + w * 0.375, x + w * 0.5, x + w * 0.625]

        p.setBrush(QBrush(self._fg))
        p.setPen(Qt.NoPen)
        for dot_x in dot_x_positions:
            p.drawEllipse(QPointF(dot_x, dot_y), dot_radius, dot_radius)
        p.setPen(thick)
        p.setBrush(Qt.NoBrush)

    # ── Step 1: Preprocessing (Filter) ────────────────────────────────────
    def _icon_1(self, p: QPainter, r: QRectF):
        x, y, w, h = r.x(), r.y(), r.width(), r.height()
        cx = x + w * 0.5

        # Funnel shape (top wide, bottom narrow)
        funnel = QPainterPath()
        top_w = w * 0.65
        bottom_w = w * 0.18
        top_y = y + h * 0.15
        bottom_y = y + h * 0.65

        funnel.moveTo(cx - top_w/2, top_y)
        funnel.lineTo(cx + top_w/2, top_y)
        funnel.lineTo(cx + bottom_w/2, bottom_y)
        funnel.lineTo(cx - bottom_w/2, bottom_y)
        funnel.closeSubpath()

        thick = QPen(p.pen()); thick.setWidthF(1.3); p.setPen(thick)
        p.drawPath(funnel)

        # Particles in funnel (dots getting filtered)
        p.setBrush(QBrush(self._fg))
        p.setPen(Qt.NoPen)
        particle_y_vals = [y + h*0.20, y + h*0.28, y + h*0.32, y + h*0.40, y + h*0.48]
        particle_x_offset = [w*0.15, w*0.25, w*0.35, w*0.20, w*0.30]
        for py, px_off in zip(particle_y_vals, particle_x_offset):
            p.drawEllipse(QPointF(cx - px_off, py), 1.2, 1.2)
            p.drawEllipse(QPointF(cx + px_off, py), 1.2, 1.2)

        # Output stream (clean flow)
        p.setPen(thick)
        p.setBrush(Qt.NoBrush)
        stream = QPainterPath()
        stream.moveTo(cx - bottom_w/4, bottom_y)
        stream.lineTo(cx + bottom_w/4, bottom_y)
        stream.lineTo(cx + bottom_w/6, y + h * 0.85)
        stream.lineTo(cx - bottom_w/6, y + h * 0.85)
        stream.closeSubpath()
        p.drawPath(stream)

        # Arrow at output
        ah = h * 0.10
        arrow_y = y + h * 0.88
        arrow_line = QPen(p.pen()); arrow_line.setWidthF(1.1); p.setPen(arrow_line)
        p.drawLine(QPointF(cx, bottom_y + h*0.05), QPointF(cx, arrow_y - ah))
        p.drawLine(QPointF(cx, arrow_y), QPointF(cx - h*0.08, arrow_y - ah))
        p.drawLine(QPointF(cx, arrow_y), QPointF(cx + h*0.08, arrow_y - ah))

    # ── Step 2: Linear Analysis ───────────────────────────────────────────
    def _icon_2(self, p: QPainter, r: QRectF):
        x, y, w, h = r.x(), r.y(), r.width(), r.height()
        by = y + h * 0.93
        p.drawLine(QPointF(x, by), QPointF(x + w, by))
        heights = [0.85, 0.58, 0.35, 0.20, 0.10]
        n = len(heights)
        slot = w / (n + 0.6)
        bw = slot * 0.55
        for i, ht in enumerate(heights):
            bx = x + (i + 0.55) * slot
            p.drawRect(QRectF(bx - bw/2, by - h*ht, bw, h*ht))

    # ── Step 3: Parameter Estimation (Sliders) ────────────────────────────
    def _icon_3(self, p: QPainter, r: QRectF):
        x, y, w, h = r.x(), r.y(), r.width(), r.height()

        # First slider (τ - tau)
        slider1_y = y + h * 0.35
        slider_w = w * 0.70
        slider_x = x + (w - slider_w) / 2

        track_line = QPen(p.pen()); track_line.setWidthF(1.2); p.setPen(track_line)
        p.drawLine(QPointF(slider_x, slider1_y), QPointF(slider_x + slider_w, slider1_y))

        # Slider thumb 1 (left position)
        thumb_pos1 = slider_x + slider_w * 0.25
        p.setBrush(QBrush(self._fg))
        p.drawEllipse(QPointF(thumb_pos1, slider1_y), 3.5, 3.5)

        # Label τ
        label_x1 = slider_x - h * 0.12
        label_size = h * 0.08
        tau_path = QPainterPath()
        tau_path.moveTo(label_x1 - label_size*0.3, slider1_y - label_size*0.4)
        tau_path.lineTo(label_x1 + label_size*0.3, slider1_y - label_size*0.4)
        tau_path.quadTo(label_x1 - label_size*0.2, slider1_y, label_x1, slider1_y + label_size*0.2)
        p.drawPath(tau_path)

        # Second slider (m - embedding dimension)
        slider2_y = y + h * 0.68
        p.drawLine(QPointF(slider_x, slider2_y), QPointF(slider_x + slider_w, slider2_y))

        # Slider thumb 2 (right position)
        thumb_pos2 = slider_x + slider_w * 0.65
        p.setBrush(QBrush(self._fg))
        p.drawEllipse(QPointF(thumb_pos2, slider2_y), 3.5, 3.5)

        # Label m
        label_x2 = slider_x - h * 0.12
        m_path = QPainterPath()
        m_path.moveTo(label_x2 - label_size*0.2, slider2_y + label_size*0.2)
        m_path.lineTo(label_x2 - label_size*0.2, slider2_y - label_size*0.3)
        m_path.lineTo(label_x2, slider2_y - label_size*0.3)
        m_path.lineTo(label_x2, slider2_y + label_size*0.2)
        m_path.lineTo(label_x2 + label_size*0.2, slider2_y + label_size*0.2)
        p.drawPath(m_path)

    # ── Step 4: Phase Space (3D orbit) ────────────────────────────────────
    def _icon_4(self, p: QPainter, r: QRectF):
        x, y, w, h = r.x(), r.y(), r.width(), r.height()
        ox, oy = x + w*0.36, y + h*0.80

        def axis(x2, y2):
            p.drawLine(QPointF(ox, oy), QPointF(x2, y2))
            dx, dy_ = x2-ox, y2-oy
            ln = math.hypot(dx, dy_) or 1
            ux, uy = dx/ln, dy_/ln
            s = h * 0.09
            p.drawLine(QPointF(x2, y2),
                       QPointF(x2 - ux*s - uy*s*0.55, y2 - uy*s + ux*s*0.55))
            p.drawLine(QPointF(x2, y2),
                       QPointF(x2 - ux*s + uy*s*0.55, y2 - uy*s - ux*s*0.55))

        axis(ox + w*0.60, oy)            # x →
        axis(ox, oy - h*0.68)            # z ↑
        axis(ox - w*0.30, oy - h*0.26)  # y ↗

        # Tilted orbital ellipse
        ec_x, ec_y = ox + w*0.20, oy - h*0.38
        rx_e, ry_e = w*0.30, h*0.16
        ang = math.radians(-20)
        orbit = QPainterPath()
        for i in range(49):
            t = i / 48 * 2 * math.pi
            ex = rx_e * math.cos(t); ey = ry_e * math.sin(t)
            px2 = ex*math.cos(ang) - ey*math.sin(ang) + ec_x
            py2 = ex*math.sin(ang) + ey*math.cos(ang) + ec_y
            if i == 0: orbit.moveTo(px2, py2)
            else: orbit.lineTo(px2, py2)
        orbit.closeSubpath()
        p.drawPath(orbit)

        # Moving dot
        t_d = math.pi * 0.3
        ex = rx_e*math.cos(t_d); ey = ry_e*math.sin(t_d)
        dpx = ex*math.cos(ang) - ey*math.sin(ang) + ec_x
        dpy = ex*math.sin(ang) + ey*math.cos(ang) + ec_y
        p.setBrush(QBrush(self._fg))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(dpx, dpy), 1.9, 1.9)
        p.setPen(QPen(self._fg, 1.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)

    # ── Step 5: Chaos Analysis (Lorenz attractor) ─────────────────────────
    def _icon_5(self, p: QPainter, r: QRectF):
        x, y, w, h = r.x(), r.y(), r.width(), r.height()
        thin = QPen(p.pen()); thin.setWidthF(1.05); p.setPen(thin)
        path = QPainterPath()
        for i, (nx, nz) in enumerate(_LORENZ):
            px = x + nx * w
            py = y + (1.0 - nz) * h
            if i == 0: path.moveTo(px, py)
            else: path.lineTo(px, py)
        p.drawPath(path)

    # ── Step 6: Results (Document) ────────────────────────────────────────
    def _icon_6(self, p: QPainter, r: QRectF):
        x, y, w, h = r.x(), r.y(), r.width(), r.height()

        # Document/paper outline
        doc_w = w * 0.58
        doc_h = h * 0.70
        doc_x = x + (w - doc_w) / 2
        doc_y = y + h * 0.12

        doc_path = QPainterPath()
        doc_path.moveTo(doc_x, doc_y)
        doc_path.lineTo(doc_x + doc_w, doc_y)
        doc_path.lineTo(doc_x + doc_w, doc_y + doc_h)
        doc_path.lineTo(doc_x, doc_y + doc_h)
        doc_path.closeSubpath()

        thick = QPen(p.pen()); thick.setWidthF(1.3); p.setPen(thick)
        p.drawPath(doc_path)

        # Content lines (text representation)
        line_y_positions = [doc_y + doc_h*0.18, doc_y + doc_h*0.32,
                           doc_y + doc_h*0.46, doc_y + doc_h*0.60]
        line_widths = [0.85, 0.78, 0.85, 0.45]

        thin = QPen(p.pen()); thin.setWidthF(0.9); p.setPen(thin)
        for ly, lw in zip(line_y_positions, line_widths):
            line_start = doc_x + doc_w * 0.08
            line_end = doc_x + doc_w * lw
            p.drawLine(QPointF(line_start, ly), QPointF(line_end, ly))

        # Corner fold (decorative document corner)
        fold_size = w * 0.12
        fold_path = QPainterPath()
        fold_path.moveTo(doc_x + doc_w, doc_y)
        fold_path.lineTo(doc_x + doc_w - fold_size, doc_y)
        fold_path.lineTo(doc_x + doc_w, doc_y + fold_size)
        fold_path.closeSubpath()
        p.setBrush(QBrush(self._fg))
        p.setPen(Qt.NoPen)
        p.drawPath(fold_path)


# ── Step card ──────────────────────────────────────────────────────────────

class StepCard(QFrame):
    clicked = Signal(int)

    def __init__(self, index: int, text: str):
        super().__init__()
        self.index = index
        self._state = 'locked'
        self.setFixedHeight(62)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("stepCard")
        self.setProperty("state", "locked")

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 0, 10, 0)
        row.setSpacing(10)

        self.badge = StepIconWidget(index, size=40)
        self.label = QLabel(text)
        self.label.setObjectName("stepLabel")
        self.label.setFont(QFont("Segoe UI", 9))
        self.label.setWordWrap(True)

        row.addWidget(self.badge)
        row.addWidget(self.label, 1)

    def set_text(self, text: str):
        self.label.setText(text)

    def get_state(self) -> str:
        return self._state

    def apply_style(self, state: str, badge_fg: str, badge_bg: str):
        self._state = state
        self.setProperty("state", state)
        self.label.setProperty("state", state)
        self.badge.set_completed(state == 'completed')
        self.badge.set_colors(badge_fg, badge_bg)
        for w in (self, self.label):
            w.style().unpolish(w)
            w.style().polish(w)
        self.update()

    def mousePressEvent(self, event):
        if self._state != 'locked' and event.button() == Qt.LeftButton:
            self.clicked.emit(self.index)
        super().mousePressEvent(event)


# ── Steps panel ────────────────────────────────────────────────────────────

_STEP_KEYS = [
    'step_data_load',
    'step_preprocessing',
    'step_linear_analysis',
    'step_parameter_estimation',
    'step_phase_space',
    'step_chaos_analysis',
    'step_results',
]


class StepsPanel(QWidget):
    step_selected = Signal(int)

    def __init__(self, translation_manager, theme_manager=None):
        super().__init__()
        self.tm = translation_manager
        self.theme_manager = theme_manager
        self.completed_steps: set = set()
        self._current_index = -1
        # (key, unlocked)
        self.steps = [(k, i == 0) for i, k in enumerate(_STEP_KEYS)]
        self._init_ui()
        self._apply_stylesheet()
        self._select_card(0)

    # ── UI construction ───────────────────────────────────────────────────

    def _init_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("stepsHeader")
        header.setFixedHeight(52)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(14, 0, 14, 0)
        hl.setSpacing(8)
        self._hicon = QLabel('◈')
        self._hicon.setObjectName("headerIcon")
        self._hicon.setFont(QFont("Segoe UI Symbol", 13))
        self.title_label = QLabel(self.tm('panel_steps'))
        self.title_label.setObjectName("stepsTitle")
        tf = QFont("Segoe UI", 10); tf.setBold(True)
        self.title_label.setFont(tf)
        hl.addWidget(self._hicon)
        hl.addWidget(self.title_label, 1)
        outer.addWidget(header)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setObjectName("stepsScroll")

        container = QWidget()
        container.setObjectName("stepsContainer")
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(8, 12, 8, 12)
        vbox.setSpacing(0)

        self.cards: list[StepCard] = []
        for i, (key, unlocked) in enumerate(self.steps):
            card = StepCard(i, self.tm(key))
            card.clicked.connect(self._on_card_clicked)
            self.cards.append(card)
            vbox.addWidget(card)
            if i < len(self.steps) - 1:
                dot = QLabel('│')
                dot.setObjectName("connectorDot")
                dot.setAlignment(Qt.AlignHCenter)
                dot.setFixedHeight(14)
                vbox.addWidget(dot)

        vbox.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll, 1)

        # Status bar
        self.status_label = QLabel(self.tm('status_locked'))
        self.status_label.setObjectName("stepsStatus")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFixedHeight(28)
        outer.addWidget(self.status_label)

    # ── Theme ─────────────────────────────────────────────────────────────

    def _get_colors(self) -> dict:
        name = self.theme_manager.current_theme if self.theme_manager else 'dark'
        if name == 'scientific':
            return dict(
                panel_bg='#1a2e30', header_bg='#213a3d', header_border='#2a4649',
                title_color='#d4e4e5', title_icon='#3d8a90', scroll_bg='#1a2e30',
                card_default='#1f3638', card_locked='#182a2c',
                card_active='#1c4246', card_completed='#1c3a2c',
                border_active='#3d8a90', border_comp='#3d7a50',
                badge_default='#2a4649', badge_fg_default='#7aaeb2',
                badge_locked='#1a2e30', badge_fg_locked='#364e52',
                badge_active='#3d8a90', badge_fg_active='#e8f4f5',
                badge_comp='#3d7050', badge_fg_comp='#d8f0e0',
                label_default='#a8c8cc', label_locked='#364e52', label_active='#d4e4e5',
                dot_color='#2a4649', status_bg='#192a2c',
                status_border='#2a4649', status_color='#5a8a8e',
            )
        elif name == 'high_contrast':
            return dict(
                panel_bg='#000000', header_bg='#0a0a0a', header_border='#ffffff',
                title_color='#ffffff', title_icon='#00ff00', scroll_bg='#000000',
                card_default='#1a1a1a', card_locked='#080808',
                card_active='#002800', card_completed='#001a00',
                border_active='#00ff00', border_comp='#00aa00',
                badge_default='#2a2a2a', badge_fg_default='#cccccc',
                badge_locked='#111111', badge_fg_locked='#444444',
                badge_active='#00ff00', badge_fg_active='#000000',
                badge_comp='#00aa00', badge_fg_comp='#000000',
                label_default='#dddddd', label_locked='#444444', label_active='#00ff00',
                dot_color='#333333', status_bg='#000000',
                status_border='#555555', status_color='#aaaaaa',
            )
        else:  # dark
            return dict(
                panel_bg='#1e1e1e', header_bg='#252525', header_border='#3f3f3f',
                title_color='#d4d4d4', title_icon='#569cd6', scroll_bg='#1e1e1e',
                card_default='#272727', card_locked='#1e1e1e',
                card_active='#193354', card_completed='#1c3020',
                border_active='#4d8cc4', border_comp='#4a9a4a',
                badge_default='#333333', badge_fg_default='#808080',
                badge_locked='#242424', badge_fg_locked='#424242',
                badge_active='#0e639c', badge_fg_active='#ffffff',
                badge_comp='#3a7a3a', badge_fg_comp='#ffffff',
                label_default='#b0b0b0', label_locked='#424242', label_active='#e0e0e0',
                dot_color='#3a3a3a', status_bg='#1a1a1a',
                status_border='#3a3a3a', status_color='#606060',
            )

    def _badge_colors(self, state: str) -> tuple:
        c = self._get_colors()
        return {
            'active':    (c['badge_fg_active'],  c['badge_active']),
            'completed': (c['badge_fg_comp'],     c['badge_comp']),
            'locked':    (c['badge_fg_locked'],   c['badge_locked']),
            'unlocked':  (c['badge_fg_default'],  c['badge_default']),
        }.get(state, (c['badge_fg_default'], c['badge_default']))

    def _apply_stylesheet(self):
        c = self._get_colors()
        self.setStyleSheet(f"""
            StepsPanel {{ background-color: {c['panel_bg']}; }}

            QFrame#stepsHeader {{
                background-color: {c['header_bg']};
                border-bottom: 1px solid {c['header_border']};
            }}
            QLabel#headerIcon {{ background-color: transparent; color: {c['title_icon']}; }}
            QLabel#stepsTitle {{ background-color: transparent; color: {c['title_color']}; }}

            QScrollArea#stepsScroll, QWidget#stepsContainer {{
                background-color: {c['scroll_bg']};
            }}

            QFrame#stepCard {{
                background-color: {c['card_default']};
                border: 1px solid transparent;
                border-radius: 6px;
            }}
            QFrame#stepCard[state="locked"] {{
                background-color: {c['card_locked']};
                border: 1px solid transparent; border-radius: 6px;
            }}
            QFrame#stepCard[state="unlocked"] {{
                background-color: {c['card_default']};
                border: 1px solid transparent; border-radius: 6px;
            }}
            QFrame#stepCard[state="active"] {{
                background-color: {c['card_active']};
                border: 1px solid {c['border_active']}; border-radius: 6px;
            }}
            QFrame#stepCard[state="completed"] {{
                background-color: {c['card_completed']};
                border: 1px solid {c['border_comp']}; border-radius: 6px;
            }}

            QLabel#stepLabel {{ background-color: transparent; color: {c['label_default']}; }}
            QLabel#stepLabel[state="locked"]    {{ color: {c['label_locked']}; }}
            QLabel#stepLabel[state="unlocked"]  {{ color: {c['label_default']}; }}
            QLabel#stepLabel[state="active"]    {{ color: {c['label_active']}; font-weight: bold; }}
            QLabel#stepLabel[state="completed"] {{ color: {c['label_default']}; }}

            QLabel#connectorDot {{
                background-color: transparent;
                color: {c['dot_color']}; font-size: 10pt;
            }}
            QLabel#stepsStatus {{
                background-color: {c['status_bg']};
                color: {c['status_color']};
                border-top: 1px solid {c['status_border']};
                font-size: 8pt; letter-spacing: 0.5px;
            }}
        """)

    def _restyle_all(self):
        for card in self.cards:
            fg, bg = self._badge_colors(card.get_state())
            card.apply_style(card.get_state(), fg, bg)

    # ── Internal logic ────────────────────────────────────────────────────

    def _on_card_clicked(self, index: int):
        self._select_card(index)
        self.step_selected.emit(index)
        try:
            mw = self.window()
            if hasattr(mw, 'content_panel'):
                mw.content_panel.set_step(index)
        except Exception:
            pass

    def _select_card(self, index: int):
        for i, card in enumerate(self.cards):
            if i == index:
                state = 'active'
            elif i in self.completed_steps:
                state = 'completed'
            else:
                state = 'unlocked' if self.steps[i][1] else 'locked'
            fg, bg = self._badge_colors(state)
            card.apply_style(state, fg, bg)
        self._current_index = index
        self._update_status(index)

    def _update_status(self, index: int):
        if index in self.completed_steps:
            self.status_label.setText(self.tm('status_completed'))
        elif 0 <= index < len(self.steps) and self.steps[index][1]:
            self.status_label.setText(self.tm('status_unlocked'))
        else:
            self.status_label.setText(self.tm('status_locked'))

    # ── Public API ────────────────────────────────────────────────────────

    def on_step_selected(self, index: int):
        if index >= 0:
            self._on_card_clicked(index)

    def update_status(self, index: int):
        self._update_status(index)

    def unlock_step(self, index: int):
        if 0 <= index < len(self.steps):
            key, _ = self.steps[index]
            self.steps[index] = (key, True)
            if self.cards[index].get_state() == 'locked':
                fg, bg = self._badge_colors('unlocked')
                self.cards[index].apply_style('unlocked', fg, bg)

    def mark_step_completed(self, index: int):
        if 0 <= index < len(self.steps):
            self.completed_steps.add(index)
            if self.cards[index].get_state() != 'active':
                fg, bg = self._badge_colors('completed')
                self.cards[index].apply_style('completed', fg, bg)

    def lock_step(self, index: int):
        if 0 <= index < len(self.steps):
            key, _ = self.steps[index]
            self.steps[index] = (key, False)
            if self.cards[index].get_state() != 'active':
                fg, bg = self._badge_colors('locked')
                self.cards[index].apply_style('locked', fg, bg)

    def apply_theme(self, theme_name: str = None):
        self._apply_stylesheet()
        self._restyle_all()

    def refresh_ui(self):
        self.title_label.setText(self.tm('panel_steps'))
        for i, (key, _) in enumerate(self.steps):
            self.cards[i].set_text(self.tm(key))
        self._update_status(self._current_index)
        self._apply_stylesheet()
        self._restyle_all()
