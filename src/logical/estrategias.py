import math
from abc import ABC, abstractmethod
from datetime import datetime

# Hito 1: Definición de la Interfaz
class EstrategiaDesgaste(ABC):
    @abstractmethod
    def calcular(self, fecha_compra: str) -> float:
        """Método que deben implementar todas las estrategias"""
        pass

    def calcular_antiguedad(self, fecha_compra: str) -> int:
        """Calcula cuántos años han pasado desde la compra"""
        try:
            anio_compra = int(fecha_compra.split("-")[0])
            anio_actual = datetime.now().year
            # Retorna al menos 1 para evitar errores en fórmulas
            return max(1, anio_actual - anio_compra)
        except Exception:
            return 1

# Hito 2: Implementaciones Reales
class DesgasteLineal(EstrategiaDesgaste):
    """Ideal para Equipos Físicos (ej. motores)"""
    def calcular(self, fecha_compra: str) -> float:
        t = self.calcular_antiguedad(fecha_compra)
        # Desgaste constante del 5% anual
        indice = t * 0.05
        return round(min(indice, 1.0), 2)

class DesgasteExponencial(EstrategiaDesgaste):
    """Ideal para Equipos Electrónicos (ej. servidores)"""
    def calcular(self, fecha_compra: str) -> float:
        t = self.calcular_antiguedad(fecha_compra)
        # El desgaste se acelera con el tiempo usando e^x
        indice = (math.exp(0.2 * t) - 1) / 10
        return round(min(indice, 1.0), 2)