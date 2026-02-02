import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            
            # Verificación de seguridad para evitar errores si no hay .env
            if not url or not key:
                print("⚠️ [ADVERTENCIA] No se detectó archivo .env con credenciales.")
                return None
            
            print("🌐 Estableciendo conexión única con Supabase...")
            cls._instance = create_client(url, key)
        
        return cls._instance