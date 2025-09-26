"""
Este archivo esta pensado para contener la lógica que responde a las peticiones de los usuarios.
En este caso, incluye una vista para simular la creación y encolado
de nuevos pedidos para ser procesados por el sistema de tareas asíncronas.
"""

from django.http import JsonResponse
from .tasks import procesar_pedido_completo
import random
import time

# --- Fuentes de Datos para Simulación ---
# Estas listas actúan como nuestra "base de datos" de clientes y productos
# para generar datos de prueba aleatorios y realistas.
CLIENTES_POSIBLES = ["ACME Corp", "Stark Industries", "Wayne Enterprises", "Cyberdyne Systems", "OsCorp"]
SKUS_VALIDOS = ["P001", "P002", "P003", "P004", "P008", "P015", "P020"]
SKUS_INVALIDOS = ["P999", "P888", "INVALID_SKU"]


def iniciar_procesamiento(request):
    """
    Simula la llegada de nuevos pedidos y los encola para su procesamiento.

    Esta vista actúa como un generador de pedidos. Cada vez que se accede a su URL,
    genera una tanda de pedidos con datos aleatorios y los envía a la cola de Huey.
    Algunos pedidos se crean intencionalmente con datos inválidos para demostrar
    el manejo de errores del worker.

    Args:
        request: El objeto HttpRequest de Django.

    Returns:
        JsonResponse: Una respuesta JSON que confirma la cantidad de tareas encoladas
                      y los IDs de los pedidos generados.
    """
    pedidos_a_generar = 10
    pedidos_encolados = []

    for i in range(pedidos_a_generar):
        # Para asegurar que cada pedido sea único en cada ejecución, generamos un ID
        # basado en el timestamp actual en milisegundos, añadiendo el índice del bucle
        # para evitar colisiones si se generan muy rápido.
        pedido_id = int(time.time() * 1000) + i
        cliente = random.choice(CLIENTES_POSIBLES)
        num_productos = random.randint(1, 3)
        productos = []

        for _ in range(num_productos):
            # Introducimos un 20% de probabilidad de generar un SKU inválido.
            # Esto nos permite probar  cómo el worker maneja errores de enriquecimiento
            # cuando un producto no se encuentra en la API externa.
            es_valido = random.random() < 0.8  # 80% de probabilidad de ser True
            sku = random.choice(SKUS_VALIDOS) if es_valido else random.choice(SKUS_INVALIDOS)
            cantidad = random.randint(1, 5)
            productos.append({"sku": sku, "cantidad": cantidad})
        
        # Forzamos la creación de un pedido inválido (sin productos) cada 5 iteraciones.
        # Esto sirve para probar la etapa de validación inicial dentro de la tarea.
        if i % 5 == 0:
            productos = []

        # Ensamblamos el diccionario final del pedido.
        pedido = {
            "id": pedido_id,
            "cliente": cliente,
            "productos": productos
        }
        
        # --- Encolar la Tarea ---
        # Aquí es donde encola las tareas de manera asíncrona. Al llamar a la función decorada
        # con @task, no la ejecutamos directamente. En su lugar, Huey la serializa
        # y la pone en la cola (la base de datos huey.db) para que un worker
        # la procese en segundo plano. La vista no espera y responde al usuario al instante.
        procesar_pedido_completo(pedido)
        pedidos_encolados.append(pedido_id)

    # Devolvemos una respuesta inmediata al usuario, confirmando que los pedidos
    # han sido recibidos y están siendo procesados.
    return JsonResponse({
        "status": "ok", 
        "message": f"{len(pedidos_encolados)} pedidos dinámicos han sido encolados.",
        "ids_encolados": pedidos_encolados
    })