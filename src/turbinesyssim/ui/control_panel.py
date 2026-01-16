"""
CONTROL_PANEL.PY
----------------
Interactive Control Deck for the Operator.
Fully aligned with the Heavy-Duty Industrial Styling (styles.py).
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QSlider,
    QLabel, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

# --- IMPORTANTE: Conectando ao "Cérebro de Estilo" ---
from .styles import (
    BTN_INDUSTRIAL_START,
    BTN_INDUSTRIAL_STOP,
    SLIDER_INDUSTRIAL,
    COLOR_PANEL_DARK,
    COLOR_TEXT_VALUE  # Azul VFD
)


class ControlPanel(QWidget):
    # Sinais para comunicação com o simulador
    sig_start_sequence = pyqtSignal()
    sig_stop_sequence = pyqtSignal()
    sig_load_change = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        # 1. Fundo do Painel (Escuro e com bordas arredondadas)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLOR_PANEL_DARK};
                border-radius: 6px;
                border: 1px solid #333;
            }}
        """)

        # Layout Principal Horizontal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)  # Margens internas confortáveis
        layout.setSpacing(30)  # Espaço entre os grupos

        # --- SEÇÃO 1: CONTROLE DE SEQUÊNCIA (Botões) ---

        # Botão Start (Verde Industrial com Gradiente)
        self.btn_start = QPushButton("AUTO START")
        self.btn_start.setFixedSize(140, 50)  # Tamanho tátil
        self.btn_start.setStyleSheet(BTN_INDUSTRIAL_START)
        self.btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_start.setToolTip("Initiate Automatic Start-up Sequence")
        self.btn_start.clicked.connect(self.sig_start_sequence.emit)

        # Botão Stop (Vermelho Industrial com Gradiente)
        self.btn_stop = QPushButton("NORMAL STOP")
        self.btn_stop.setFixedSize(140, 50)
        self.btn_stop.setStyleSheet(BTN_INDUSTRIAL_STOP)
        self.btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_stop.setToolTip("Initiate Normal Shutdown Sequence")
        self.btn_stop.clicked.connect(self.sig_stop_sequence.emit)

        layout.addWidget(self.btn_start)
        layout.addWidget(self.btn_stop)

        # --- DIVISOR FÍSICO (Linha Vertical) ---
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)  # Efeito de entalhe
        line.setStyleSheet("background-color: #444; margin-top: 5px; margin-bottom: 5px;")
        line.setFixedWidth(2)
        layout.addWidget(line)

        # --- SEÇÃO 2: CONTROLE DE CARGA (Slider) ---

        load_layout = QHBoxLayout()
        load_layout.setSpacing(15)

        # Rótulo Descritivo
        lbl_load_title = QLabel("GENERATOR LOAD SETPOINT:")
        # Fonte Segoe UI para legibilidade, cor cinza clara
        lbl_load_title.setStyleSheet(
            "color: #aaa; font-weight: bold; font-family: 'Segoe UI'; font-size: 10pt; border: none;")

        # Slider Industrial (Grosso)
        self.slider_load = QSlider(Qt.Orientation.Horizontal)
        self.slider_load.setRange(0, 100)
        self.slider_load.setValue(0)
        self.slider_load.setStyleSheet(SLIDER_INDUSTRIAL)  # Aplica o estilo do styles.py
        self.slider_load.setMinimumWidth(350)  # Largo para precisão
        self.slider_load.setCursor(Qt.CursorShape.PointingHandCursor)

        # Valor Digital (Azul VFD Brilhante)
        self.lbl_load_val = QLabel("0 MW")
        self.lbl_load_val.setStyleSheet(f"""
            color: {COLOR_TEXT_VALUE}; 
            font-weight: bold; 
            font-size: 18pt; 
            font-family: 'Consolas';
            min-width: 90px;
            border: none;
        """)
        self.lbl_load_val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Conectar lógica
        self.slider_load.valueChanged.connect(self._on_slider_change)

        # Montar grupo de carga
        load_layout.addWidget(lbl_load_title)
        load_layout.addWidget(self.slider_load)
        load_layout.addWidget(self.lbl_load_val)

        layout.addLayout(load_layout)

        # Empurrar tudo para a esquerda
        layout.addStretch()

    def _on_slider_change(self, val):
        self.lbl_load_val.setText(f"{val} MW")
        self.sig_load_change.emit(float(val))