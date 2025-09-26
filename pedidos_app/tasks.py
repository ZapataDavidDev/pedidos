"""
Módulo de tareas asíncronas para el procesamiento de pedidos.

Define la lógica de negocio principal que se ejecuta en segundo plano
a través de un worker de Huey, asegurando la ejecucion asincrona de las tareas.
"""

import hashlib
import json
import logging
import requests
import socket
from typing import Dict, Any
from django.utils import timezone

from huey.contrib.djhuey import task
from .models import PedidoProcesado, TaskHistory

# Define constantes a nivel de módulo para una fácil configuración y legibilidad.
API_BASE_URL = "https://fakestoreapi.com"
UMBRAL_DESCUENTO = 500.0
PORCENTAJE_DESCUENTO = 0.10

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@task(retries=2, retry_delay=10, context=True)
def procesar_pedido_completo(pedido_data: Dict[str, Any], task=None):
    """
    Orquesta el flujo completo de procesamiento de un pedido de forma asíncrona.

    Esta tarea es idempotente y resiliente, gestionando su propio historial de
    ejecución y manejando reintentos en caso de fallos transitorios.

    Args:
        pedido_data: Payload del pedido a procesar.
        task (huey.api.Task, optional): Instancia de la tarea inyectada por Huey
                                        para acceder a metadatos de ejecución.
    """
    order_id = pedido_data.get('id')
    
    # Crea un nuevo registro en el historial de tareas caso de reintentos actualiza los datos para garantizar unicidad.
    history_entry, created = TaskHistory.objects.update_or_create(
        task_id=task.id,
        defaults={
            'task_name': task.name,
            'status': TaskHistory.Status.STARTED,
            'worker_hostname': socket.gethostname()
        }
    )

    # Si es un reintento, resetea el estado para reflejar la nueva ejecución.
    if not created:
        history_entry.status = TaskHistory.Status.STARTED
        history_entry.error_message = None
        history_entry.start_time = timezone.now()
        history_entry.end_time = None
        history_entry.save()

    pedido_procesado_obj = None
    try:
        # --- ETAPA A: VALIDACIÓN DE LA ESTRUCTURA DEL PEDIDO ---
        if not all(key in pedido_data for key in ["id", "cliente", "productos"]):
            raise ValueError("Payload del pedido incompleto: faltan claves principales.")
        if not isinstance(pedido_data["productos"], list) or not pedido_data["productos"]:
            raise ValueError("La lista de productos está vacía o no es válida.")

        # --- ETAPA B: ENRIQUECIMIENTO DE DATOS VÍA API EXTERNA ---
        enriched_products = []
        for producto in pedido_data["productos"]:
            sku = producto.get("sku")
            product_id = "".join(filter(str.isdigit, sku)) if sku else None
            if not product_id: continue

            response = requests.get(f"{API_BASE_URL}/products/{product_id}", timeout=10)
            
            if response.status_code == 200 and response.text and response.json():
                api_data = response.json()
                enriched_products.append({
                    "sku": sku, "cantidad": producto["cantidad"],
                    "title": api_data.get("title"), "precio_unitario_api": float(api_data.get("price")),
                })
        
        if not enriched_products:
            raise ValueError("No se pudo enriquecer ningún producto válido para el pedido.")
        
        # --- ETAPA C: APLICACIÓN DE LÓGICA DE NEGOCIO ---
        subtotal = sum(p["cantidad"] * p["precio_unitario_api"] for p in enriched_products)
        descuento = subtotal * PORCENTAJE_DESCUENTO if subtotal > UMBRAL_DESCUENTO else 0.0
        total_final = subtotal - descuento
        
        # Genera un hash para verificar la integridad del procesamiento.
        hash_str = json.dumps({"pedido": pedido_data, "enriquecido": enriched_products}, sort_keys=True)
        pedido_hash = hashlib.sha256(hash_str.encode()).hexdigest()

        # --- ETAPA D: PERSISTENCIA DEL RESULTADO ---
        pedido_procesado_obj, _ = PedidoProcesado.objects.update_or_create(
            id_pedido_original=order_id,
            defaults={
                'hash_pedido': pedido_hash, 'cliente': pedido_data["cliente"],
                'detalle_completo': enriched_products, 'subtotal': round(subtotal, 2),
                'descuento': round(descuento, 2), 'total_final': round(total_final, 2),
            }
        )
        
        # Marca la auditoría como exitosa.
        history_entry.status = TaskHistory.Status.SUCCESS

    except Exception as e:
        # Captura cualquier error durante el flujo para registrarlo.
        history_entry.status = TaskHistory.Status.ERROR
        history_entry.error_message = str(e)[:500]
        raise e # Relanza la excepción para que Huey gestione los reintentos.

    finally:
        # Este bloque se ejecuta siempre, asegurando que el log se actualice.
        history_entry.end_time = timezone.now()
        
        # Si el pedido se procesó, se enlaza con el historial para una trazabilidad completa.
        if pedido_procesado_obj:
            history_entry.pedido = pedido_procesado_obj

        history_entry.save()
        logging.info(f"[Pedido {order_id}] Registro de historial actualizado a estado: {history_entry.status}")