import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- 1. OPTIMIZACIÓN CON CACHÉ (Punto Clave del Entregable 5) ---
@st.cache_data
def cargar_inventario():
    """
    Simula la carga de datos desde la Base de Datos (Supabase).
    """
    # Simulamos un retraso para demostrar el uso de caché al profesor
    time.sleep(1) 
    
    # DATOS MOCK (Datos temporales para el Dashboard)
    data = [
        {"id": "OSC-001", "nombre": "Osciloscopio Tektronix", "tipo": "Electrónico", "fecha_compra": "2019-05-20", "estado": "OPERATIVO", "ubicacion": "Lab Control"},
        {"id": "GEN-002", "nombre": "Generador de Funciones", "tipo": "Electrónico", "fecha_compra": "2018-03-15", "estado": "CRÍTICO", "ubicacion": "Lab Circuitos"},
        {"id": "MOT-003", "nombre": "Motor Trifásico Siemens", "tipo": "Mecánico", "fecha_compra": "2015-08-10", "estado": "MANTENIMIENTO", "ubicacion": "Lab Máquinas"},
        {"id": "MUL-004", "nombre": "Multímetro Fluke", "tipo": "Electrónico", "fecha_compra": "2021-01-10", "estado": "OPERATIVO", "ubicacion": "Pañol"},
        {"id": "TRA-005", "nombre": "Transformador 50kVA", "tipo": "Mecánico", "fecha_compra": "2010-11-05", "estado": "CRÍTICO", "ubicacion": "Subestación"},
    ]
    
    # Convertimos la lista en un DataFrame de Pandas
    return pd.DataFrame(data)

# --- 2. ESTRUCTURA DE LA VISTA (MVC) ---
def mostrar_dashboard():
    st.title("📊 Dashboard de Activos FIEE")
    st.markdown("---")

    # A. Cargamos los datos (Usando caché)
    df = cargar_inventario()

    # B. BARRA LATERAL DE FILTROS (Sidebar)
    st.sidebar.header("🔍 Filtros de Inventario")
    
    tipos_disponibles = df["tipo"].unique()
    tipos_selec = st.sidebar.multiselect("Filtrar por Tipo:", options=tipos_disponibles, default=tipos_disponibles)
    
    estados_disponibles = df["estado"].unique()
    estados_selec = st.sidebar.multiselect("Filtrar por Estado:", options=estados_disponibles, default=estados_disponibles)

    # C. APLICAR FILTROS (Lógica de Pandas)
    df_filtrado = df[
        (df["tipo"].isin(tipos_selec)) & 
        (df["estado"].isin(estados_selec))
    ]

    # D. MÉTRICAS CLAVE (KPIs)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Equipos", len(df_filtrado))
    col2.metric("Críticos", len(df_filtrado[df_filtrado["estado"] == "CRÍTICO"]), delta="-Riesgo", delta_color="inverse")
    col3.metric("Operativos", len(df_filtrado[df_filtrado["estado"] == "OPERATIVO"]), delta="+Ok")

    # E. MOSTRAR TABLA INTERACTIVA
    st.subheader("📋 Listado Detallado")
    
    st.dataframe(
        df_filtrado,
        use_container_width=True,
        column_config={
            "fecha_compra": st.column_config.DateColumn("Fecha Compra", format="DD/MM/YYYY"),
            "estado": st.column_config.TextColumn("Estado", help="Estado actual según inspección")
        },
        hide_index=True
    )

    # Botón de recarga manual
    if st.button("🔄 Actualizar Datos"):
        st.cache_data.clear()
        st.rerun() 