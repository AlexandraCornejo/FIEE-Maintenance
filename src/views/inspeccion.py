import streamlit as st
import time
import os
from src.views.base_view import Vista
from src.utils.enums import EstadoEquipo
from src.repositories.equipo_repository import EquipoRepository # <--- NUEVO

try:
    from src.services.vision_service import VisionService
except ImportError:
    VisionService = None

class VistaInspeccion(Vista):
    def render(self):
        st.header("📲 Inspección Técnica (Estudiante)")
        st.markdown("---")

        # 1. SIMULACIÓN DE ESCANEO QR
        qr_input = st.text_input("🔫 Escanear Código QR (ID del Activo):", placeholder="Ej: MOT-01").strip()

        equipo_encontrado = None
        lab_ubicacion = None

        # Buscamos el equipo en la base de datos global (Ya cargada de Supabase)
        if qr_input and 'db_laboratorios' in st.session_state:
            for lab, lista_equipos in st.session_state.db_laboratorios.items():
                for eq in lista_equipos:
                    if eq.id_activo == qr_input:
                        equipo_encontrado = eq
                        lab_ubicacion = lab
                        break
        
        # 2. SI ENCUENTRA EL EQUIPO -> MUESTRA FICHA TÉCNICA
        if equipo_encontrado:
            st.success(f"✅ Equipo Identificado: {equipo_encontrado.modelo}")
            
            with st.container(border=True):
                c1, c2 = st.columns([1, 3])
                with c1:
                    if "Motor" in type(equipo_encontrado).__name__:
                         st.image("https://cdn-icons-png.flaticon.com/512/3662/3662819.png", width=80)
                    else:
                         st.image("https://cdn-icons-png.flaticon.com/512/9626/9626649.png", width=80)
                
                with c2:
                    st.write(f"**📍 Ubicación:** {lab_ubicacion}")
                    st.write(f"**🚦 Estado:** {equipo_encontrado.estado.value}")
                    obs = equipo_encontrado.calcular_obsolescencia()
                    vida_restante = max(0, 1.0 - obs)
                    st.progress(vida_restante, text=f"Vida Útil Restante: {vida_restante*100:.1f}%")

            st.divider()

            # 3. FORMULARIO DE REPORTE DE AVERÍA
            st.subheader("🚨 Reportar Incidencia")
            
            with st.form("form_reporte"):
                usuario = st.text_input("Tu Nombre / Código:", "Estudiante-01")
                descripcion = st.text_area("Descripción del problema:", placeholder="El equipo hace un ruido extraño...")
                st.write("📸 **Evidencia Visual (Opcional)**")
                col_cam, col_upload = st.columns(2)
                foto_cam = col_cam.camera_input("Tomar Foto")
                foto_upl = col_upload.file_uploader("Subir Imagen", type=["jpg", "png", "jpeg"])
                
                enviar = st.form_submit_button("📢 Enviar Reporte")

                if enviar:
                    if not descripcion:
                        st.warning("⚠️ Por favor describe el problema.")
                    else:
                        foto_final = foto_cam if foto_cam else foto_upl
                        dictamen_ia = "Sin análisis visual."

                        # --- BLOQUE VISIÓN ---
                        if foto_final:
                            with st.spinner("🤖 Analizando imagen con IA..."):
                                time.sleep(1.5)
                                temp_filename = "temp_vision.jpg"
                                with open(temp_filename, "wb") as f: f.write(foto_final.getbuffer())
                                
                                try:
                                    if VisionService:
                                        servicio = VisionService()
                                        if hasattr(servicio, 'analizar_quemadura'):
                                            resultado = servicio.analizar_quemadura(temp_filename)
                                        elif hasattr(servicio, 'analizar_imagen'):
                                            resultado = servicio.analizar_imagen(temp_filename)
                                        else:
                                            resultado = {"diagnostico": "Error de Método", "alerta": False}
                                        
                                        dictamen_ia = f"IA: {resultado.get('diagnostico', 'Desconocido')}"
                                        
                                        if resultado.get('alerta') or "QUEMADURA" in str(resultado):
                                            equipo_encontrado.estado = EstadoEquipo.EN_MANTENIMIENTO
                                            st.error("🚨 ¡LA IA DETECTÓ DAÑO CRÍTICO!")
                                    else:
                                        dictamen_ia = "IA (Simulada): Posible desgaste térmico detectado."
                                
                                except Exception as e:
                                    dictamen_ia = f"Error en IA: {str(e)}"
                                finally:
                                    if os.path.exists(temp_filename): os.remove(temp_filename)

                        # --- GUARDADO ---
                        detalle_log = f"Reportado por {usuario}: {descripcion}"
                        equipo_encontrado.registrar_incidencia(detalle_log)
                        ultimo_ticket = equipo_encontrado.historial_incidencias[-1]
                        ultimo_ticket['dictamen_ia'] = dictamen_ia

                        # --- PERSISTENCIA SUPABASE ---
                        repo = EquipoRepository()
                        repo.actualizar_equipo(equipo_encontrado) # <--- AQUÍ GUARDAMOS

                        st.success("✅ Reporte registrado y guardado en la Nube.")
                        st.session_state.trigger = st.session_state.get('trigger', 0) + 1
                        st.cache_data.clear()
                        
        elif qr_input:
            st.error("❌ Código QR no encontrado en la base de datos.")