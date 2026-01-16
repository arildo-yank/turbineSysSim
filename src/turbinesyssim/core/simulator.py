"""
SIMULATOR.PY - High Performance Version
---------------------------------------
The Orchestrator / Governor System.
Gerencia o tempo, a física do motor e a telemetria da interface.
"""

import time
import math
import threading
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QMutex

# Importação robusta da Engine Física e Acústica
try:
    from .engine import EngineState, GasTurbineEngine
except ImportError:
    from dataclasses import dataclass


    @dataclass
    class EngineState:
        time: float = 0.0;
        rpm: float = 0.0;
        load_mw: float = 0.0;
        phase: str = "OFF"
        vibration: float = 0.0;
        fuel_flow: float = 0.0;
        t_combustor_out: float = 0.0
        t_exhaust: float = 0.0;
        efficiency: float = 0.0;
        noise_level_db: float = 0.0


    class GasTurbineEngine:
        def __init__(self): self.rpm = 0.0; self.is_tripped = False; self.trip_reason = ""

        def set_command(self, **kwargs): pass

        def update(self, dt): return EngineState(rpm=self.rpm)

try:
    from ..acoustics.noise_model import TurbineNoiseModel, NoiseInputs
except ImportError:
    class NoiseInputs:
        pass


    class TurbineNoiseModel:
        def __init__(self, i): pass

        def run(self):
            class R: overall_spl_db = 0.0

            return R()


class TurbineSimulator(QObject):
    data_updated = pyqtSignal(object)
    alarm_triggered = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.mutex = QMutex()
        self.running = False

        # Sistemas Core
        self.phys_engine = GasTurbineEngine()
        self.noise_model = TurbineNoiseModel(None)

        # Comandos e Estado
        self.command_load = 0.0
        self.command_starter = False
        self.auto_mode = False
        self.manual_fuel = 0.0

        # Variáveis de Controle PID (Amortecido)
        self.pid_integral = 0.0
        self.last_error = 0.0
        self.critical_speeds = [1250, 2400]

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

    def set_controls(self, load_mw=None, starter=None, auto=None):
        self.mutex.lock()
        if load_mw is not None: self.command_load = float(load_mw)
        if starter is not None: self.command_starter = bool(starter)
        if auto is not None: self.auto_mode = bool(auto)
        self.mutex.unlock()

    def _run_loop(self):
        """Loop de alta precisão (60Hz)"""
        last_t = time.perf_counter()

        while self.running:
            now = time.perf_counter()
            dt = min(now - last_t, 0.05)  # Delta time estável
            last_t = now

            self.mutex.lock()
            # 1. GOVERNADOR (Cálculo da Válvula de Combustível)
            target_fuel = self._governor_logic(dt)

            # 2. FÍSICA (Aplicação de Torque e Inércia)
            self.phys_engine.set_command(
                fuel=target_fuel,
                load=self.command_load,
                starter=self.command_starter,
                igv=34.0
            )
            state = self.phys_engine.update(dt)

            # 3. TURBO VISUAL (Sincronizado com a Carga)
            if self.command_load > 0.1 and state.rpm > 3000:
                # O RPM Visual sobe para dar realismo ao giro das pás
                state.rpm += (self.command_load * 85.0)

                # 4. ANÁLISE DE VIBRAÇÃO E ACÚSTICA
            state = self._process_environmental(state, dt)
            self.mutex.unlock()

            # 5. EMISSÃO DE TELEMETRIA
            self.data_updated.emit(state)

            if hasattr(self.phys_engine, 'is_tripped') and self.phys_engine.is_tripped:
                self.alarm_triggered.emit(self.phys_engine.trip_reason)
                self.running = False

            time.sleep(0.016)

    def _governor_logic(self, dt):
        """Lógica de controle PID Industrial"""
        if not self.auto_mode: return self.manual_fuel

        curr_rpm = self.phys_engine.rpm
        # Alvo dinâmico para compensar a queda de rotação por carga (Droop Control)
        setpoint = 3600.0 + (self.command_load * 5.0)

        error = setpoint - curr_rpm

        # PID Constants amaciadas para turbinas pesadas
        kp, ki, kd = 0.012, 0.006, 0.002

        self.pid_integral = np.clip(self.pid_integral + error * dt, -10, 10)
        derivative = (error - self.last_error) / dt
        self.last_error = error

        # Feed-forward: Antecipa o combustível necessário para a carga solicitada
        ff_load = (self.command_load / 100.0) * 0.75

        output = 0.28 + ff_load + (error * kp) + (self.pid_integral * ki) + (derivative * kd)
        return np.clip(output, 0.0, 1.0)

    def _process_environmental(self, state, dt):
        """Cálculos de efeitos secundários (Vibração/Som)"""
        # Vibração Dinâmica
        vib_base = (state.rpm / 3600.0) * 0.5
        # Ressonância em velocidades críticas
        mag = 0.0
        for crit in self.critical_speeds:
            if abs(state.rpm - crit) < 200:
                mag += 4.0 * math.exp(-((state.rpm - crit) ** 2) / 5000)

        state.vibration = vib_base + mag + (self.command_load * 0.05)

        # Processamento Acústico
        try:
            self.noise_model.inputs = NoiseInputs(
                rpm=state.rpm, load_factor=self.command_load / 100.0,
                fouling_index=0, imbalance_level=state.vibration / 10.0
            )
            state.noise_level_db = self.noise_model.run().overall_spl_db
        except:
            pass

        return state