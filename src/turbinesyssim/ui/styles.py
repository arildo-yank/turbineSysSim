"""
STYLES.PY
---------
Central definitions for Industrial HMI Look & Feel (QSS Stylesheets).
Mimics GE Mark VIe / Siemens SPPA-T3000 aesthetics.
This file must NOT import other project modules to avoid circular dependencies.
"""

# --- PALETA DE CORES INDUSTRIAL ---
COLOR_PANEL_BG = "#2b2b2b"       # Fundo cinza chumbo
COLOR_PANEL_DARK = "#1e1e1e"     # Fundo de áreas recuadas (Gauges/Scope)
COLOR_BEZEL_LIGHT = "#444444"    # Borda iluminada (Efeito 3D)
COLOR_BEZEL_DARK = "#111111"     # Borda sombreada (Efeito 3D)

# Cores de Texto
COLOR_TEXT_LABEL = "#aaaaaa"     # Texto de rótulos (Cinza claro)
COLOR_TEXT_VALUE = "#00e5ff"     # Azul VFD (Vacuum Fluorescent Display) - Brilhante

# Cores Semânticas
COLOR_ACCENT = "#007acc"         # Azul Seleção/Destaque
COLOR_SUCCESS = "#4ec9b0"        # Verde Status OK
COLOR_WARNING = "#ce9178"        # Laranja Alerta
COLOR_DANGER = "#ff3333"         # Vermelho Crítico/Trip

# --- ESTILO DA JANELA PRINCIPAL E ABAS ---
MAIN_WINDOW_STYLE = f"""
    QMainWindow {{
        background-color: {COLOR_PANEL_BG};
    }}
    QTabWidget::pane {{
        border: 2px solid {COLOR_BEZEL_DARK};
        background: {COLOR_PANEL_DARK};
        margin-top: -2px;
    }}
    QTabBar::tab {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3d3d3d, stop:1 #2b2b2b);
        color: #aaa;
        padding: 8px 25px;
        border: 1px solid {COLOR_BEZEL_DARK};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        font-weight: bold;
        font-family: 'Segoe UI', sans-serif;
    }}
    QTabBar::tab:selected {{
        background: {COLOR_PANEL_DARK};
        color: #fff;
        border-top: 3px solid {COLOR_ACCENT};
        margin-bottom: -2px;
    }}
    QTabBar::tab:hover {{
        background: #444;
    }}
    QStatusBar {{
        background: #1a1a1a;
        color: #666;
    }}
"""

# --- ESTILO DOS MOSTRADORES DIGITAIS (GAUGES) ---
# Frame externo com efeito de profundidade (Inset)
DIGITAL_READOUT_FRAME = f"""
    QFrame {{
        background-color: {COLOR_PANEL_DARK};
        border-style: inset;
        border-width: 2px;
        border-radius: 4px;
        border-color: {COLOR_BEZEL_DARK} {COLOR_BEZEL_LIGHT} {COLOR_BEZEL_LIGHT} {COLOR_BEZEL_DARK};
    }}
"""

# Valor Numérico (Grande e Brilhante)
# Adicionado 'Menlo' e 'Courier New' para compatibilidade com Mac
DIGITAL_READOUT_VALUE = f"""
    QLabel {{
        color: {COLOR_TEXT_VALUE};
        font-family: 'Menlo', 'Consolas', 'Courier New', monospace;
        font-size: 24pt;
        font-weight: bold;
        padding: 5px;
        border: none;
    }}
"""

# Título do Instrumento (Pequeno e Discreto)
DIGITAL_READOUT_TITLE = f"""
    QLabel {{
        color: {COLOR_TEXT_LABEL};
        font-size: 9pt;
        font-weight: bold;
        text-transform: uppercase;
        border: none;
        font-family: 'Segoe UI', sans-serif;
    }}
"""

# --- ESTILO DOS BOTÕES DE CONTROLE ---

# Botão Start (Verde com Gradiente e Borda)
BTN_INDUSTRIAL_START = """
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2e7d32, stop:1 #1b5e20);
        color: white;
        border: 3px solid #1b5e20;
        border-radius: 6px;
        font-weight: bold;
        font-size: 12pt;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #388e3c, stop:1 #2e7d32);
        border-color: #2e7d32;
    }
    QPushButton:pressed {
        background-color: #1b5e20;
        border-style: inset;
        padding-top: 7px; /* Efeito tátil de afundar */
        padding-left: 7px;
    }
"""

# Botão Stop (Vermelho com Gradiente e Borda)
BTN_INDUSTRIAL_STOP = """
    QPushButton {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #c62828, stop:1 #b71c1c);
        color: white;
        border: 3px solid #b71c1c;
        border-radius: 6px;
        font-weight: bold;
        font-size: 12pt;
        padding: 5px;
    }
    QPushButton:hover {
        background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d32f2f, stop:1 #c62828);
        border-color: #c62828;
    }
    QPushButton:pressed {
        background-color: #b71c1c;
        border-style: inset;
        padding-top: 7px;
    }
"""

# --- ESTILO DO SLIDER INDUSTRIAL ---
SLIDER_INDUSTRIAL = f"""
    QSlider::groove:horizontal {{
        border: 2px solid {COLOR_BEZEL_DARK};
        height: 12px; /* Sulco grosso */
        background: {COLOR_PANEL_DARK};
        margin: 2px 0;
        border-radius: 6px;
    }}
    QSlider::handle:horizontal {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0096c7, stop:1 #007acc);
        border: 2px solid #005f99;
        width: 24px; /* Handle largo para pega fácil */
        margin: -8px 0;
        border-radius: 4px;
    }}
    QSlider::handle:horizontal:hover {{
        background: #00a8e8;
    }}
    QSlider::handle:horizontal:pressed {{
        background: #005f99;
    }}
"""