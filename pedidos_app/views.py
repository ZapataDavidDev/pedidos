from django.http import JsonResponse
from .tasks import procesar_pedido_completo

def iniciar_procesamiento(request):
    """
    Esta vista actúa como el "productor", encolando una serie de pedidos de ejemplo.
    """
    sample_orders = [
        {"id": 123, "cliente": "ACME Corp", "productos": [{"sku": "P001", "cantidad": 3}, {"sku": "P002", "cantidad": 5}]},
        {"id": 124, "cliente": "Stark Industries", "productos": [{"sku": "P003", "cantidad": 10}, {"sku": "P004", "cantidad": 1}]},
        {"id": 125, "cliente": "Wayne Enterprises", "productos": [{"sku": "P008", "cantidad": 30}]},
        {"id": 126, "cliente": "Cyberdyne Systems", "productos": [{"sku": "P015", "cantidad": 2}]},
        {"id": 999, "cliente": "Error Corp", "productos": []},
        {"id": 127, "cliente": "OsCorp", "productos": [{"sku": "P999", "cantidad": 1}]},
    ]

    count = 0
    for order in sample_orders:
        procesar_pedido_completo(order)
        count += 1
    
    return JsonResponse({"status": "ok", "message": f"{count} pedidos han sido encolados para su procesamiento."})