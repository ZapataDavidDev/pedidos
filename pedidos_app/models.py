from django.db import models

class PedidoProcesado(models.Model):
    id_pedido_original = models.IntegerField(primary_key=True, help_text="ID pedido de entrada")
    hash_pedido = models.CharField(max_length=64, unique=True, help_text="Hash procesado")
    cliente = models.CharField(max_length=255)
    detalle_completo = models.JSONField(help_text="JSON enriquecido")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    descuento = models.DecimalField(max_digits=10, decimal_places=2)
    total_final = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_procesado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {self.id_pedido_original} - {self.cliente}"

class TaskHistory(models.Model):
    class Status(models.TextChoices):
        STARTED = 'STARTED', 'Iniciada'
        SUCCESS = 'SUCCESS', 'Completada'
        ERROR = 'ERROR', 'Fallida'

    task_id = models.CharField(max_length=36, primary_key=True)
    task_name = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    worker_hostname = models.CharField(max_length=255, null=True, blank=True, help_text="Hostname del worker que ejecutó la tarea")

    pedido = models.ForeignKey(
                                PedidoProcesado,
                                on_delete=models.SET_NULL, # Si se borra el pedido, el historial no se borra, solo se anula el enlace.
                                null=True,
                                blank=True,
                                related_name="task_history"
                                )
    def __str__(self):
        return f"{self.task_name} ({self.task_id}) - {self.status}"
