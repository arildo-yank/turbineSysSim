"""
SCOPE_WIDGET.PY v2.0
--------------------
High-Fidelity Power Analyzer & Oscilloscope.
Features:
- Real-time 3-Phase waveform rendering with CRT glow effect.
- Harmonic distortion simulation (THD) based on Load.
- Vector Phasor Diagram (PiP).
- Automatic Voltage Regulator (AVR) transient simulation (Voltage Sag/Recovery).
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont,
    QPainterPath, QLinearGradient, QRadialGradient
)
import math
import random
import numpy as np

# --- CORES INDUSTRIAIS ---
COLOR_BG = QColor(10, 12, 16)  # Fundo "Dark Matter"
COLOR_GRID = QColor(0, 255, 200, 30)  # Grid Ciano Tecnológico
COLOR_PHASE_A = QColor(255, 60, 60)  # Vermelho
COLOR_PHASE_B = QColor(0, 255, 100)  # Verde
COLOR_PHASE_C = QColor(60, 100, 255)  # Azul


class Oscilloscope(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background-color: {COLOR_BG.name()}; border: 1px solid #333;")
        self.setMinimumHeight(200)

        # Estado do Gerador
        self.rpm = 0.0
        self.load_mw = 0.0
        self.target_voltage = 13800.0  # 13.8 kV
        self.current_voltage = 0.0
        self.phase_offset = 0.0

        # Simulação de Transientes (AVR - Automatic Voltage Regulator)
        self.voltage_sag = 0.0  # Queda temporária de tensão
        self.noise_seed = [random.random() for _ in range(1000)]

        # Timer de Renderização (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(16)

    def update_data(self, rpm, load):
        """Recebe dados da física"""
        # Detectar mudança brusca de carga para criar "Voltage Sag"
        delta_load = load - self.load_mw
        if delta_load > 5.0:  # Se a carga subiu mais de 5MW de repente
            self.voltage_sag += delta_load * 0.02  # Afunda a tensão

        self.rpm = rpm
        self.load_mw = load

    def animate(self):
        """Loop de física interna do osciloscópio (separado da física principal)"""
        # 1. Recuperação do AVR (A tensão tenta voltar ao normal)
        self.voltage_sag *= 0.92  # Decaimento exponencial (recuperação)

        # 2. Rotação de fase baseada na Frequência
        # Freq = RPM * Polos / 120. Assumindo 2 polos -> Hz = RPM / 60
        freq_hz = self.rpm / 60.0
        self.phase_offset -= freq_hz * 0.3  # Velocidade visual

        self.update()  # Força repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Fundo e Grid
        self._draw_background(painter, w, h)

        # Se a turbina estiver parada/lenta, mostra linha reta
        if self.rpm < 100:
            self._draw_dead_signal(painter, w, h)
            return

        # 2. Calcular Parâmetros da Onda
        # Amplitude Visual (Pixels)
        base_amp = h * 0.35
        # Efeito Sag: Tensão cai com carga súbita
        current_amp_factor = 1.0 - min(0.3, self.voltage_sag)
        visual_amp = base_amp * current_amp_factor

        # Distorção Harmônica (THD): Aumenta com a carga
        # Cargas altas sujam a onda (simulação de carga não-linear)
        thd_factor = (self.load_mw / 150.0) * 0.15

        # 3. Desenhar Ondas (Trifásico)
        phases = [
            (COLOR_PHASE_A, 0.0),  # Fase A (0°)
            (COLOR_PHASE_B, 2 * math.pi / 3),  # Fase B (120°)
            (COLOR_PHASE_C, 4 * math.pi / 3)  # Fase C (240°)
        ]

        for color, offset in phases:
            self._draw_wave(painter, w, h, visual_amp, offset, thd_factor, color)

        # 4. Desenhar Diagrama Fasorial (Canto Inferior Direito)
        self._draw_phasor_diagram(painter, w, h, self.phase_offset)

        # 5. Overlay de Dados Digitais (Texto Técnico)
        self._draw_digital_readout(painter, w, h, visual_amp, thd_factor)

    def _draw_background(self, p, w, h):
        # Gradiente sutil de vinheta (CRT look)
        grad = QRadialGradient(w / 2, h / 2, w / 1.5)
        grad.setColorAt(0, COLOR_BG)
        grad.setColorAt(1, QColor(0, 0, 0))
        p.fillRect(0, 0, w, h, QBrush(grad))

        # Grid
        p.setPen(QPen(COLOR_GRID, 1, Qt.PenStyle.DotLine))

        # Linhas Verticais (Tempo)
        step_x = w / 10
        for i in range(11):
            x = i * step_x
            p.drawLine(int(x), 0, int(x), h)

        # Linhas Horizontais (Tensão)
        step_y = h / 8
        for i in range(9):
            y = i * step_y
            p.drawLine(0, int(y), w, int(y))

        # Linha Central (Zero)
        p.setPen(QPen(QColor(0, 255, 200, 80), 1))
        p.drawLine(0, int(h / 2), w, int(h / 2))

    def _draw_dead_signal(self, p, w, h):
        p.setPen(QPen(QColor(0, 255, 0), 2))
        mid = h / 2
        p.drawLine(0, int(mid), w, int(mid))

        p.setPen(QColor(100, 100, 100))
        p.setFont(QFont("Consolas", 12))
        p.drawText(int(w / 2) - 50, int(mid) - 20, "NO SIGNAL")

    def _draw_wave(self, p, w, h, amp, phase_shift, thd, color):
        path = QPainterPath()
        mid_y = h / 2

        # Frequência visual (Quantos ciclos cabem na tela)
        # Mais RPM = Ondas mais "apertadas"
        cycles_on_screen = 2.0 + (self.rpm / 3600.0) * 2.0

        points = []
        resolution = 2  # Pixels por passo (menor = mais suave)

        for x in range(0, w + resolution, resolution):
            t = (x / w) * cycles_on_screen * 2 * math.pi

            # Fundamental
            val = math.sin(t + self.phase_offset + phase_shift)

            # Harmônicas (Sujeira na rede)
            # 3ª Harmônica (f * 3)
            val += math.sin((t + self.phase_offset + phase_shift) * 3) * (thd * 0.5)
            # 5ª Harmônica (f * 5)
            val += math.sin((t + self.phase_offset + phase_shift) * 5) * (thd * 0.2)

            # Ruído Branco (Noise)
            noise_idx = int((x + self.phase_offset * 100) % 999)
            val += (self.noise_seed[noise_idx] - 0.5) * 0.02

            y = mid_y - (val * amp)

            if x == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        # Efeito "Glow" (Neon)
        # Desenhamos a linha duas vezes: uma grossa transparente e uma fina opaca

        # 1. Glow
        glow_color = QColor(color)
        glow_color.setAlpha(60)
        p.setPen(QPen(glow_color, 4))
        p.drawPath(path)

        # 2. Core
        p.setPen(QPen(color, 1.5))
        p.drawPath(path)

    def _draw_phasor_diagram(self, p, w, h, rotation):
        """Diagrama Vetorial no canto da tela (Picture in Picture)"""
        size = 80
        center_x = w - size / 2 - 20
        center_y = h - size / 2 - 20
        radius = size / 2.5

        # Fundo do Fasor
        p.setBrush(QColor(0, 0, 0, 150))
        p.setPen(QPen(QColor(100, 100, 100), 1))
        p.drawEllipse(QPointF(center_x, center_y), radius, radius)

        # Vetores (Giram com a fase)
        # Como o gráfico corre para esquerda, o vetor gira horário visualmente
        offsets = [0, 2 * math.pi / 3, 4 * math.pi / 3]
        colors = [COLOR_PHASE_A, COLOR_PHASE_B, COLOR_PHASE_C]

        for i in range(3):
            angle = rotation + offsets[i]
            # O vetor A deve apontar para onde a onda está no tempo 0
            # Simplificação visual: Apenas girar

            vec_x = center_x + math.cos(angle) * radius
            vec_y = center_y + math.sin(angle) * radius

            p.setPen(QPen(colors[i], 2))
            p.drawLine(QPointF(center_x, center_y), QPointF(vec_x, vec_y))
            # Pequena bolinha na ponta
            p.setBrush(colors[i])
            p.drawEllipse(QPointF(vec_x, vec_y), 2, 2)

    def _draw_digital_readout(self, p, w, h, amp_pixels, thd):
        """Texto técnico sobreposto"""
        p.setFont(QFont("Consolas", 9))

        # Frequência
        freq = self.rpm / 60.0
        p.setPen(QColor(0, 255, 200))
        p.drawText(10, 20, f"FREQ: {freq:.3f} Hz")

        # Tensão Estimada (Baseado na amplitude visual relativa)
        # Assumindo 100 pixels = 10kV
        kv_peak = (amp_pixels / 100.0) * 10.0
        kv_rms = kv_peak * 0.707

        p.drawText(10, 35, f"Vpk : {kv_peak:.2f} kV")
        p.setPen(QColor(255, 255, 0))  # Amarelo para destaque
        p.drawText(10, 50, f"Vrms: {kv_rms:.2f} kV")

        # THD (Distorção Harmônica Total)
        p.setPen(QColor(200, 200, 200))
        p.drawText(10, 75, f"THD : {thd * 100:.1f} %")

        # Power Factor (Simulado)
        # Cargas indutivas industriais abaixam o PF
        pf = 1.0 - (self.load_mw * 0.002)
        pf = max(0.85, pf)
        p.drawText(10, 90, f"PF  : {pf:.2f} Lag")