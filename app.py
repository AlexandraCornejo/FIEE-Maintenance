import streamlit as st
import sys
import os

# 1. Configuración de Rutas
sys.path.append(os.getcwd())

# 2. Imports del Modelo (Backend)
from src.models.concretos import Osciloscopio, Multimetro, MotorInduccion
from src.logical.estrategias import DesgasteLineal, DesgasteExponencial

# 3. Imports de las Vistas (Frontend POO)
from src.views.inspeccion import VistaInspeccion
from src.views.dashboard import VistaDashboard

st.set_page_config(page_title="FIEE Maintenance OOP", page_icon="🏭", layout="wide")

# --- INITIALIZATION (Persistencia de Datos Simulada) ---
if 'db_laboratorios' not in st.session_state:
    # A. Inicialización de Estrategias (Singleton)
    st.session_state.est_lineal = DesgasteLineal()
    st.session_state.est_expo = DesgasteExponencial()
    
    # B. Base de Datos Simulada (¡AQUÍ AGREGAMOS MÁS EQUIPOS!)
    st.session_state.db_laboratorios = {
        
        "Laboratorio de Máquinas Eléctricas": [
            # MotorInduccion: (id, modelo, fecha, hp, voltaje, rpm, estrategia)
            MotorInduccion("MOT-01", "Siemens 1LE1", "2020-01-15", "15HP", "440V", 3600, st.session_state.est_lineal),
            MotorInduccion("MOT-02", "WEG W22", "2018-05-20", "10HP", "380V", 1800, st.session_state.est_expo),
        ],
        
        "Laboratorio de Telecomunicaciones": [
            # Osciloscopio: (id, modelo, fecha, ancho_banda, estrategia)
            Osciloscopio("OSC-01", "Tektronix TBS", "2019-05-20", "100MHz", st.session_state.est_expo),
            Osciloscopio("OSC-02", "Keysight EDU", "2021-11-10", "70MHz", st.session_state.est_lineal),
        ],
        
        "Laboratorio de Circuitos": [
            # Multimetro: (id, modelo, fecha, precision, es_digital, estrategia)
            # ¡Aquí estaba el error! Faltaba el True/False
            Multimetro("MUL-01", "Fluke 87V", "2022-02-01", "0.05%", True, st.session_state.est_lineal),
            Multimetro("MUL-02", "Uni-T UT61E", "2020-08-15", "0.1%", True, st.session_state.est_expo),
        ]
    }
# --- CONTROLLER (Main) ---
def main():
    # Menú Lateral
    with st.sidebar:
        st.title("Sistema FIEE")
        st.info("Sistema de Gestión de Activos v1.0")
        opcion = st.radio("Seleccione Perfil:", ["Estudiante / Técnico", "Docente / Admin"])

    # --- APLICACIÓN DE POLIMORFISMO ---
    # La variable 'vista_actual' puede comportarse de diferentes formas
    vista_actual = None

    if opcion == "Estudiante / Técnico":
        # Instanciamos la clase hija Inspección (Aquí usas la cámara y QR)
        vista_actual = VistaInspeccion()
    else:
        # Instanciamos la clase hija Dashboard (Aquí ves los gráficos y reportes)
        vista_actual = VistaDashboard()

    # Ejecución Polimórfica: 
    # No importa qué clase sea, ambas tienen el método .render()
    if vista_actual:
        vista_actual.render()

if __name__ == "__main__":
    main()