from enum import Enum

class EstadoEquipo(Enum):
    OPERATIVO = "Operativo"
    REPORTADO_CON_FALLA = "Reportado con Falla"
    EN_MANTENIMIENTO = "En Mantenimiento"
    DE_BAJA = "De Baja"