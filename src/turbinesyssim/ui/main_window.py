"""
MAIN_WINDOW.PY
--------------
"Mission Control" Interface v3.3 (High-Performance).
FIX: Throttled Plot Updates to prevent UI freezing.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QGridLayout, QFrame, QSizePolicy, QCheckBox,
    QSplitter, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSlot, QTimer
from PyQt6.QtGui import QFont

from ..core.engine import EngineState
from ..core.simulator import TurbineSimulator
from .opengl_view import TurbineOpenGLView
from .control_panel import ControlPanel
from .scope_widget import Oscilloscope
from .plots import PerformancePlots

# --- ESTILOS INDUSTRIAIS ---
from .styles import (
    MAIN_WINDOW_STYLE,
    DIGITAL_READOUT_FRAME,
    DIGITAL_READOUT_VALUE,
    DIGITAL_READOUT_TITLE,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, COLOR_ACCENT
)

FONT_MONO = "Consolas"


class IndustrialGauge(QFrame):
    """Gauge Digital Otimizado"""

    def __init__(self, title, unit="", fmt="{:.1f}"):
        super().__init__()
        self.setStyleSheet(DIGITAL_READOUT_FRAME)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.fmt = fmt

        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(DIGITAL_READOUT_TITLE)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_value = QLabel("---")
        self.lbl_value.setStyleSheet(DIGITAL_READOUT_VALUE)
        self.lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_unit = QLabel(unit)
        lbl_unit.setStyleSheet("color: #666; font-size: 8pt; font-weight: bold;")
        lbl_unit.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addWidget(lbl_title)
        layout.addWidget(self.lbl_value)
        layout.addWidget(lbl_unit)
        self.setLayout(layout)

    def update_value(self, val):
        self.lbl_value.setText(self.fmt.format(val))


class StatusHeader(QFrame):
    """Header Fixo"""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #121212; border-bottom: 2px solid #333;")
        self.setFixedHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        self.lbl_status = QLabel("SYSTEM READY")
        self.lbl_status.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_status.setStyleSheet(f"color: {COLOR_ACCENT};")

        self.lbl_time = QLabel("T+ 00:00")
        self.lbl_time.setFont(QFont(FONT_MONO, 12))
        self.lbl_time.setStyleSheet("color: #fff;")

        layout.addWidget(self.lbl_status)
        layout.addStretch()
        layout.addWidget(QLabel("MISSION CLOCK:"))
        layout.addWidget(self.lbl_time)

    def set_status(self, text, color):
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"color: {color};")


class MainWindow(QMainWindow):
    def __init__(self, simulator: TurbineSimulator):
        super().__init__()
        self.sim = simulator
        self.setWindowTitle("SILICONERA-TURBINE SIM v3.3 ")
        self.resize(1600, 950)
        self.setStyleSheet(MAIN_WINDOW_STYLE)

        # Contador para otimização de renderização
        self.render_counter = 0

        self.setup_ui()

        # Conectar Sinais
        self.sim.data_updated.connect(self.update_telemetry)
        self.sim.alarm_triggered.connect(self.handle_alarm)

        # Performance Monitoring do 3D
        if hasattr(self.gl_view, "performanceUpdated"):
            self.gl_view.performanceUpdated.connect(self.update_status_bar)

        # Auto-start Simulator Loop se não estiver rodando
        if not self.sim.running:
            self.sim.start()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 1. HEADER
        self.header = StatusHeader()
        main_layout.addWidget(self.header)

        # 2. SPLITTER
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #333; }")

        # --- PAINEL ESQUERDO: 3D ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.chk_cutaway = QCheckBox("INTERNAL VIEW")
        self.chk_cutaway.setStyleSheet("color: #fff; font-weight: bold; padding: 10px;")
        self.chk_cutaway.setChecked(True)
        self.chk_cutaway.toggled.connect(self.toggle_cutaway)
        left_layout.addWidget(self.chk_cutaway)

        self.gl_view = TurbineOpenGLView()
        self.gl_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(self.gl_view)

        self.splitter.addWidget(left_container)

        # --- PAINEL DIREITO: INSTRUMENTOS ---
        right_container = QWidget()
        right_container.setStyleSheet("background-color: #1e1e1e;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)

        # A. OSCILOSCÓPIO
        lbl_scope = QLabel("GENERATOR OUTPUT (3Ø WAVEFORM)")
        lbl_scope.setStyleSheet("background: #252525; color: #888; font-weight: bold; padding: 4px;")
        lbl_scope.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(lbl_scope)

        self.scope = Oscilloscope()
        self.scope.setMinimumHeight(200)
        right_layout.addWidget(self.scope)

        # B. TABS
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; background: #222; }
            QTabBar::tab { background: #2c2c2c; color: #888; padding: 8px 25px; }
            QTabBar::tab:selected { background: #383838; color: #00e5ff; border-bottom: 2px solid #00e5ff; }
        """)

        # ABA 1: TELEMETRY
        tab_gauges = QWidget()
        layout_gauges = QGridLayout(tab_gauges)
        layout_gauges.setSpacing(10)

        self.gauges = {
            'rpm': IndustrialGauge("ROTOR SPEED", "RPM", "{:.0f}"),
            'load': IndustrialGauge("GENERATOR LOAD", "MW", "{:.1f}"),
            'tit': IndustrialGauge("TURBINE INLET", "K", "{:.0f}"),
            'exh': IndustrialGauge("EXHAUST TEMP", "K", "{:.0f}"),
            'vib': IndustrialGauge("VIBRATION", "mm/s", "{:.2f}"),
            'fuel': IndustrialGauge("FUEL FLOW", "kg/s", "{:.2f}")
        }

        layout_gauges.addWidget(self.gauges['rpm'], 0, 0)
        layout_gauges.addWidget(self.gauges['load'], 0, 1)
        layout_gauges.addWidget(self.gauges['tit'], 1, 0)
        layout_gauges.addWidget(self.gauges['exh'], 1, 1)
        layout_gauges.addWidget(self.gauges['vib'], 2, 0)
        layout_gauges.addWidget(self.gauges['fuel'], 2, 1)

        layout_gauges.setRowStretch(3, 1)
        self.tabs.addTab(tab_gauges, "LIVE TELEMETRY")

        # ABA 2: TRENDS
        self.plots_widget = PerformancePlots()
        self.tabs.addTab(self.plots_widget, "HISTORICAL TRENDS")

        right_layout.addWidget(self.tabs, stretch=1)
        self.splitter.addWidget(right_container)

        self.splitter.setStretchFactor(0, 60)
        self.splitter.setStretchFactor(1, 40)

        main_layout.addWidget(self.splitter, stretch=1)

        # 3. CONTROLES
        control_frame = QFrame()
        control_frame.setStyleSheet("background-color: #252525; border-top: 1px solid #444;")
        control_layout = QVBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)

        self.controls = ControlPanel()
        control_layout.addWidget(self.controls)

        main_layout.addWidget(control_frame)

        self.controls.sig_start_sequence.connect(self.command_start)
        self.controls.sig_stop_sequence.connect(self.command_stop)
        self.controls.sig_load_change.connect(self.command_load)

    # --- COMANDOS ---
    def toggle_cutaway(self, checked):
        if hasattr(self.gl_view, 'toggle_cutaway'):
            self.gl_view.cutaway_mode = checked
            self.gl_view.update()

    def command_start(self):
        self.sim.set_controls(load_mw=0, starter=True, auto=True)
        self.header.set_status("SEQUENCE: AUTO START INITIATED", "#fff")

    def command_stop(self):
        self.sim.set_controls(load_mw=0, starter=False, auto=False)
        self.sim.set_manual_fuel(0.0)
        self.header.set_status("SEQUENCE: NORMAL STOP INITIATED", "#fff")

    def command_load(self, mw):
        self.sim.set_controls(load_mw=float(mw))

    # --- ATUALIZAÇÃO DA TELA (OTIMIZADO) ---
    @pyqtSlot(object)
    def update_telemetry(self, state):
        try:
            self.render_counter += 1

            # 1. 3D (Alta Prioridade - Todo Frame)
            if hasattr(self.gl_view, 'update_physics'):
                self.gl_view.update_physics(state.rpm)
            elif hasattr(self.gl_view, 'update_rpm'):
                self.gl_view.update_rpm(state.rpm)

            # 2. Scope (Alta Prioridade - Todo Frame)
            self.scope.update_data(state.rpm, state.load_mw)

            # 3. Gauges (Média Prioridade - Todo Frame é leve)
            self.gauges['rpm'].update_value(state.rpm)
            self.gauges['load'].update_value(state.load_mw)
            self.gauges['tit'].update_value(state.t_combustor_out)
            self.gauges['exh'].update_value(state.t_exhaust)
            self.gauges['fuel'].update_value(state.fuel_flow)
            self.gauges['vib'].update_value(state.vibration)

            # 4. PLOTS (BAIXA PRIORIDADE - CORREÇÃO DE TRAVAMENTO)
            # Atualiza apenas a cada 5 frames (~12 FPS se o sim rodar a 60 FPS)
            # Isso libera a CPU para desenhar a turbina sem travar
            if self.render_counter % 5 == 0:
                self.plots_widget.update_data(
                    state.time, state.rpm, state.load_mw,
                    state.t_exhaust, getattr(state, 'efficiency', 0.0)
                )

            # 5. Header
            if self.render_counter % 10 == 0:  # Otimização extra
                status_text = f"STATUS: {state.phase}"
                color = "#888"
                if state.phase == "ON LOAD":
                    color = COLOR_SUCCESS
                elif "TRIP" in state.phase:
                    color = COLOR_DANGER

                self.header.set_status(status_text, color)

                m, s = divmod(int(state.time), 60)
                self.header.lbl_time.setText(f"T+ {m:02d}:{s:02d}")

        except Exception as e:
            print(f"UI Update Error: {e}")

    @pyqtSlot(str)
    def handle_alarm(self, reason):
        self.header.set_status(f"TRIP: {reason}", COLOR_DANGER)

    def update_status_bar(self, fps, mem, part):
        self.statusBar().showMessage(f"3D RENDER: {fps:.0f} FPS | PARTICLES: {part}")