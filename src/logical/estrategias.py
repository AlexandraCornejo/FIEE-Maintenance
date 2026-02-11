import math
from datetime import datetime
from src.interfaces.estrategias import IEstrategiaDesgaste 

class DesgasteLineal(IEstrategiaDesgaste):
    """Implementación para equipos físicos (Motores, Maquinaria)"""
    def calcular(self, fecha_compra: str) -> float:
        # 1. Calculamos antigüedad en años
        anio_compra = int(fecha_compra.split("-")[0])
        anio_actual = datetime.now().year
        t = max(1, anio_actual - anio_compra)
        
        # 2. Fórmula: Desgaste constante del 5% anual
        indice = t * 0.05
        return round(min(indice, 1.0), 2)

class DesgasteExponencial(IEstrategiaDesgaste):
    """Implementación para equipos electrónicos (Laptops, Servidores)"""
    def calcular(self, fecha_compra: str) -> float:
        # 1. Calculamos antigüedad en años
        anio_compra = int(fecha_compra.split("-")[0])
        anio_actual = datetime.now().year
        t = max(1, anio_actual - anio_compra)
        
        # 2. Fórmula: El desgaste aumenta más rápido cada año
        indice = (math.exp(0.2 * t) - 1) / 10
        return round(min(indice, 1.0), 2)