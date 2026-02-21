from src.equipo_factory import EquipoFactory
from src.utils.enums import EstadoEquipo


def map_json_to_object(data_list, estrategia_lineal, estrategia_exponencial):
    """
    Convierte los datos JSON de Supabase en objetos del sistema.
    """
    objetos_convertidos = []

    for item in data_list:
        tipo = item.get("tipo_equipo")
        detalles = item.get("detalles_tecnicos", {})

        # Selección de estrategia
        nombre_est = item.get("estrategia_nombre", "Lineal")
        est_obj = estrategia_lineal if "Lineal" in nombre_est else estrategia_exponencial

        try:
            nuevo_obj = EquipoFactory.crear_equipo(
                tipo,
                item,
                detalles,
                est_obj
            )

            # Datos comunes a todos los equipos
            nuevo_obj.ubicacion = item.get("ubicacion", "Sin Asignar")

            estado_str = item.get("estado", "OPERATIVO")
            if hasattr(EstadoEquipo, estado_str):
                nuevo_obj.estado = getattr(EstadoEquipo, estado_str)

            nuevo_obj.historial_incidencias = item.get("historial_incidencias", [])

            objetos_convertidos.append(nuevo_obj)

        except Exception as e:
            print(f"Error mapeando objeto {item.get('id_activo')}: {e}")

    return objetos_convertidos