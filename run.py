from src.models.concretos import Osciloscopio, MotorInduccion
from src.repositories.equipo_repository import EquipoRepository

if __name__ == "__main__":
    print("--- 🔬 FIEE MAINTENANCE: PRUEBA DE ARQUITECTURA ---")
    
    # 1. Crear Objetos en Memoria
    osc = Osciloscopio("OSC-001", "Tektronix TBS", "2023-01-01", "100MHz")
    print(f"Equipo creado: {osc.modelo} | {osc.escanear_web()}")

    # 2. Intentar guardar (Solo funcionará si tienes el .env configurado)
    repo = EquipoRepository()
    repo.guardar_equipo(osc)