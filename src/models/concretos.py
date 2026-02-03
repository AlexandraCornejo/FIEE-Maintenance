from src.models.equipo import Equipo
from src.interfaces.mixins import IdentificableQR, AnalizadorPredictivo

# --- TIPO 1: ELECTRÓNICA DE LABORATORIO ---
class Osciloscopio(Equipo, IdentificableQR):
    def __init__(self, id_activo, modelo, fecha, ancho_banda):
        super().__init__(id_activo, modelo, fecha)
        self.ancho_banda = ancho_banda
    
    def calcular_obsolescencia(self) -> float:
        # Lógica: 15% de desgaste base
        return 0.15 

# --- TIPO 2: INSTRUMENTACIÓN PORTÁTIL (¡NUEVO!) ---
class Multimetro(Equipo, IdentificableQR):
    def __init__(self, id_activo, modelo, fecha, precision, es_digital: bool):
        super().__init__(id_activo, modelo, fecha)
        self.precision = precision
        self.es_digital = es_digital

    def calcular_obsolescencia(self) -> float:
        # Polimorfismo: Si es digital dura más (10%), si es viejo dura menos (30%)
        return 0.10 if self.es_digital else 0.30

# --- TIPO 3: POTENCIA Y CONTROL ---
class MotorInduccion(Equipo, IdentificableQR, AnalizadorPredictivo):
    def __init__(self, id_activo, modelo, fecha, hp, voltaje, rpm):
        super().__init__(id_activo, modelo, fecha)
        self.hp = hp
        self.voltaje = voltaje
        self.rpm = rpm

    def calcular_obsolescencia(self) -> float:
        # Lógica: Los motores industriales son muy duraderos (5% desgaste)
        return 0.05