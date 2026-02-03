class IdentificableQR:
    def generar_qr(self) -> str:
        codigo= f"QR-{id(self)}"
        return f"📡 [QR SYSTEM] Identificado activo: {codigo}"

class AnalizadorPredictivo:
    def predecir_fallo(self) -> str:
        # Aquí conectaremos Scikit-Learn en la Semana 2
        return "🔮 [IA] Predicción pendiente: Faltan datos históricos."

class InspectorVisual:
    def analizar_foto(self, ruta_imagen: str) -> dict:
        # Aquí conectaremos OpenCV en la Semana 2
        return {"status": "OK", "detalles": "Análisis visual simulado"}