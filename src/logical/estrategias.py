import math
from datetime import datetime
# Esta es la línea que tu compañera exige para mantener el orden
from src.interfaces.estrategias import IEstrategiaDesgaste 

class DesgasteLineal(IEstrategiaDesgaste):
    """Implementación para equipos físicos"""
    def calcular(self, fecha_compra: str) -> float:
        # Calculamos antigüedad
        anio_compra = int(fecha_compra.split("-")[0])
        anio_actual = datetime.now().year
        t = max(1, anio_actual - anio_compra)
        
        # Desgaste constante del 5% anual
        indice = t * 0.05
        return round(min(indice, 1.0), 2)

class DesgasteExponencial(IEstrategiaDesgaste):
    """Implementación para equipos electrónicos"""
    def calcular(self, fecha_compra: str) -> float:
        # Calculamos antigüedad
        anio_compra = int(fecha_compra.split("-")[0])
        anio_actual = datetime.now().year
        t = max(1, anio_actual - anio_compra)
        
        # El desgaste se acelera con el tiempo
        indice = (math.exp(0.2 * t) - 1) / 10
        return round(min(indice, 1.0), 2)