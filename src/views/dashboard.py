import streamlit as st
import pandas as pd
import random
import os
import time
from datetime import datetime
from fpdf import FPDF
from src.views.base_view import Vista 
from src.models.concretos import MotorInduccion, Osciloscopio, Multimetro
from src.logical.estrategias import DesgasteLineal, DesgasteExponencial

# --- IMPORTS PARA LA IA ---
from src.utils.enums import EstadoEquipo
from src.services.vision_service import VisionService

# ==============================================================================
# 1. ZONA DE UTILIDADES (Lógica de Negocio y PDF)
# ==============================================================================

def obtener_comentario_estado(obs_val, estado_str):
    est_upper = str(estado_str).upper()
    if obs_val >= 0.95 or any(palabra in est_upper for palabra in ["MANTENIMIENTO", "FALLA", "REPORTADO", "BAJA"]):
        return "⚠️ ATENCIÓN: Equipo fuera de servicio. Revisar dictamen de IA."
    if obs_val < 0.2: return "✅ Óptimas condiciones. Uso estándar."
    elif obs_val < 0.5: return "🟡 Desgaste moderado. Inspección preventiva."
    elif obs_val < 0.8: return "🟠 Desgaste avanzado. Programar mantenimiento."
    else: return "🔴 CRÍTICO: Riesgo inminente. Evaluar reemplazo."

def convertir_objetos_a_df(_lista_equipos_dict):
    data = []
    for lab_nombre, lista_equipos in _lista_equipos_dict.items():
        for eq in lista_equipos:
            obs_num = eq.calcular_obsolescencia()
            estado_actual = eq.estado.value if hasattr(eq.estado, 'value') else str(eq.estado)
            data.append({
                "ID": eq.id_activo,
                "Modelo": eq.modelo,
                "Tipo": type(eq).__name__, 
                "Ubicación": lab_nombre,
                "Estado": estado_actual,
                "Obsolescencia_Num": obs_num * 100, 
                "Análisis del Sistema": obtener_comentario_estado(obs_num, estado_actual),
                "OBJ_REF": eq 
            })
    return pd.DataFrame(data)

def generar_pdf(equipo, lab):
    pdf = FPDF()
    pdf.add_page()
    
    def limpiar_texto(texto):
        if not isinstance(texto, str): return str(texto)
        return texto.replace("✅", "[OK]").replace("🚨", "[ALERTA]").replace("🤖", "[IA]").encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'FIEE - REPORTE DE ESTADO TECNICO', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"EQUIPO: {limpiar_texto(equipo.modelo)}", 1, 1, 'L', fill=True)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"ID: {equipo.id_activo} | Ubicacion: {limpiar_texto(lab)}", 0, 1)
    estado_val = equipo.estado.value if hasattr(equipo.estado, 'value') else str(equipo.estado)
    pdf.cell(0, 8, f"Estado Operativo: {limpiar_texto(estado_val)}", 0, 1)
    
    desgaste = equipo.calcular_obsolescencia()
    porc = desgaste * 100
    
    if porc < 40: color = (200, 255, 200); msg = "Estado Optimo."
    elif porc < 70: color = (255, 255, 200); msg = "Precaucion: Desgaste detectado."
    else: color = (255, 200, 200); msg = "Estado Critico: Evaluar reemplazo."

    pdf.set_fill_color(*color)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 12, f"DESGASTE: {porc:.2f}%", 1, 1, 'C', fill=True)
    pdf.set_font('Arial', 'I', 10)
    pdf.multi_cell(0, 8, f"Interpretacion: {msg}")
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "HISTORIAL DE INCIDENCIAS", 0, 1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    
    if not equipo.historial_incidencias:
        pdf.cell(0, 10, "Sin registros.", 0, 1)
    else:
        for inc in equipo.historial_incidencias:
            pdf.ln(3)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 6, f"FECHA: {inc['fecha']}", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 5, f"Reporte: {limpiar_texto(inc.get('detalle', ''))}")
            if 'dictamen_ia' in inc:
                pdf.set_font('Courier', '', 9)
                pdf.multi_cell(0, 5, f">> IA: {limpiar_texto(inc['dictamen_ia'])}")

    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 2. CLASE VISTA DASHBOARD
# ==============================================================================

class VistaDashboard(Vista):
    def render(self):
        st.title("📊 Dashboard de Activos FIEE")
        st.markdown("---")

        if 'db_laboratorios' not in st.session_state:
            st.error("Datos no inicializados.")
            return

        # Persistencia de estrategias
        if 'est_lineal' not in st.session_state: st.session_state.est_lineal = DesgasteLineal()
        if 'est_expo' not in st.session_state: st.session_state.est_expo = DesgasteExponencial()

        df = convertir_objetos_a_df(st.session_state.db_laboratorios)

        st.sidebar.header("🔍 Filtros")
        if not df.empty:
            filtro_lab = st.sidebar.selectbox("📍 Laboratorio:", list(st.session_state.db_laboratorios.keys()))
            lista_equipos_real = st.session_state.db_laboratorios[filtro_lab]
            df_filtrado = df[df["Ubicación"] == filtro_lab]
        else:
            st.warning("Inventario vacío.")
            return

        tab_tabla, tab_detalle, tab_alta = st.tabs(["📋 Inventario", "⚙️ Gestión & IA", "➕ Alta"])

        with tab_tabla:
            c1, c2 = st.columns(2)
            c1.metric("Equipos en Lab", len(df_filtrado))
            criticos = len(df_filtrado[df_filtrado["Análisis del Sistema"].str.contains("🔴|🟠|⚠️")])
            c2.metric("En Alerta", criticos, delta_color="inverse")
            st.dataframe(df_filtrado.drop(columns=["OBJ_REF"]), use_container_width=True, hide_index=True)

        with tab_detalle:
            st.subheader(f"Gestión Técnica - {filtro_lab}")
            if lista_equipos_real:
                # Selección por índice para evitar pérdida de referencia
                idx_sel = st.selectbox("Seleccionar Equipo:", range(len(lista_equipos_real)), 
                                     format_func=lambda i: f"{lista_equipos_real[i].modelo} ({lista_equipos_real[i].id_activo})")
                equipo_sel = lista_equipos_real[idx_sel]
                
                col_izq, col_der = st.columns([1, 1])
                
                with col_izq:
                    st.info(f"**Estado:** {equipo_sel.estado.value}")
                    
                    # --- BLOQUE IA ---
                    st.markdown("#### 🤖 Inspección IA")
                    archivo_ia = st.file_uploader("Evidencia visual:", type=['jpg', 'png'], key=f"ia_{equipo_sel.id_activo}")
                    if archivo_ia and st.button("Analizar con VisionService", type="primary"):
                        vision = VisionService()
                        res = vision.analizar_quemadura(archivo_ia)
                        nuevo_reporte = {
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "detalle": f"Inspección Visual: {res['alerta']}",
                            "dictamen_ia": res['diagnostico']
                        }
                        equipo_sel.historial_incidencias.append(nuevo_reporte)
                        if res.get('es_critico'): equipo_sel.estado = EstadoEquipo.DE_BAJA
                        
                        # Guardado explícito
                        st.session_state.db_laboratorios[filtro_lab][idx_sel] = equipo_sel
                        st.cache_data.clear()
                        st.rerun()

                    st.markdown("---")
                    
                    # --- BLOQUE ESTRATEGIA ---
                    st.markdown("#### 🧠 Estrategia de Desgaste")
                    est_actual = type(getattr(equipo_sel, 'estrategia_desgaste', equipo_sel)).__name__
                    nueva_opcion = st.radio("Cambiar Algoritmo:", ["Lineal", "Exponencial"], 
                                          index=0 if "Lineal" in est_actual else 1, horizontal=True)
                    
                    if st.button("🔄 Aplicar y Guardar"):
                        est_obj = st.session_state.est_lineal if nueva_opcion == "Lineal" else st.session_state.est_expo
                        equipo_sel.cambiar_estrategia(est_obj)
                        
                        # Guardado explícito en session_state para que no se pierda
                        st.session_state.db_laboratorios[filtro_lab][idx_sel] = equipo_sel
                        
                        st.cache_data.clear()
                        st.toast(f"Estrategia {nueva_opcion} aplicada")
                        time.sleep(0.5)
                        st.rerun()

                with col_der:
                    obs = equipo_sel.calcular_obsolescencia()
                    st.metric("Desgaste Actual", f"{obs*100:.2f}%")
                    st.progress(min(obs, 1.0))
                    st.caption(f"Motor de cálculo: `{type(getattr(equipo_sel, 'estrategia_desgaste', 'No definida')).__name__}`")

                    with st.expander("Ver Historial", expanded=True):
                        if equipo_sel.historial_incidencias:
                            for inc in equipo_sel.historial_incidencias:
                                st.caption(f"📅 {inc['fecha']}")
                                st.write(f"📝 {inc['detalle']}")
                                if 'dictamen_ia' in inc: st.code(inc['dictamen_ia'], language="text")
                                st.divider()
                        else: st.write("Sin reportes.")
                    
                    if st.button("📄 Generar PDF"):
                        pdf_bytes = generar_pdf(equipo_sel, filtro_lab)
                        st.download_button("⬇️ Descargar Reporte", pdf_bytes, f"Reporte_{equipo_sel.id_activo}.pdf")

        with tab_alta:
            st.subheader("Registrar Nuevo Activo")
            with st.form("form_alta"):
                tipo = st.selectbox("Tipo", ["Motor", "Osciloscopio", "Multimetro"])
                mod = st.text_input("Modelo")
                f_compra = st.date_input("Fecha", datetime.today())
                if st.form_submit_button("💾 Guardar"):
                    n_id = f"EQ-{random.randint(1000, 9999)}"
                    f_str = f_compra.strftime("%Y-%m-%d")
                    if tipo == "Motor": new = MotorInduccion(n_id, mod, f_str, "10HP", "220V", 1800, st.session_state.est_lineal)
                    elif tipo == "Osciloscopio": new = Osciloscopio(n_id, mod, f_str, "100MHz", st.session_state.est_lineal)
                    else: new = Multimetro(n_id, mod, f_str, "0.5%", True, st.session_state.est_lineal)
                    
                    st.session_state.db_laboratorios[filtro_lab].append(new)
                    st.cache_data.clear()
                    st.rerun()