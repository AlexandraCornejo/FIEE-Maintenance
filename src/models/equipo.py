from abc import ABC, abstractmethod
from datetime import datetime
from src.utils.enums import EstadoEquipo

class Equipo(ABC):
    def __init__(self, id_activo: str, modelo: str, fecha_compra: str):
        self._id_activo = id_activo
        self.modelo = modelo
        self.fecha_compra = fecha_compra
        self.estado = EstadoEquipo.OPERATIVO
        self.historial_incidencias = []
    
    def registrar_incidencia(self, descripcion: str, reportado_por: str):
        self.estado = EstadoEquipo.REPORTADO_CON_FALLA
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ticket = {
            "fecha": fecha,
            "usuario": reportado_por,
            "descripcion": descripcion
        }
        self.historial_incidencias.append(ticket)
        print(f"⚠️ [ALERTA] {self.modelo} cambio a estado: {self.estado.value}")

    @abstractmethod
    def calcular_obsolescencia(self) -> float:
        pass
    
    def to_dict(self):
        """Convierte el objeto a diccionario para Supabase"""
        return {
            "id": self._id_activo,
            "modelo": self.modelo,
            "fecha_compra": self.fecha_compra,
            "estado": self.estado.value,
            "tipo": self.__class__.__name__
        }
    