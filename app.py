import streamlit as st
import sys
import os

# 1. Configuración de Rutas
sys.path.append(os.getcwd())

# 2. Imports del Modelo (Backend)
from src.models.concretos import Osciloscopio, Multimetro, MotorInduccion
from src.logical.estrategias import DesgasteLineal, DesgasteExponencial
# --- NUEVOS IMPORTS ---
from src.repositories.equipo_repository import EquipoRepository 
from src.utils.mapper import map_json_to_object

# 3. Imports de las Vistas (Frontend POO)
from src.views.inspeccion import VistaInspeccion
from src.views.dashboard import VistaDashboard

st.set_page_config(page_title="FIEE Maintenance OOP", page_icon="🏭", layout="wide")

# --- INITIALIZATION (Persistencia REAL con Supabase) ---
if 'db_laboratorios' not in st.session_state:
    # A. Inicialización de Estrategias (Singleton)
    st.session_state.est_lineal = DesgasteLineal()
    st.session_state.est_expo = DesgasteExponencial()
    
    # B. CARGA DE DATOS DESDE SUPABASE (Reemplaza al diccionario manual)
    repo = EquipoRepository()
    datos_crudos = repo.leer_todos()
    
    if datos_crudos:
        st.session_state.db_laboratorios = map_json_to_object(
            datos_crudos, 
            st.session_state.est_lineal, 
            st.session_state.est_expo
        )
        print("✅ Datos cargados de Supabase")
    else:
        st.warning("⚠️ Base de datos vacía o desconectada. Iniciando vacío.")
        st.session_state.db_laboratorios = {}

# --- CONTROLLER (Main) ---
def main():
    # Menú Lateral
    with st.sidebar:
        st.title("Sistema FIEE")
        st.info("Sistema de Gestión de Activos v1.0")
        opcion = st.radio("Seleccione Perfil:", ["Estudiante / Técnico", "Docente / Admin"])

    # --- APLICACIÓN DE POLIMORFISMO ---
    vista_actual = None

    if opcion == "Estudiante / Técnico":
        vista_actual = VistaInspeccion()
    else:
        vista_actual = VistaDashboard()

    if vista_actual:
        vista_actual.render()

if __name__ == "__main__":
    main()
    