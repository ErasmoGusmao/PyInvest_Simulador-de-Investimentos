"""
PyInvest - Worker para execução em background
Executa simulações Monte Carlo sem travar a interface.
"""

from PySide6.QtCore import QObject, Signal, QRunnable, Slot
from core.calculation import SimulationParameters, SimulationResult, run_full_simulation


class SimulationSignals(QObject):
    """Sinais para comunicação entre worker e main thread."""
    started = Signal()
    finished = Signal(object)  # SimulationResult
    error = Signal(str)
    progress = Signal(int)  # Percentual de progresso


class SimulationWorker(QRunnable):
    """
    Worker para executar simulação em thread separada.
    Usa QRunnable para ser executado pelo QThreadPool.
    """
    
    def __init__(self, params: SimulationParameters):
        super().__init__()
        self.params = params
        self.signals = SimulationSignals()
        self._is_cancelled = False
    
    def cancel(self):
        """Cancela a execução."""
        self._is_cancelled = True
    
    @Slot()
    def run(self):
        """Executa a simulação."""
        try:
            self.signals.started.emit()
            
            if self._is_cancelled:
                return
            
            # Executar simulação completa
            result = run_full_simulation(self.params)
            
            if self._is_cancelled:
                return
            
            self.signals.finished.emit(result)
            
        except Exception as e:
            self.signals.error.emit(str(e))
