from src.models.equipo import Equipo
from src.interfaces.mixins import IdentificableQR, AnalizadorPredictivo, InspectorVisual

# --- FÍSICA ---
class Osciloscopio(Equipo, IdentificableQR, AnalizadorPredictivo, InspectorVisual):
    def __init__(self, id_activo, modelo, fecha, ancho_banda):
        Equipo.__init__(self, id_activo, modelo, fecha)
        IdentificableQR.__init__(self)
        self.ancho_banda = ancho_banda
    
    def calcular_obsolescencia(self) -> float:
        # Lógica dummy: Equipos electrónicos obsoletos a los 5 años
        return 0.2  # 20% de desgaste simulado

# --- ELECTROTECNIA ---
class MotorACTrifasico(Equipo, IdentificableQR):
    def __init__(self, id_activo, modelo, fecha, hp, voltaje):
        Equipo.__init__(self, id_activo, modelo, fecha)
        IdentificableQR.__init__(self)
        self.hp = hp
        self.voltaje = voltaje

    def calcular_obsolescencia(self) -> float:
        # Lógica dummy: Motores duran más
        return 0.05 # 5% de desgaste simulado