from datetime import datetime
from src.utils.enums import EstadoEquipo
from src.interfaces.estrategias import IEstrategiaDesgaste

class Equipo:
    def __init__(self, id_activo: str, modelo: str, fecha_compra: str, estrategia: IEstrategiaDesgaste):
        """
        Constructor que implementa el Patrón Strategy (Hito 3).
        Recibe una instancia de la estrategia de desgaste.
        """
        self.id_activo = id_activo
        self.modelo = modelo
        self.fecha_compra = fecha_compra
        self.estado = EstadoEquipo.OPERATIVO
        self.historial_incidencias = []
        
        # Guardamos la estrategia inyectada
        self.estrategia_desgaste = estrategia

    def calcular_obsolescencia(self) -> float:
        """
        Delega el cálculo a la estrategia asignada.
        """
        if not self.estrategia_desgaste:
            return 0.0
        return self.estrategia_desgaste.calcular(self.fecha_compra)

    def cambiar_estrategia(self, nueva_estrategia: IEstrategiaDesgaste):
        """
        Permite cambiar la lógica de cálculo en tiempo de ejecución.
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