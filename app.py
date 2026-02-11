import streamlit as st
import sys
import os
import time
import random
from datetime import datetime
from fpdf import FPDF

# --- CONFIGURACIÓN Y RUTAS ---
sys.path.append(os.getcwd())

try:
    from src.models.concretos import Osciloscopio, Multimetro, MotorInduccion
    from src.utils.enums import EstadoEquipo
    from src.interfaces.mixins import AnalizadorPredictivo, InspectorVisual
except ImportError:
    st.error("⚠️ Error: No se encuentran los archivos en 'src'.")
    st.stop()

st.set_page_config(page_title="FIEE Maintenance Pro", page_icon="🏭", layout="wide")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS (SINGLETON EN MEMORIA) ---
if 'db_laboratorios' not in st.session_state:
    st.session_state.db_laboratorios = {
        "Laboratorio de Electrotecnia": [
            MotorInduccion("MOT-01", "Siemens 1LE1", "2020", "15HP", "440V", 3600),
            Osciloscopio("OSC-IND", "Rigol DS1054", "2023", "50MHz")
        ],
        "Laboratorio de Física": [
            Osciloscopio("OSC-01", "Tektronix TBS", "2019", "100MHz"),
            Multimetro("MUL-01", "Fluke 115", "2022", "0.5%", True)
        ]
    }

# --- FUNCIONES AUXILIARES ---

def buscar_equipo_por_qr(qr_id):
    """Busca un equipo por su ID en todos los laboratorios"""
    for lab, equipos in st.session_state.db_laboratorios.items():
        for eq in equipos:
            if eq.id_activo == qr_id:
                return eq, lab
    return None, None

def generar_dictamen_ia(texto):
    frases = ["Desgaste severo en rodamientos.", "Falla en aislamiento eléctrico.", "Sobrecalentamiento crítico detectado."]
    return f"IA DETECTÓ: {random.choice(frases)} Se requiere parada técnica."

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'FIEE - REPORTE DE MANTENIMIENTO', 0, 1, 'C')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Pág {self.page_no()}', 0, 0, 'C')

def generar_pdf(equipo, lab):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(230, 240, 255)
    pdf.cell(0, 10, f"EQUIPO: {equipo.modelo}", 1, 1, 'L', fill=True)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"ID: {equipo.id_activo} | Ubicación: {lab}", 0, 1)
    pdf.cell(0, 8, f"Estado: {equipo.estado.value}", 0, 1)
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "HISTORIAL DE FALLAS", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    if not equipo.historial_incidencias:
        pdf.set_font('Arial', 'I', 11)
        pdf.cell(0, 10, "Sin registros.", 0, 1)
    else:
        for inc in equipo.historial_incidencias:
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 6, f"[{inc['fecha']}] {inc['usuario']}", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 5, f"Problema: {inc['descripcion']}")
            if 'dictamen_ia' in inc:
                pdf.set_font('Courier', '', 9)
                pdf.multi_cell(0, 5, f">> {inc['dictamen_ia']}")
            pdf.ln(3)
    return pdf.output(dest='S').encode('latin-1')

# --- BARRA LATERAL (SELECCIÓN DE ROL) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942544.png", width=80)
    st.title("Acceso FIEE")
    rol = st.radio("Seleccione Perfil:", ["🎓 Estudiante / Técnico", "👨‍🏫 Docente / Admin"])
    st.divider()
    
    # Ayuda visual para la Demo
    st.info("💡 **IDs para probar el QR:**\n- MOT-01\n- OSC-01\n- MUL-01")

# ==========================================
# 🎓 VISTA ESTUDIANTE: ESCANEO Y REPORTE
# ==========================================
if rol == "🎓 Estudiante / Técnico":
    st.header("📲 Registro de Incidencias (QR)")
    st.markdown("Escanee el código QR del equipo dañado para reportar una falla.")

    col_qr, col_manual = st.columns([2, 1])
    with col_qr:
        # Simulamos el escáner con un input de texto (en la vida real sería la cámara)
        qr_input = st.text_input("🔫 Escanear Código QR (Ingrese ID)", placeholder="Ej: MOT-01").strip()
    
    if qr_input:
        equipo_encontrado, lab_ubicacion = buscar_equipo_por_qr(qr_input)
        
        if equipo_encontrado:
            st.success(f"✅ Equipo Identificado: {equipo_encontrado.modelo}")
            
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                with c1:
                    # Imagen dinámica según tipo
                    if isinstance(equipo_encontrado, MotorInduccion):
                        st.image("https://cdn-icons-png.flaticon.com/512/3662/3662819.png", width=100)
                    else:
                        st.image("https://cdn-icons-png.flaticon.com/512/9626/9626649.png", width=100)
                
                with c2:
                    st.write(f"**Ubicación:** {lab_ubicacion}")
                    st.write(f"**Estado Actual:** {equipo_encontrado.estado.value}")
                    st.progress(equipo_encontrado.calcular_obsolescencia(), text="Desgaste Técnico")

                st.divider()
                st.subheader("🚨 Reportar Avería")
                
                with st.form("form_incidencia"):
                    usuario = st.text_input("Tu Código / Nombre", "Alumno-001")
                    desc = st.text_area("Describe la falla observada")
                    foto = st.file_uploader("Adjuntar Foto Evidencia", type=["jpg", "png"])
                    
                    enviar = st.form_submit_button("📢 ENVIAR REPORTE")
                    
                    if enviar:
                        if desc:
                            with st.spinner("Subiendo evidencia y analizando con IA..."):
                                time.sleep(1.5)
                                ia_dx = generar_dictamen_ia(desc)
                                
                                # 1. GUARDADO
                                equipo_encontrado.registrar_incidencia(desc, usuario)
                                
                                # 2. ENRIQUECIMIENTO (IA + FOTO)
                                ticket = equipo_encontrado.historial_incidencias[-1]
                                ticket['dictamen_ia'] = ia_dx
                                ticket['foto'] = foto.name if foto else None
                                
                                st.success("¡Reporte enviado al sistema central!")
                                time.sleep(1)
                                st.rerun() # Refresca para limpiar el form
                        else:
                            st.warning("⚠️ Debes describir el problema.")
        else:
            st.error("❌ Código QR no encontrado en el inventario.")
    else:
        st.info("👈 Ingrese un ID (ej: MOT-01) para comenzar.")

# ==========================================
# 👨‍🏫 VISTA DOCENTE: REPORTES Y GESTIÓN
# ==========================================
else:
    st.header("📊 Centro de Control FIEE")
    
    # Selector de Laboratorio
    lab_actual = st.selectbox("📍 Filtrar por Laboratorio:", list(st.session_state.db_laboratorios.keys()))
    equipos = st.session_state.db_laboratorios[lab_actual]
    
    tab_dash, tab_rep, tab_alta = st.tabs(["📈 Dashboard", "📑 Reportes Oficiales", "➕ Alta Activos"])
    
    # --- DASHBOARD ---
    with tab_dash:
        total = len(equipos)
        fallas = sum(1 for e in equipos if e.estado != EstadoEquipo.OPERATIVO)
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Equipos", total)
        c2.metric("Equipos con Falla", fallas, delta_color="inverse")
        c3.metric("Disponibilidad", f"{((total-fallas)/total)*100:.0f}%" if total > 0 else "0%")
        
        st.markdown("### Vista Rápida")
        cols = st.columns(3)
        for i, eq in enumerate(equipos):
            with cols[i%3]:
                with st.container(border=True):
                    color = "🔴" if eq.estado != EstadoEquipo.OPERATIVO else "🟢"
                    st.markdown(f"**{color} {eq.modelo}**")
                    st.caption(f"ID: {eq.id_activo}")
                    # Botón para saltar a reportes (UX Trick)
                    st.caption(f"Incidencias: {len(eq.historial_incidencias)}")

    # --- REPORTES (Aquí es donde se quejaba de que no actualizaba) ---
    with tab_rep:
        st.subheader("Expedientes Técnicos")
        
        # Selector de Equipo
        eq_sel = st.selectbox("Seleccionar Equipo:", equipos, format_func=lambda x: f"{x.modelo} ({x.id_activo})")
        
        if eq_sel:
            c_info, c_hist = st.columns([1, 2])
            
            with c_info:
                st.info(f"**Estado:** {eq_sel.estado.value}")
                st.write(f"**Obsolescencia:** {eq_sel.calcular_obsolescencia()*100:.1f}%")
                if st.button("📄 Descargar PDF"):
                    pdf_data = generar_pdf(eq_sel, lab_actual)
                    st.download_button("⬇️ Guardar", pdf_data, f"Reporte_{eq_sel.id_activo}.pdf", "application/pdf")
            
            with c_hist:
                st.markdown("### 📂 Historial de Incidencias")
                if not eq_sel.historial_incidencias:
                    st.warning("Este equipo no tiene reportes registrados.")
                else:
                    for i, inc in enumerate(eq_sel.historial_incidencias):
                        with st.expander(f"Ticket #{i+1} | {inc['fecha']} | {inc['usuario']}", expanded=True):
                            st.error(f"**Falla:** {inc['descripcion']}")
                            if 'dictamen_ia' in inc:
                                st.markdown(f"> 🤖 *{inc['dictamen_ia']}*")
                            if 'foto' in inc and inc['foto']:
                                st.markdown(f"📎 **Adjunto:** {inc['foto']}")
    
    # --- ALTA ---
    with tab_alta:
        st.markdown("### Registrar Nuevo Equipo")
        c1, c2 = st.columns(2)
        tipo = c1.selectbox("Tipo", ["Motor", "Osciloscopio", "Multimetro"])
        modelo = c2.text_input("Modelo")
        if st.button("Guardar Equipo"):
            new_id = f"NEW-{random.randint(100,999)}"
            if tipo == "Motor": obj = MotorInduccion(new_id, modelo, "2024", "10", "220", 1800)
            elif tipo == "Osciloscopio": obj = Osciloscopio(new_id, modelo, "2024", "100MHz")
            else: obj = Multimetro(new_id, modelo, "2024", "1%", True)
            
            st.session_state.db_laboratorios[lab_actual].append(obj)
            st.success("Guardado.")
            time.sleep(0.5)
            st.rerun()