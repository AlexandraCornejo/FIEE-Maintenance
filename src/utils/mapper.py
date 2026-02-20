from src.models.concretos import MotorInduccion, Osciloscopio, Multimetro
from src.utils.enums import EstadoEquipo

def map_json_to_object(data_list, estrategia_lineal, estrategia_exponencial):
    """
    Convierte una lista de diccionarios (JSON) a una lista de Objetos Concretos.
    """
    objetos_convertidos = []
    
    for item in data_list:
        tipo = item.get('tipo_equipo')
        detalles = item.get('detalles_tecnicos', {})
        
        # 1. Recuperar estrategia
        nombre_est = item.get('estrategia_nombre', 'Lineal')
        est_obj = estrategia_lineal if 'Lineal' in nombre_est else estrategia_exponencial
        
        # 2. Instanciar la clase concreta
        nuevo_obj = None 
        
        try:
            if tipo == 'MotorInduccion':
                nuevo_obj = MotorInduccion(
                    item['id_activo'], item['modelo'], item['fecha_compra'], 
                    detalles.get('hp'), detalles.get('voltaje'), detalles.get('rpm'), 
                    est_obj
                )
            elif tipo == 'Osciloscopio':
                nuevo_obj = Osciloscopio(
                    item['id_activo'], item['modelo'], item['fecha_compra'], 
                    detalles.get('ancho_banda'), est_obj
                )
            elif tipo == 'Multimetro':
                nuevo_obj = Multimetro(
                    item['id_activo'], item['modelo'], item['fecha_compra'], 
                    detalles.get('precision'), detalles.get('es_digital', True), est_obj
                )
            
            # 3. Si se creó correctamente, llenar datos comunes
            if nuevo_obj:
                nuevo_obj.ubicacion = item.get('ubicacion', 'Sin Asignar') # IMPORTANTE PARA EL DASHBOARD
                
                # Convertir string a Enum de forma segura
                estado_str = item.get('estado', 'OPERATIVO')
                if hasattr(EstadoEquipo, estado_str):
                    nuevo_obj.estado = getattr(EstadoEquipo, estado_str)
                
                nuevo_obj.historial_incidencias = item.get('historial_incidencias', [])
                objetos_convertidos.append(nuevo_obj)
                
        except Exception as e:
            print(f"Error mapeando objeto {item.get('id_activo')}: {e}")
            continue

    return objetos_convertidos