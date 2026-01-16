"""
PLOTS.PY
--------
Real-time trend monitoring using PyQtGraph.
Displays historical data for RPM, Load, and Temperature.
"""

import numpy as np
from collections import deque
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
import pyqtgraph as pg

# Configuração Global do PyQtGraph (Estilo Industrial)
pg.setConfigOption('background', '#1e1e1e')
pg.setConfigOption('foreground', '#aaaaaa')
pg.setConfigOption('antialias', True)


class PerformancePlots(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Layout Vertical
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # --- GRÁFICO 1: MECÂNICO (RPM & CARGA) ---
        self.plot_mech = pg.PlotWidget(title="MECHANICAL TRENDS (RPM vs LOAD)")
        self.plot_mech.showGrid(x=True, y=True, alpha=0.3)
        self.plot_mech.setLabel('left', 'RPM', units='rpm')
        self.plot_mech.setLabel('right', 'Load', units='MW')
        self.plot_mech.setLabel('bottom', 'Time', units='s')
        self.plot_mech.addLegend()

        # Eixo Direito para Carga (MW)
        self.p_mech_right = pg.ViewBox()
        self.plot_mech.scene().addItem(self.p_mech_right)
        self.plot_mech.getAxis('right').linkToView(self.p_mech_right)
        self.p_mech_right.setXLink(self.plot_mech)

        # Curvas
        self.curve_rpm = self.plot_mech.plot(pen=pg.mkPen('#00e5ff', width=2), name="Rotor Speed")
        self.curve_load = pg.PlotCurveItem(pen=pg.mkPen('#ffab00', width=2), name="Generator Load")
        self.p_mech_right.addItem(self.curve_load)

        # --- GRÁFICO 2: TÉRMICO (TEMPERATURA) ---
        self.plot_therm = pg.PlotWidget(title="THERMAL TRENDS (EGT)")
        self.plot_therm.showGrid(x=True, y=True, alpha=0.3)
        self.plot_therm.setLabel('left', 'Temperature', units='K')
        self.plot_therm.setLabel('bottom', 'Time', units='s')

        self.curve_egt = self.plot_therm.plot(pen=pg.mkPen('#ff1744', width=2), name="Exhaust Temp")

        # Adiciona ao layout
        layout.addWidget(self.plot_mech)
        layout.addWidget(self.plot_therm)

        # Buffers de Dados (Armazena os últimos 200 pontos)
        self.buffer_size = 200
        self.time_data = deque(maxlen=self.buffer_size)
        self.rpm_data = deque(maxlen=self.buffer_size)
        self.load_data = deque(maxlen=self.buffer_size)
        self.temp_data = deque(maxlen=self.buffer_size)

        # Hook para redimensionar o eixo direito
        self.plot_mech.getViewBox().sigResized.connect(self.update_views)

    def update_views(self):
        """Mantém o eixo direito sincronizado com o esquerdo"""
        self.p_mech_right.setGeometry(self.plot_mech.getViewBox().sceneBoundingRect())
        self.p_mech_right.linkedViewChanged(self.plot_mech.getViewBox(), self.p_mech_right.XAxis)

    def update_data(self, time, rpm, load, temperature, efficiency=0.0):
        """Recebe dados do simulador e atualiza os gráficos"""
        self.time_data.append(time)
        self.rpm_data.append(rpm)
        self.load_data.append(load)
        self.temp_data.append(temperature)

        # Converte para lista para plotar
        t = list(self.time_data)

        # Atualiza curvas
        self.curve_rpm.setData(t, list(self.rpm_data))
        self.curve_load.setData(t, list(self.load_data))
        self.curve_egt.setData(t, list(self.temp_data))

        # Auto-range no eixo direito
        self.p_mech_right.autoRange()


# Classe Dummy para compatibilidade se necessário
class RealTimePlot(PerformancePlots):
    pass