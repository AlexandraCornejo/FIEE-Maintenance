import cv2
import numpy as np

class VisionService:
    def analizar_quemadura(self, image_path_or_buffer):
        """
        Versión V2: Detecta porcentaje de oscuridad en lugar de promedio simple.
        Ideal para detectar objetos negros aunque el fondo sea claro.
        """
        try:
            # 1. Cargar la imagen
            if hasattr(image_path_or_buffer, 'read'): 
                file_bytes = np.asarray(bytearray(image_path_or_buffer.read()), dtype=np.uint8)
                img = cv2.imdecode(file_bytes, 1)
            else:
                img = cv2.imread(image_path_or_buffer)

            if img is None:
                return {"alerta": "ERROR", "diagnostico": "Img corrupta", "brillo_detectado": 0}

            # 2. Convertir a Gris
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 3. Lógica V2: CONTAR PÍXELES NEGROS
            # Definimos "Negro" como cualquier píxel con valor menor a 60 (0 es negro puro)
            umbral_oscuridad = 60
            
            # Contamos cuántos píxeles son así de oscuros
            pixeles_totales = gray.size
            pixeles_oscuros = np.count_nonzero(gray < umbral_oscuridad)
            
            # Calculamos el porcentaje de oscuridad en la foto
            porcentaje_quemado = (pixeles_oscuros / pixeles_totales) * 100

            # --- DIAGNÓSTICO ---
            # Si más del 10% de la imagen es "negra", asumimos quemadura/carbonización
            if porcentaje_quemado > 10.0:
                return {
                    "alerta": "🚨 ALERTA CRÍTICA",
                    "diagnostico": f"Zona CARBONIZADA detectada ({porcentaje_quemado:.1f}% de área afectada).",
                    "brillo_detectado": f"Área oscura: {porcentaje_quemado:.1f}%"
                }
            else:
                return {
                    "alerta": "✅ OK",
                    "diagnostico": "Superficie dentro de parámetros normales.",
                    "brillo_detectado": f"Área oscura: {porcentaje_quemado:.1f}%"
                }

        except Exception as e:
            return {"alerta": "ERROR", "diagnostico": f"Fallo IA: {str(e)}", "brillo_detectado": 0}
