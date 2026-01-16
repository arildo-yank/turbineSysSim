#!/usr/bin/env python3
"""
MAIN.PY
-------
Entry Point do Sistema TITRAGO.
Configura o ambiente, o OpenGL e inicia a interface "Mission Control".
"""

import sys
import traceback
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QSurfaceFormat, QIcon

# --- 1. CONFIGURAÇÃO DE PATH (CRÍTICO) ---
# Garante que o Python encontre a pasta 'src'
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
    print(f"DEBUG: Root configurado em: {SRC_PATH}")

# --- 2. IMPORTS SEGUROS ---
try:
    from turbinesyssim.core.simulator import TurbineSimulator
    from turbinesyssim.ui.main_window import MainWindow
except ImportError as e:
    print("\n❌ ERRO CRÍTICO DE IMPORTAÇÃO:")
    print(f"Detalhe: {e}")
    print("Verifique se a estrutura de pastas está correta (src/turbinesyssim/...).")
    sys.exit(1)


def configure_opengl():
    """
    Configura o Contexto OpenGL.
    NOTA: Mantemos 2.1 Compatibility para suportar 'gluCylinder' e 'glBegin' no macOS.
    Se mudar para Core Profile (3.3+), a visualização 3D precisará ser reescrita do zero.
    """
    fmt = QSurfaceFormat()
    fmt.setDepthBufferSize(24)
    fmt.setStencilBufferSize(8)

    # --- MODO LEGACY (Compatível com seu código atual) ---
    fmt.setVersion(2, 1)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CompatibilityProfile)

    # --- MODO MODERNO (Descomente APENAS se reescrever o opengl_view.py) ---
    # fmt.setVersion(3, 3)
    # fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)

    fmt.setSwapInterval(1)  # VSync (Evita tearing)
    fmt.setSamples(4)  # Anti-aliasing (Suaviza bordas)

    QSurfaceFormat.setDefaultFormat(fmt)


def main():
    # 1. Configura Gráficos
    configure_opengl()

    # 2. Inicia Aplicação
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Estilo Dark/Moderno padrão do Qt
    app.setApplicationName("TITRAGO Turbine Simulator")
    app.setApplicationVersion("3.1")

    print("\n--- INICIANDO TITRAGO MISSION CONTROL V3.1 ---")

    # 3. Inicializa o Cérebro (Simulador)
    try:
        simulator = TurbineSimulator()
        print("✅ Simulador: Online")
    except Exception:
        print("❌ ERRO: Falha ao iniciar Simulador.")
        traceback.print_exc()
        return

    # 4. Inicializa a Interface (Mission Control)
    try:
        window = MainWindow(simulator)
        window.show()
        print("✅ Interface Gráfica: Carregada")
    except Exception:
        print("❌ ERRO: Falha ao abrir Janela Principal.")
        traceback.print_exc()
        return

    # 5. Loop Principal
    print("🚀 Sistema rodando...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()