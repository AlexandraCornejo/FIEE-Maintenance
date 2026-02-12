from datetime import datetime
import sys
import os

# Agregamos la ruta raíz para evitar errores de importación
sys.path.append(os.getcwd())

from src.utils.enums import EstadoEquipo

try:
    from src.interfaces.estrategias import IEstrategiaDesgaste
except ImportError:
    IEstrategiaDesgaste = object # Fallback para que no rompa si falla el import

class Equipo:
    def __init__(self, id_activo: str, modelo: str, fecha_compra: str, estrategia):
        """
        Constructor que implementa el Patrón Strategy.
        :param estrategia: Instancia de DesgasteLineal o DesgasteExponencial
        """
        self.id_activo = id_activo
        self.modelo = modelo
        self.fecha_compra = fecha_compra
        self.estado = EstadoEquipo.OPERATIVO
        self.historial_incidencias = []
        
        self.estrategia_desgaste = estrategia

    def calcular_obsolescencia(self) -> float:
        if not hasattr(self, 'estrategia_desgaste') or self.estrategia_desgaste is None:
            return 0.0
        valor_teorico = self.estrategia_desgaste.calcular(self.fecha_compra)
        historial = getattr(self, 'historial_incidencias', [])
        
        if historial: 
            ultimo_ticket = historial[-1]
            dictamen_ia = str(ultimo_ticket.get('dictamen_ia', '')).upper()
            
            if "ALERTA" in dictamen_ia or "CARBONIZADA" in dictamen_ia:
                return 0.98

        return min(valor_teorico, 1.0)

    def cambiar_estrategia(self, nueva_estrategia):
        """
        Permite cambiar la estrategia de cálculo en tiempo de ejecución.
        """
        self.estrategia_desgaste = nueva_estrategia

    def registrar_incidencia(self, descripcion: str):
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.historial_incidencias.append({"fecha": fecha, "detalle": descripcion})

    def to_dict(self):
        return {
            "id": self.id_activo,
            "modelo": self.modelo,
            "fecha_compra": self.fecha_compra,
            "estado": self.estado.value,
            "indice_obsolescencia": self.calcular_obsolescencia(),
            "incidencias": self.historial_incidencias
        }