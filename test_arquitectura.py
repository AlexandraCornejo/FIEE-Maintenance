import sys
import os

# TRUCO DE INGENIERA: 
# Agregamos la ruta actual al sistema para que Python encuentre la carpeta 'src'
sys.path.append(os.getcwd())

from src.models.concretos import Osciloscopio, Multimetro, MotorInduccion
from src.utils.enums import EstadoEquipo # Importamos para poder comparar

def probar_logica_negocio():
    print("--- 🏗️ TEST ROL A: LÓGICA DE NEGOCIO ---")

    # 1. Crear la flota
    print("1. Creando equipos...")
    osc = Osciloscopio("OSC-01", "Tektronix", "2023-01-01", "100MHz")
    multi = Multimetro("MUL-01", "Fluke 87V", "2024-02-01", "0.01%", True)
    motor = MotorInduccion("MOT-01", "Siemens", "2020-05-20", "10HP", "440V", 3600)

    lista_equipos = [osc, multi, motor]

    # 2. Probar Polimorfismo
    print(f"\n{'MODELO':<15} | {'OBSOLESCENCIA':<15} | {'QR'}")
    print("-" * 60)
    for eq in lista_equipos:
        obs = eq.calcular_obsolescencia()
        # Generamos QR y manejamos el caso si devuelve string o print
        qr_resultado = eq.generar_qr()
        print(f"{eq.modelo:<15} | {obs*100:>5.1f}%          | {qr_resultado}")

    # 3. Probar Sistema de Incidencias
    print("\n--- ⚠️ PROBANDO REPORTE DE FALLAS ---")
    print(f"Estado original Motor: {motor.estado.value}")
    
    # Aquí probamos que cambie al estado correcto
    motor.registrar_incidencia("Rodamiento con ruido excesivo", "Ing. Ale")
    
    print(f"Nuevo estado Motor:    {motor.estado.value}")
    
    # Verificación automática
    if motor.estado == EstadoEquipo.REPORTADO_CON_FALLA:
        print("✅ ÉXITO: El estado cambió correctamente en memoria.")
    else:
        print("❌ ERROR: El estado no cambió como se esperaba.")

if __name__ == "__main__":
    probar_logica_negocio()