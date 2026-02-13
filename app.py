import streamlit as st
import sys
import os
import time
import random
import numpy as np
from datetime import datetime
from fpdf import FPDF
from src.services.vision_engine import VisionService

# --- CONFIGURACIÓN INICIAL ---
sys.path.append(os.getcwd())

# --- IMPORTACIONES ROBUSTAS (Para que no falle si faltan archivos) ---
try:
    from src.models.concretos import Osciloscopio, Multimetro, MotorInduccion
    from src.utils.enums import EstadoEquipo
    from src.logical.estrategias import DesgasteLineal, DesgasteExponencial
    # Intentamos importar el servicio de visión. Si falla, usaremos uno simulado.
    try:
        from src.services.vision_service import VisionService
    except ImportError:
        # Fallback por si la compañera cambió el nombre del archivo
        from src.services.vision_engine import VisionService
except ImportError as e:
    st.error(f"⚠️ ERROR CRÍTICO DE IMPORTACIÓN: {e}")
    st.info("Verifica que la carpeta 'src' esté bien estructurada.")
    st.stop()

st.set_page_config(page_title="FIEE Maintenance Pro", page_icon="🏭", layout="wide")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
    div[data-testid="stCameraInput"] { border: 2px solid #ddd; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 1. INICIALIZACIÓN DE ESTRATEGIAS (PERSISTENCIA) ---
# Esto garantiza que el patrón Strategy no se "olvide" al recargar
if 'est_lineal' not in st.session_state:
    st.session_state.est_lineal = DesgasteLineal()
if 'est_expo' not in st.session_state:
    st.session_state.est_expo = DesgasteExponencial()

# --- 2. BASE DE DATOS (SINGLETON) ---
if 'db_laboratorios' not in st.session_state:
    st.session_state.db_laboratorios = {
        "Laboratorio de Electrotecnia": [
            MotorInduccion("MOT-01", "Siemens 1LE1", "2020-01-15", "15HP", "440V", 3600, st.session_state.est_lineal),
            Osciloscopio("OSC-IND", "Rigol DS1054", "2023-03-10", "50MHz", st.session_state.est_expo)
        ],
        "Laboratorio de Física": [
            Osciloscopio("OSC-01", "Tektronix TBS", "2019-05-20", "100MHz", st.session_state.est_expo),
            Multimetro("MUL-01", "Fluke 115", "2022-08-01", "0.5%", True, st.session_state.est_lineal)
        ]
    }

# --- FUNCIONES AUXILIARES ---
def buscar_equipo_por_qr(qr_id):
    for lab, equipos in st.session_state.db_laboratorios.items():
        for eq in equipos:
            if eq.id_activo == qr_id:
                return eq, lab
    return None, None

def generar_pdf(equipo, lab):
    # 1. INSTANCIACIÓN
    # Creamos un objeto PDF vacío. Es el "lienzo" donde vamos a dibujar.
    pdf = FPDF()
    pdf.add_page()
    
    # --- BLOQUE A: SANITIZACIÓN DE DATOS ---
    # ¿Por qué? Las librerías de PDF antiguas (como FPDF) explotan si ven un emoji (✅, 🚨).
    # Esta función actúa como un "filtro" que limpia el texto antes de escribirlo.
    def limpiar_texto(texto):
        if not isinstance(texto, str): return str(texto)
        # Reemplazamos los iconos bonitos por texto seguro
        texto = texto.replace("✅", "[OK]").replace("🚨", "[ALERTA]").replace("🤖", "[IA]").replace("🔫", "[QR]")
        # Forzamos la codificación a Latin-1 (estándar occidental) para evitar errores raros
        return texto.encode('latin-1', 'replace').decode('latin-1')

    # --- BLOQUE B: CABECERA Y DATOS ---
    # Configuramos fuente Arial, Negrita (B), tamaño 16.
    pdf.set_font('Arial', 'B', 16)
    # Cell(ancho, alto, texto, borde, salto_linea, alineacion)
    pdf.cell(0, 10, 'FIEE - REPORTE DE ESTADO', 0, 1, 'C')
    pdf.ln(5) # Salto de línea de 5mm
    
    # Datos del Activo (Fondo Gris)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(240, 240, 240) # Color gris claro (RGB)
    # Usamos limpiar_texto() para asegurar que el modelo se imprima bien
    pdf.cell(0, 10, f"EQUIPO: {limpiar_texto(equipo.modelo)}", 1, 1, 'L', fill=True)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"ID: {equipo.id_activo} | Ubicacion: {limpiar_texto(lab)}", 0, 1)
    pdf.cell(0, 8, f"Estado Operativo: {limpiar_texto(equipo.estado.value)}", 0, 1)
    pdf.ln(5)

    # --- BLOQUE C: LÓGICA DE NEGOCIO (EL SEMÁFORO) ---
    # Aquí es donde tu código "piensa". No solo muestra el número, lo interpreta.
    desgaste = equipo.calcular_obsolescencia()
    porc = desgaste * 100
    
    # Algoritmo de decisión basado en umbrales (Thresholds)
    if porc < 40:
        # CASO VERDE: Todo bien.
        color_r, color_g, color_b = 200, 255, 200 
        titulo_estado = "ESTADO: OPTIMO (VERDE)"
        mensaje = "Eficiencia nominal. El equipo opera dentro de parametros seguros."
    elif porc < 70:
        # CASO AMARILLO: Atención.
        color_r, color_g, color_b = 255, 255, 200
        titulo_estado = "ESTADO: PRECAUCION (AMARILLO)"
        mensaje = "Signos de desgaste detectados. Se recomienda programar mantenimiento."
    else:
        # CASO ROJO: Peligro.
        color_r, color_g, color_b = 255, 200, 200
        titulo_estado = "ESTADO: CRITICO (ROJO)"
        mensaje = "Obsolescencia avanzada. Riesgo inminente de falla. Evaluar reemplazo."

    # --- BLOQUE D: RENDERIZADO VISUAL ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "DIAGNOSTICO DEL CICLO DE VIDA", 0, 1)
    
    # Dibujamos la caja con el color calculado en el Bloque C
    pdf.set_fill_color(color_r, color_g, color_b)
    pdf.set_font('Arial', 'B', 14)
    # Esta es la barra de color principal del reporte
    pdf.cell(0, 12, f"{titulo_estado} - {porc:.2f}% DESGASTE", 1, 1, 'C', fill=True)
    
    # Explicación para el gerente/profesor
    pdf.set_font('Arial', 'I', 10) # Cursiva (Italic)
    pdf.multi_cell(0, 8, f"Interpretacion: {mensaje}")
    pdf.ln(5)

    # --- BLOQUE E: TRAZABILIDAD (HISTORIAL) ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "HISTORIAL DE INCIDENCIAS", 0, 1)
    # Dibujamos una línea horizontal
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    if not equipo.historial_incidencias:
        pdf.set_font('Arial', 'I', 11)
        pdf.cell(0, 10, "Sin registros.", 0, 1)
    else:
        for inc in equipo.historial_incidencias:
            pdf.ln(3)
            # Fecha y Hora
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 6, f"FECHA: {inc['fecha']}", 0, 1)
            
            # Detalle del humano
            pdf.set_font('Arial', '', 10)
            det_limpio = limpiar_texto(inc.get('detalle', ''))
            pdf.multi_cell(0, 5, f"Reporte: {det_limpio}")
            
            # Detalle de la IA (Si existe)
            if 'dictamen_ia' in inc:
                pdf.set_font('Courier', '', 9) # Fuente tipo máquina de escribir para código/IA
                ia_limpio = limpiar_texto(inc['dictamen_ia'])
                pdf.multi_cell(0, 5, f">> ANALISIS IA: {ia_limpio}")
                
    # 2. SALIDA
    # Generamos el binario del PDF para que el navegador lo pueda descargar
    return pdf.output(dest='S').encode('latin-1')

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2942/2942544.png", width=80)
    st.title("Acceso FIEE")
    rol = st.radio("Seleccione Perfil:", ["🎓 Estudiante / Técnico", "👨‍🏫 Docente / Admin"])
    st.divider()
    st.info("💡 **IDs Demo:** MOT-01, OSC-01, MUL-01")

# ==========================================
# 🎓 VISTA ESTUDIANTE: REPORTE CON DOBLE OPCIÓN
# ==========================================
if rol == "🎓 Estudiante / Técnico":
    st.header("📲 Registro de Incidencias (QR)")
    
    qr_input = st.text_input("🔫 Escanear Código QR (Ingrese ID)", placeholder="Ej: MOT-01").strip()
    
    if qr_input:
        equipo_encontrado, lab_ubicacion = buscar_equipo_por_qr(qr_input)
        
        if equipo_encontrado:
            st.success(f"✅ Equipo Identificado: {equipo_encontrado.modelo}")
            
            with st.container(border=True):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if isinstance(equipo_encontrado, MotorInduccion):
                        st.image("https://cdn-icons-png.flaticon.com/512/3662/3662819.png", width=100)
                    else:
                        st.image("https://cdn-icons-png.flaticon.com/512/9626/9626649.png", width=100)
                
                with c2:
                    st.write(f"**Ubicación:** {lab_ubicacion}")
                    st.write(f"**Estado:** {equipo_encontrado.estado.value}")
                    obs = equipo_encontrado.calcular_obsolescencia()
                    st.progress(obs, text=f"Desgaste Técnico: {obs*100:.1f}%")

            st.divider()
            
            # --- FORMULARIO UNIFICADO ---
            with st.form("form_incidencia"):
                st.subheader("🚨 Reportar Avería con IA")
                usuario = st.text_input("Tu Código / Nombre", "Alumno-001")
                desc = st.text_area("Describe la falla observada")
                
                st.markdown("### 📸 Evidencia Visual (Opcional)")
                st.caption("Puedes tomar una foto ahora mismo o subir una de tu galería.")
                
                # COLUMNAS PARA LAS DOS OPCIONES
                col_cam, col_upl = st.columns(2)
                with col_cam:
                    foto_cam = st.camera_input("Opción A: Usar Cámara")
                with col_upl:
                    foto_upl = st.file_uploader("Opción B: Subir Archivo", type=["jpg", "png", "jpeg"])
                
                enviar = st.form_submit_button("📢 ENVIAR REPORTE")
                
                if enviar:
                    if desc:
                        # Prioridad: Si hay foto de cámara, usa esa. Si no, usa la subida.
                        foto_final = foto_cam if foto_cam is not None else foto_upl
                        
                        with st.spinner("Procesando con Visión Artificial..."):
                            time.sleep(1) # Pequeña pausa para UX
                            dictamen_ia = "No se adjuntó evidencia visual."
                            
                            if foto_final:
                                # Guardamos temporalmente para que OpenCV lo lea
                                with open("temp_vision.jpg", "wb") as f:
                                    f.write(foto_final.getbuffer())
                                
                                # Llamada al servicio de tu compañera
                                try:
                                    servicio_vision = VisionService()
                                    # Intentamos llamar al método, asumiendo que es analizar_quemadura o similar
                                    # Si tu compañera usa otro nombre, el try/except lo manejará
                                    if hasattr(servicio_vision, 'analizar_quemadura'):
                                        res = servicio_vision.analizar_quemadura("temp_vision.jpg")
                                    else:
                                        # Fallback por si el nombre cambió
                                        res = servicio_vision.analizar_integridad("temp_vision.jpg")
                                        
                                    dictamen_ia = f"{res.get('alerta', 'Info')}: {res.get('diagnostico', 'Analizado')} (Brillo: {res.get('brillo_detectado', 0)})"
                                    
                                    # Lógica de negocio: Si es crítico, marcamos el equipo
                                    if "ALERTA" in str(res.get('alerta', '')):
                                        equipo_encontrado.estado = EstadoEquipo.REPORTADO_CON_FALLA
                                        
                                except Exception as e:
                                    dictamen_ia = f"Error en análisis de imagen: {str(e)}"
                                
                                # Limpieza
                                if os.path.exists("temp_vision.jpg"):
                                    os.remove("temp_vision.jpg")
                            
                            # Guardar en Historial
                            detalle_completo = f"{desc} | Reportado por: {usuario}"
                            equipo_encontrado.registrar_incidencia(detalle_completo)
                            
                            # Actualizar el último ticket con la data de IA
                            ticket = equipo_encontrado.historial_incidencias[-1]
                            ticket['dictamen_ia'] = dictamen_ia
                            ticket['foto'] = "Evidencia Adjunta" if foto_final else "Sin foto"
                            
                            st.success("¡Reporte enviado y analizado por IA!")
                            st.info(f"Resultado Visión: {dictamen_ia}")
                            time.sleep(2.5)
                            st.rerun()
                    else:
                        st.warning("⚠️ Debes describir el problema para enviar.")
        else:
            st.error("❌ Código QR no encontrado.")

# ==========================================
# 👨‍🏫 VISTA DOCENTE: STRATEGY PATTERN + GESTIÓN
# ==========================================
else:
    st.header("📊 Centro de Control FIEE")
    
    lab_actual = st.selectbox("📍 Filtrar por Laboratorio:", list(st.session_state.db_laboratorios.keys()))
    equipos = st.session_state.db_laboratorios[lab_actual]
    
    tab_dash, tab_rep, tab_alta = st.tabs(["📈 Dashboard", "📑 Reportes & Estrategias", "➕ Alta Activos"])
    
    with tab_dash:
        total = len(equipos)
        if total > 0:
            fallas = sum(1 for e in equipos if e.estado != EstadoEquipo.OPERATIVO)
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Equipos", total)
            c2.metric("Equipos con Falla", fallas, delta_color="inverse")
            promedio_vida = sum([1 - e.calcular_obsolescencia() for e in equipos]) / total
            c3.metric("Vida Útil Promedio", f"{promedio_vida*100:.0f}%")
        else:
            st.info("No hay equipos registrados en este laboratorio.")

    # --- PESTAÑA PRINCIPAL DEL PATRÓN STRATEGY ---
    with tab_rep:
        st.subheader("Gestión de Obsolescencia (Strategy Pattern)")
        
        # Selector usando índices para evitar pérdida de referencia
        if equipos:
            idx_sel = st.selectbox("Seleccionar Equipo:", range(len(equipos)), 
                                  format_func=lambda i: f"{equipos[i].modelo} ({equipos[i].id_activo})")
            eq_sel = equipos[idx_sel]
            
            c_info, c_hist = st.columns([1, 2])
            
            with c_info:
                st.info(f"**Estado:** {eq_sel.estado.value}")
                st.markdown("#### Configuración de Cálculo")
                
                # 1. MOSTRAR ESTRATEGIA ACTUAL
                est_actual_nombre = type(eq_sel.estrategia_desgaste).__name__
                st.write(f"🧠 Estrategia en Memoria: **{est_actual_nombre}**")
                
                # 2. SELECCIONAR NUEVA
                nueva_opcion = st.radio("Cambiar Algoritmo:", ["Lineal", "Exponencial"], 
                                       index=0 if est_actual_nombre == "DesgasteLineal" else 1, horizontal=True)
                
                # 3. APLICAR CAMBIO (Con lógica de persistencia)
                if st.button("🔄 Aplicar y Recalcular"):
                    if nueva_opcion == "Lineal":
                        eq_sel.cambiar_estrategia(st.session_state.est_lineal)
                    else:
                        eq_sel.cambiar_estrategia(st.session_state.est_expo)
                    
                    # GUARDADO EXPLÍCITO EN SESSION_STATE
                    st.session_state.db_laboratorios[lab_actual][idx_sel] = eq_sel
                    
                    st.toast(f"Estrategia actualizada a: {nueva_opcion}", icon="✅")
                    time.sleep(0.5)
                    st.rerun() # Recarga para mostrar el nuevo número

                # 4. RESULTADO
                obs = eq_sel.calcular_obsolescencia()
                st.metric("Obsolescencia Calculada", f"{obs*100:.2f}%")
                
                # Barra de progreso con colores según gravedad
                color_bar = "green"
                if obs > 0.7: color_bar = "red"
                elif obs > 0.4: color_bar = "orange"
                st.progress(min(obs, 1.0))
                
                if st.button("📄 Descargar Reporte PDF"):
                    pdf_data = generar_pdf(eq_sel, lab_actual)
                    st.download_button("⬇️ Guardar", pdf_data, f"Reporte_{eq_sel.id_activo}.pdf", "application/pdf")
            
            with c_hist:
                st.markdown("### 📂 Historial de Incidencias")
                if not eq_sel.historial_incidencias:
                    st.warning("Este equipo no tiene reportes registrados.")
                else:
                    for i, inc in enumerate(eq_sel.historial_incidencias):
                        with st.expander(f"Ticket #{i+1} | {inc['fecha']}", expanded=True):
                            st.write(f"**Detalle:** {inc.get('detalle', '')}")
                            if 'dictamen_ia' in inc:
                                st.markdown(f"> 🤖 **Análisis IA:** {inc['dictamen_ia']}")
                            if 'foto' in inc:
                                st.caption(f"Evidencia: {inc['foto']}")
        else:
            st.warning("No hay equipos para mostrar.")

    with tab_alta:
        st.markdown("### Registrar Nuevo Equipo")
        with st.form("nuevo_equipo"):
            c1, c2 = st.columns(2)
            tipo = c1.selectbox("Tipo", ["Motor", "Osciloscopio", "Multimetro"])
            modelo = c2.text_input("Modelo")
            fecha = st.date_input("Fecha Compra", datetime(2020, 1, 1))
            submit = st.form_submit_button("💾 Guardar Equipo")
            
            if submit and modelo:
                new_id = f"NEW-{random.randint(100,999)}"
                f_str = fecha.strftime("%Y-%m-%d")
                
                # Factory manual con estrategias persistentes
                if tipo == "Motor":
                    obj = MotorInduccion(new_id, modelo, f_str, "10", "220", 1800, st.session_state.est_lineal)
                elif tipo == "Osciloscopio":
                    obj = Osciloscopio(new_id, modelo, f_str, "100MHz", st.session_state.est_expo)
                else:
                    obj = Multimetro(new_id, modelo, f_str, "1%", True, st.session_state.est_lineal)
                
                st.session_state.db_laboratorios[lab_actual].append(obj)
                st.success(f"Equipo {new_id} registrado correctamente.")
                time.sleep(1)
                st.rerun()