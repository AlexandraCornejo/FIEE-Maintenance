from datetime import datetime
from src.utils.enums import EstadoEquipo

class Equipo:
    """
    Hito 3: Clase Contexto del patrón Strategy.
    Ya no es abstracta porque delega el cálculo a una estrategia externa.
    """
    def __init__(self, id_activo: str, modelo: str, fecha_compra: str, estrategia):
        self.id_activo = id_activo
        self.modelo = modelo
        self.fecha_compra = fecha_compra
        self.estado = EstadoEquipo.OPERATIVO
        self.historial_incidencias = []
        
        # INYECCIÓN DE LA ESTRATEGIA: Se recibe el comportamiento por constructor
        self.estrategia_desgaste = estrategia 
    
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

    def calcular_obsolescencia(self) -> float:
        """
        DELEGACIÓN: El equipo no sabe la fórmula, solo llama a la estrategia.
        Cumple con el requisito de que dos equipos del mismo año puedan tener 
        índices de degradación diferentes.
        """
        return self.estrategia_desgaste.calcular(self.fecha_compra)
    
    def cambiar_estrategia(self, nueva_estrategia):
        """Permite cambiar el comportamiento en tiempo de ejecución"""
        self.estrategia_desgaste = nueva_estrategia

    def to_dict(self):
        """Datos para la BD"""
        return {
            "id_activo": self.id_activo,
            "modelo": self.modelo,
            "fecha_compra": self.fecha_compra,
            "estado": self.estado.value
        }

    def __str__(self):
        return f"[Equipo] {self.modelo} (ID: {self.id_activo})"