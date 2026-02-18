import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime
from fpdf import FPDF

# --- IMPORTS PROPIOS ---
from src.views.base_view import Vista 
# Importamos la clase base Equipo para poder crear el genérico
from src.models.equipo import Equipo 
from src.models.concretos import MotorInduccion, Osciloscopio, Multimetro
from src.logical.estrategias import DesgasteLineal, DesgasteExponencial
from src.repositories.equipo_repository import EquipoRepository 
from src.utils.enums import EstadoEquipo
from src.services.vision_service import VisionService

# ==============================================================================
# 0. CLASE PARA EQUIPOS GENÉRICOS (Flexibilidad Total)
# ==============================================================================
class EquipoGenerico(Equipo):
    """Clase comodín para registrar equipos que no son Motores, Osciloscopios o Multímetros."""
    def __init__(self, id_activo, modelo, fecha_compra, descripcion, estrategia_desgaste):
        super().__init__(id_activo, modelo, fecha_compra, estrategia_desgaste)
        self.descripcion = descripcion
        # Asumimos valores por defecto para atributos que no aplican
        self.detalles_tecnicos = {"descripcion": descripcion}

# ==============================================================================
# 1. ZONA DE UTILIDADES (SEMÁFORO Y PDF)
# ==============================================================================

def obtener_comentario_estado(obs_val, estado_str):
    """Genera una recomendación basada en el valor numérico y el estado."""
    est_upper = str(estado_str).upper()
    
    if any(palabra in est_upper for palabra in ["MANTENIMIENTO", "FALLA", "REPORTADO", "BAJA"]):
        return "⚠️ ATENCIÓN: Equipo fuera de servicio. Revisar dictamen IA."
    
    if obs_val < 0.2: return "✅ Óptimas condiciones. Uso estándar."
    elif obs_val < 0.5: return "🟡 Desgaste moderado. Inspección preventiva."
    elif obs_val < 0.8: return "🟠 Desgaste avanzado. Programar mantenimiento."
    else: return "🔴 CRÍTICO: Riesgo inminente. Evaluar reemplazo."

@st.cache_data
def convertir_objetos_a_df(_lista_equipos_dict, _trigger): 
    data = []
    if not _lista_equipos_dict: return pd.DataFrame()

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
                "Desgaste (%)": f"{obs_num * 100:.2f}%", 
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
    pdf.cell(0, 8, f"Tipo: {type(equipo).__name__}", 0, 1)
    
    desgaste = equipo.calcular_obsolescencia()
    porc = desgaste * 100
    
    if porc < 40: 
        color = (200, 255, 200)
        msg = "Estado Optimo."
    elif porc < 70: 
        color = (255, 255, 200)
        msg = "Precaucion: Desgaste detectado."
    else: 
        color = (255, 200, 200)
        msg = "Estado Critico: Evaluar reemplazo."

    pdf.ln(5)
    pdf.set_fill_color(*color)
    pdf.cell(0, 12, f"NIVEL DE DESGASTE: {porc:.2f}% - {msg}", 1, 1, 'C', fill=True)

    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "HISTORIAL DE INCIDENCIAS", 0, 1)
    pdf.set_font('Arial', '', 10)
    
    if not equipo.historial_incidencias:
        pdf.cell(0, 10, "Sin registros.", 0, 1)
    else:
        for inc in equipo.historial_incidencias:
            pdf.ln(2)
            fecha = inc.get('fecha', 'S/F')
            detalle = limpiar_texto(inc.get('detalle', ''))
            dictamen = limpiar_texto(inc.get('dictamen_ia', ''))
            
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 6, f"FECHA: {fecha}", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.multi_cell(0, 5, f"Reporte: {detalle}")
            if dictamen:
                pdf.set_font('Arial', 'I', 9)
                pdf.multi_cell(0, 5, f"IA Note: {dictamen}")

    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 2. VISTA DASHBOARD
# ==============================================================================

class VistaDashboard(Vista):
    
    def _cargar_y_agrupar_desde_supabase(self):
        """Descarga de Supabase y DISTRIBUYE INTELIGENTEMENTE (Incluye Genéricos)."""
        repo = EquipoRepository()
        datos_raw = repo.leer_todos()
        
        laboratorios_dict = {
            "Laboratorio de Control": [],
            "Laboratorio de Circuitos": [],
            "Laboratorio de Máquinas": [],
            "Laboratorio de Telecom": []
        } 
        
        est_lineal = st.session_state.get('est_lineal', DesgasteLineal())
        est_expo = st.session_state.get('est_expo', DesgasteExponencial())

        for d in datos_raw:
            try:
                tipo = d.get('tipo_equipo', 'Equipo')
                ubicacion_original = d.get('ubicacion', 'Laboratorio FIEE')
                modelo = d.get('modelo', 'Desconocido')
                id_act = d.get('id_activo', '000')
                fecha = d.get('fecha_compra', '2024-01-01')
                detalles = d.get('detalles_tecnicos', {}) or {}
                
                # --- AUTO-DISTRIBUCIÓN ---
                if ubicacion_original == "Laboratorio FIEE":
                    if "Motor" in tipo: ubicacion = "Laboratorio de Máquinas"
                    elif "Osciloscopio" in tipo: ubicacion = "Laboratorio de Circuitos"
                    elif "Multimetro" in tipo: ubicacion = "Laboratorio de Control"
                    else: ubicacion = "Laboratorio de Telecom" # Genéricos van aquí por defecto si no se especifica
                else:
                    ubicacion = ubicacion_original
                
                # Instanciación de Estrategia
                est_nombre = d.get('estrategia_nombre', 'Lineal')
                estrategia = est_expo if "Exponencial" in est_nombre else est_lineal
   
                # --- INSTANCIACIÓN DE OBJETOS ---
                nuevo_obj = None
   
                if "Motor" in tipo:
                    nuevo_obj = MotorInduccion(id_act, modelo, fecha, 
                                             detalles.get('hp', '5HP'), detalles.get('voltaje', '220V'), 
                                             detalles.get('rpm', 1800), estrategia)
                elif "Osciloscopio" in tipo:
                    nuevo_obj = Osciloscopio(id_act, modelo, fecha, detalles.get('ancho_banda', '50MHz'), estrategia)
                elif "Multimetro" in tipo:
                    nuevo_obj = Multimetro(id_act, modelo, fecha, detalles.get('precision', '1%'), True, estrategia)
                else:
                    # CASO GENÉRICO: Para todo lo que no sea lo anterior
                    desc = detalles.get('descripcion', 'Equipo Diverso')
                    nuevo_obj = EquipoGenerico(id_act, modelo, fecha, desc, estrategia)

                # Asignación final
                if nuevo_obj:
                    nuevo_obj.historial_incidencias = d.get('historial_incidencias', [])
                    estado_str = d.get('estado', 'OPERATIVO')
                    if hasattr(EstadoEquipo, estado_str):
                        nuevo_obj.estado = getattr(EstadoEquipo, estado_str)
                    
                    nuevo_obj.ubicacion = ubicacion 

                    if ubicacion in laboratorios_dict:
                        laboratorios_dict[ubicacion].append(nuevo_obj)
                    else:
                        if ubicacion not in laboratorios_dict:
                            laboratorios_dict[ubicacion] = []
                        laboratorios_dict[ubicacion].append(nuevo_obj)
            
            except Exception as e:
                print(f"Error procesando equipo {d.get('id_activo')}: {e}")
                continue
                
        return laboratorios_dict

    def render(self):
        st.title("📊 Dashboard de Activos FIEE")
        st.markdown("---")

        if 'trigger' not in st.session_state: st.session_state.trigger = 0
        if 'est_lineal' not in st.session_state: st.session_state.est_lineal = DesgasteLineal()
        if 'est_expo' not in st.session_state: st.session_state.est_expo = DesgasteExponencial()

        # Carga Blindada
        if ('db_laboratorios' not in st.session_state or 
            st.session_state.trigger > 0 or 
            not isinstance(st.session_state.db_laboratorios, dict)):
            st.session_state.db_laboratorios = self._cargar_y_agrupar_desde_supabase()
            st.session_state.trigger = 0 

        # --- SIDEBAR ---
        st.sidebar.header("🔍 Filtros")
        lista_labs_disponibles = list(st.session_state.db_laboratorios.keys())
        
        if lista_labs_disponibles:
            filtro_lab = st.sidebar.selectbox("📍 Seleccione Laboratorio:", lista_labs_disponibles)
            lista_equipos_real = st.session_state.db_laboratorios[filtro_lab]
            df_global = convertir_objetos_a_df(st.session_state.db_laboratorios, st.session_state.trigger)
            if not df_global.empty:
                df_filtrado = df_global[df_global["Ubicación"] == filtro_lab]
            else:
                df_filtrado = pd.DataFrame()
        else:
            st.sidebar.warning("No hay laboratorios.")
            filtro_lab = None
            lista_equipos_real = []
            df_filtrado = pd.DataFrame()

        # --- PESTAÑAS ---
        # Renombré "Alta" a "Alta Inventario" para diferenciar de resolver incidencias
        tab_tabla, tab_detalle, tab_alta = st.tabs(["📋 Inventario", "⚙️ Gestión & IA", "➕ Alta Inventario"])

        with tab_tabla:
            if not df_filtrado.empty:
                c1, c2 = st.columns(2)
                c1.metric(f"Equipos en {filtro_lab}", len(df_filtrado))
                criticos = len(df_filtrado[df_filtrado["Análisis del Sistema"].str.contains("🔴|🟠|⚠️")])
                c2.metric("Atención Requerida", criticos, delta_color="inverse")
                st.dataframe(df_filtrado.drop(columns=["OBJ_REF"]), use_container_width=True, hide_index=True)
            else:
                st.info(f"El **{filtro_lab}** no tiene equipos registrados actualmente.")

        with tab_detalle:
            if filtro_lab and lista_equipos_real:
                st.subheader(f"Gestión Técnica - {filtro_lab}")
                idx_sel = st.selectbox("Seleccionar Equipo:", range(len(lista_equipos_real)),
                                     format_func=lambda i: f"{lista_equipos_real[i].modelo} ({lista_equipos_real[i].id_activo})")
                equipo_sel = lista_equipos_real[idx_sel]
                
                col_izq, col_der = st.columns([1, 1])

                with col_izq:
                    st.info(f"**Estado:** {equipo_sel.estado.name if hasattr(equipo_sel.estado, 'name') else str(equipo_sel.estado)}")
                    
                    st.markdown("#### 🤖 Inspección IA")
                    archivo_ia = st.file_uploader("Subir evidencia visual:", type=['jpg', 'png'], key=f"ia_{equipo_sel.id_activo}")
                    
                    if archivo_ia and st.button("Analizar Daño", type="primary"):
                        vision = VisionService()
                        res = vision.analizar_quemadura(archivo_ia)
                        
                        nuevo_reporte = {
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "detalle": f"Inspección Visual: {res['alerta']}",
                            "dictamen_ia": res['diagnostico']
                        }
                        equipo_sel.historial_incidencias.append(nuevo_reporte)
                        
                        if res.get('es_critico'): 
                            equipo_sel.estado = EstadoEquipo.BAJA
                        
                        repo = EquipoRepository()
                        repo.actualizar_equipo(equipo_sel)
                        st.session_state.trigger = 1
                        st.rerun()

                    st.markdown("---")
                    st.markdown("#### 🧠 Estrategia")
                    est_actual = type(equipo_sel.estrategia_desgaste).__name__
                    st.write(f"Algoritmo: **{est_actual}**")
                    if st.button("Cambiar Algoritmo"):
                        if "Lineal" in est_actual: equipo_sel.cambiar_estrategia(st.session_state.est_expo)
                        else: equipo_sel.cambiar_estrategia(st.session_state.est_lineal)
                        EquipoRepository().actualizar_equipo(equipo_sel)
                        st.session_state.trigger = 1
                        st.rerun()

                with col_der:
                    obs = equipo_sel.calcular_obsolescencia()
                    st.metric("Desgaste Actual", f"{obs*100:.2f}%")
                    st.progress(min(obs, 1.0))
                    
                    with st.expander("Ver Historial", expanded=True):
                        if equipo_sel.historial_incidencias:
                            for inc in equipo_sel.historial_incidencias:
                                st.caption(f"📅 {inc.get('fecha', '?')}")
                                st.write(f"📝 {inc.get('detalle', '')}")
                                if 'dictamen_ia' in inc: st.code(inc['dictamen_ia'], language="text")
                                st.divider()
                        else: st.write("Sin reportes.")
                    
                    if st.button("📄 Generar PDF Oficial"):
                        pdf_bytes = generar_pdf(equipo_sel, filtro_lab)
                        st.download_button("⬇️ Descargar Reporte", pdf_bytes, f"Reporte_{equipo_sel.id_activo}.pdf")
            else:
                st.warning("No hay equipos seleccionables.")

        # PESTAÑA 3: ALTA DE EQUIPOS (MEJORADA Y FLEXIBLE)
        with tab_alta:
            st.subheader("➕ Registrar Nuevo Activo al Inventario")
            st.caption("Seleccione primero el laboratorio para ver los equipos permitidos.")
            
            # NOTA: Quitamos el st.form principal para permitir que la interactividad 
            # (cambiar laboratorio -> cambiar lista) funcione instantáneamente sin botón de recarga.
            
            col_lab, col_tipo = st.columns(2)
            
            # 1. SELECCIÓN DE LABORATORIO
            with col_lab:
                lab_destino = st.selectbox("📍 Laboratorio de Destino", 
                                         ["Laboratorio de Control", 
                                          "Laboratorio de Circuitos", 
                                          "Laboratorio de Máquinas", 
                                          "Laboratorio de Telecom"])
            
            # 2. LÓGICA DE FILTRADO (ESTRICTA)
            # Definimos qué equipos pertenecen EXCLUSIVAMENTE a cada lab
            opciones_validas = []
            
            if lab_destino == "Laboratorio de Máquinas":
                opciones_validas = ["MotorInduccion"]
            elif lab_destino == "Laboratorio de Circuitos":
                opciones_validas = ["Osciloscopio"]   # <--- Solo Osciloscopio aquí
            elif lab_destino == "Laboratorio de Control":
                opciones_validas = ["Multimetro"]     # <--- Solo Multímetro aquí
            else:
                opciones_validas = []                 # Telecom u otros

            # Siempre añadimos la opción genérica al final
            opciones_validas.append("Otro / Genérico")

            # 3. SELECTOR DE TIPO (CON TRUCO "KEY")
            with col_tipo:
                # El parámetro 'key' hace que este widget sea único para cada lab. 
                # Al cambiar de lab, este widget se destruye y se crea uno nuevo limpio (índice 0).
                tipo_seleccion = st.selectbox("📦 Clase de Equipo", 
                                            opciones_validas, 
                                            key=f"select_tipo_{lab_destino}")

            st.markdown("---")
            
            # 4. FORMULARIO DE DETALLES (Ahora sí usamos form para agrupar los datos)
            with st.form("form_alta_detalles"):
                col_det1, col_det2 = st.columns(2)
                
                with col_det1:
                    mod = st.text_input("Modelo / Marca")
                    f_compra = st.date_input("Fecha Adquisición", datetime.today())
                
                with col_det2:
                    if tipo_seleccion == "Otro / Genérico":
                        tipo_manual = st.text_input("Especifique el Tipo (Ej. Fuente, PLC):")
                        detalle_extra = st.text_area("Descripción Técnica:")
                    else:
                        tipo_manual = tipo_seleccion 
                        detalle_extra = ""
                        st.info(f"✅ Configuración predefinida para: **{tipo_seleccion}**")

                # BOTÓN DE GUARDADO
                if st.form_submit_button("💾 Guardar en Base de Datos"):
                    n_id = f"EQ-{random.randint(1000, 9999)}"
                    f_str = f_compra.strftime("%Y-%m-%d")
                    new = None
                    
                    # Lógica de Instanciación
                    if tipo_seleccion == "MotorInduccion":
                        new = MotorInduccion(n_id, mod, f_str, "10HP", "220V", 1800, st.session_state.est_lineal)
                    elif tipo_seleccion == "Osciloscopio":
                        new = Osciloscopio(n_id, mod, f_str, "100MHz", st.session_state.est_lineal)
                    elif tipo_seleccion == "Multimetro":
                        new = Multimetro(n_id, mod, f_str, "0.5%", True, st.session_state.est_lineal)
                    else:
                        # Genérico
                        nombre_final = tipo_manual if tipo_manual else "Equipo Genérico"
                        new = EquipoGenerico(n_id, mod, f_str, detalle_extra, st.session_state.est_lineal)

                    if new:
                        new.ubicacion = lab_destino
                        repo = EquipoRepository()
                        repo.guardar_equipo(new)
                        
                        st.success(f"✅ Registrado: {tipo_manual} en {lab_destino}")
                        st.session_state.trigger = 1
                        time.sleep(1.5)
                        st.rerun()