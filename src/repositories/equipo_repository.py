from src.database.db import DatabaseConnection

class EquipoRepository:
    def __init__(self):
        self.db = DatabaseConnection() # Singleton

    def guardar_equipo(self, equipo):
        if not self.db:
            print("❌ Error: Base de datos no conectada (Revisa el .env)")
            return

        # 1. Convertir datos básicos
        data_dict = equipo.to_dict()
        
        # 2. Empaquetar detalles técnicos en el JSONB
        detalles = {}
        if hasattr(equipo, 'ancho_banda'): detalles['ancho_banda'] = equipo.ancho_banda
        if hasattr(equipo, 'hp'): detalles['hp'] = equipo.hp
        if hasattr(equipo, 'voltaje'): detalles['voltaje'] = equipo.voltaje
        
        data_dict['detalles_tecnicos'] = detalles
        
        try:
            # Insertar en tabla 'equipos'
            response = self.db.table("equipos").insert(data_dict).execute()
            print(f"✅ Guardado en Nube: {equipo.modelo}")
            return response
        except Exception as e:
            print(f"❌ Error guardando en BD: {e}")

    def leer_todos(self):
        if not self.db:
            return []
        try:
            response = self.db.table("equipos").select("*").execute()
            return response.data
        except Exception as e:
            print(f"❌ Error leyendo BD: {e}")
            return []