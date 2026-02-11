import math
from datetime import datetime
# Esta línea es la que ella quiere ver sí o sí
from src.interfaces.estrategias import IEstrategiaDesgaste 

class DesgasteLineal(IEstrategiaDesgaste):
    def calcular(self, fecha_compra: str) -> float:
        anio_compra = int(fecha_compra.split("-")[0])
        anio_actual = datetime.now().year
        t = max(1, anio_actual - anio_compra)
        return round(min(t * 0.05, 1.0), 2)

class DesgasteExponencial(IEstrategiaDesgaste):
    def calcular(self, fecha_compra: str) -> float:
        anio_compra = int(fecha_compra.split("-")[0])
        anio_actual = datetime.now().year
        t = max(1, anio_actual - anio_compra)
        indice = (math.exp(0.2 * t) - 1) / 10
        return round(min(indice, 1.0), 2)