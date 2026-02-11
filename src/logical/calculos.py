from datetime import datetime
from src.interfaces.estrategias import IEstrategiaDesgaste

class DesgasteLineal(IEstrategiaDesgaste):
    """Estrategia para equipos mecánicos (Motores). Desgaste constante del 5% anual."""
    def calcular(self, fecha_compra: str) -> float:
        anio_actual = datetime.now().year
        anio_compra = int(fecha_compra.split("-")[0])
        anios_uso = anio_actual - anio_compra
        
        # Fórmula: 5% por año, máximo 100%
        desgaste = anios_uso * 0.05
        return min(max(desgaste, 0.0), 1.0)

class DesgasteExponencial(IEstrategiaDesgaste):
    """Estrategia para equipos electrónicos (Osciloscopios). Desgaste acelerado."""
    def calcular(self, fecha_compra: str) -> float:
        anio_actual = datetime.now().year
        anio_compra = int(fecha_compra.split("-")[0])
        anios_uso = anio_actual - anio_compra
        
        # Fórmula: Crecimiento compuesto del 15% anual
        if anios_uso <= 0: return 0.0
        factor = (1.15 ** anios_uso) - 1
        return min(max(factor, 0.0), 1.0)