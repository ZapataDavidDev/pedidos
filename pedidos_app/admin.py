from django.contrib import admin
from .models import PedidoProcesado, TaskHistory

@admin.register(PedidoProcesado)
class PedidoProcesadoAdmin(admin.ModelAdmin):
    list_display = ('id_pedido_original', 'cliente', 'total_final', 'fecha_procesado')
    list_filter = ('cliente', 'fecha_procesado')
    search_fields = ('id_pedido_original', 'cliente')

# Agregamos a nuestro Admin de Django la tabla con el historial de tareas.
@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    # --- AÑADIMOS LOS NUEVOS CAMPOS A LA VISTA ---
    list_display = ('task_id', 'task_name', 'link_al_pedido', 'status', 'worker_hostname', 'start_time', 'end_time')
    list_filter = ('status', 'task_name', 'worker_hostname', 'start_time')
    search_fields = ('task_id', 'task_name', 'pedido_id')
    
    # Hacemos que la vista sea de solo lectura
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Pedido ID')
    def link_al_pedido(self, obj):
        """
        Crea un enlace HTML al admin del PedidoProcesado correspondiente.
        """
        if obj.pedido_id:
            # Construimos la URL a la página de edición del PedidoProcesado
            url = reverse('admin:pedidos_app_pedidoprocesado_change', args=[obj.pedido_id])
            return format_html('<a href="{}">{}</a>', url, obj.pedido_id)
        return "-" # Muestra un guion si no hay ID de pedido