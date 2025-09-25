# pedidos_app/tasks.py

import hashlib
import json
import logging
import requests
from datetime import datetime
from decimal import Decimal, InvalidOperation # Usamos Decimal para precisión financiera

from huey.contrib.djhuey import task
from .models import PedidoProcesado



API_BASE_URL = "https://fakestoreapi.com"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@task(retries=2, retry_delay=10) # Aumentamos el delay para dar tiempo a la API a recuperarse
def procesar_pedido_completo(pedido_data: dict):
    """
    Tarea principal que ejecuta el flujo completo de procesamiento de un pedido
    con validaciones y manejo de errores mejorados.
    """
    order_id = pedido_data.get('id', 'ID_DESCONOCIDO')
    
    # --- ETAPA A: VALIDACIÓN (Mejorada) ---
    logging.info(f"[Pedido {order_id}] Etapa A: Iniciando validación.")
    if not all(key in pedido_data for key in ["id", "cliente", "productos"]):
        logging.error(f"[Pedido {order_id}] Fallo de validación: Faltan claves principales. El pedido será descartado.")
        return # Salimos de la tarea; no tiene sentido reintentar un pedido malformado.
    
    if not isinstance(pedido_data["productos"], list):
        logging.error(f"[Pedido {order_id}] Fallo de validación: El campo 'productos' no es una lista. El pedido será descartado.")
        return
    
    logging.info(f"[Pedido {order_id}] Validación OK.")

    # --- ETAPA B: ENRIQUECIMIENTO (Mejorada) ---
    logging.info(f"[Pedido {order_id}] Etapa B: Iniciando enriquecimiento de productos.")
    enriched_products = []
    for producto in pedido_data["productos"]:
        sku = producto.get("sku")
        if not sku:
            logging.warning(f"[Pedido {order_id}] Producto sin SKU encontrado, será ignorado.")
            continue
        
        try:
            product_id = "".join(filter(str.isdigit, sku))
            if not product_id:
                raise ValueError
        except (ValueError, TypeError):
            logging.warning(f"[Pedido {order_id}] No se pudo extraer un ID numérico del SKU '{sku}'. Producto ignorado.")
            continue

        try:
            response = requests.get(f"{API_BASE_URL}/products/{product_id}", timeout=10)
            
            # Verificamos si la respuesta es exitosa y si contiene datos válidos
            if response.status_code == 200 and response.text:
                api_data = response.json()
                if not api_data: # La API a veces devuelve 'null' con un 200 OK para IDs no encontrados
                     logging.warning(f"[Pedido {order_id}] Producto con SKU {sku} (ID: {product_id}) no encontrado. Respuesta nula.")
                     continue
                
                enriched_products.append({
                    "sku": sku,
                    "cantidad": producto["cantidad"],
                    "title": api_data.get("title"),
                    "category": api_data.get("category"),
                    "precio_unitario_api": str(api_data.get("price")), # Guardamos como string para convertir a Decimal
                })
            else:
                logging.warning(f"[Pedido {order_id}] Producto con SKU {sku} (ID: {product_id}) no encontrado. Status: {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            logging.error(f"[Pedido {order_id}] Error de red al consultar SKU {sku}: {e}. Huey gestionará el reintento.")
            raise e # Relanzamos la excepción para que Huey la capture y reintente la tarea completa

    if not enriched_products:
        logging.warning(f"[Pedido {order_id}] No se pudo enriquecer ningún producto. El pedido no será procesado.")
        return

    logging.info(f"[Pedido {order_id}] Enriquecimiento OK. {len(enriched_products)} productos procesados.")
    
    # --- ETAPA C: CÁLCULOS (Mejorada con Decimal) ---
    logging.info(f"[Pedido {order_id}] Etapa C: Iniciando cálculos.")
    try:
        subtotal = sum(Decimal(p["cantidad"]) * Decimal(p["precio_unitario_api"]) for p in enriched_products)
        
        # Lógica de descuento
        descuento = Decimal('0.0')
        if subtotal > Decimal('500'):
            descuento = subtotal * Decimal('0.10')
            
        total_final = subtotal - descuento
    except InvalidOperation:
        logging.error(f"[Pedido {order_id}] Error al convertir un valor a Decimal. Revisar datos de la API.")
        return
    
    # Generar Hash
    hash_content = {**pedido_data, "productos_enriquecidos": enriched_products}
    hash_str = json.dumps(hash_content, sort_keys=True)
    pedido_hash = hashlib.sha256(hash_str.encode()).hexdigest()
    logging.info(f"[Pedido {order_id}] Cálculos OK. Total=${total_final:.2f}")

    # --- ETAPA D: PERSISTENCIA (Mejorada) ---
    logging.info(f"[Pedido {order_id}] Etapa D: Iniciando persistencia.")
    # update_or_create es la implementación perfecta de "No duplicar por reintentos"
    obj, created = PedidoProcesado.objects.update_or_create(
        id_pedido_original=order_id,
        defaults={
            'hash_pedido': pedido_hash,
            'cliente': pedido_data["cliente"],
            'detalle_completo': enriched_products,
            'subtotal': subtotal,
            'descuento': descuento,
            'total_final': total_final,
        }
    )
    action = "creado" if created else "actualizado"
    logging.info(f"[Pedido {order_id}] Persistencia OK. Pedido {action} en la base de datos. ¡Proceso completado!")