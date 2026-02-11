from src.models.equipo import Equipo
from src.logical.estrategias import DesgasteLineal, DesgasteExponencial

def ejecutar_prueba_hito4():
    print("="*40)
    print("🚀 VALIDACIÓN ENTREGABLE 3: PATRÓN STRATEGY")
    print("="*40)

    # Definimos una fecha de compra común (hace 5 años)
    fecha_test = "2021-01-01"

    # 1. Creamos un equipo con Estrategia LINEAL (Mecánico)
    # Hito 3: Inyección por constructor
    equipo_fisico = Equipo("F-001", "Motor Industrial", fecha_test, DesgasteLineal())

    # 2. Creamos un equipo con Estrategia EXPONENCIAL (Electrónico)
    equipo_digital = Equipo("E-999", "Servidor de Datos", fecha_test, DesgasteExponencial())

    # Calculamos resultados
    resultado_lineal = equipo_fisico.calcular_obsolescencia()
    resultado_expo = equipo_digital.calcular_obsolescencia()

    print(f"📊 Equipo Físico (Lineal):      Índice {resultado_lineal}")
    print(f"📊 Equipo Digital (Exponencial): Índice {resultado_expo}")
    print("-" * 40)

    # Verificación del Hito 4: Los resultados DEBEN ser diferentes
    if resultado_lineal != resultado_expo:
        print("✅ HITO 4 CUMPLIDO: Los comportamientos son diferentes")
        print("   para equipos del mismo año. El patrón Strategy funciona.")
    else:
        print("❌ ERROR: Los resultados son iguales. Revisa las fórmulas.")
    print("="*40)

if __name__ == "__main__":
    ejecutar_prueba_hito4()