# pedidos_app/huey.py

# ¡Añadimos la librería socket!
import socket
from huey.contrib.djhuey import HUEY as huey
from django.utils import timezone

@huey.pre_execute()
def pre_execute_handler(task):
    """
    Se ejecuta ANTES de que una tarea comience.
    Crea el registro inicial del historial.
    """
    from .models import TaskHistory
    
    pedido_id = None
    if task.name == 'pedidos_app.tasks.procesar_pedido_completo':
        if task.args and isinstance(task.args[0], dict):
            pedido_id = task.args[0].get('id')
            
    TaskHistory.objects.create(
        task_id=task.id,
        task_name=task.name,
        status=TaskHistory.Status.STARTED,
        pedido_id=pedido_id
        # Ya no intentamos obtener el hostname aquí.
    )

@huey.post_execute()
def post_execute_handler(task, task_value, exception):
    """
    Se ejecuta DESPUÉS de que una tarea termine.
    Actualiza el registro con el estado final y el hostname.
    """
    from .models import TaskHistory
    try:
        history_entry = TaskHistory.objects.get(task_id=task.id)
        history_entry.end_time = timezone.now()
        
        # --- LA SOLUCIÓN DEFINITIVA ---
        # Obtenemos el hostname directamente del sistema operativo.
        # Esto es 100% fiable y no depende del objeto task.
        history_entry.worker_hostname = socket.gethostname()
        
        if exception:
            history_entry.status = TaskHistory.Status.ERROR
            history_entry.error_message = str(exception)[:500]
        else:
            history_entry.status = TaskHistory.Status.SUCCESS
        
        history_entry.save()
    except TaskHistory.DoesNotExist:
        pass