# src/interfaces/mixins.py

class IdentificableQR:
    def generar_qr(self):
        """Hito 1: Generación de identificador único"""
        return f"QR-{id(self)}"

class AnalizadorPredictivo:
    def predecir_fallo(self):
        """Hito 3: Simulación de probabilidad de falla con IA"""
        return "🔮 IA: Probabilidad de fallo 12%"
