"""
Configuracion de interfaz Django Admin.

Definimos los modelos que vamos a registrar en el admnin de django asi como 
las columnas a mostrar y filtros disponibles, se configuran permisos a nivel de vista."""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import PedidoProcesado, TaskHistory

@admin.register(PedidoProcesado)
class PedidoProcesadoAdmin(admin.ModelAdmin):
    list_display = ('id_pedido_original', 'cliente','subtotal','descuento','total_final','detalle_completo' ,'fecha_procesado')
    list_filter = ('cliente', 'fecha_procesado')
    search_fields = ('id_pedido_original', 'cliente')

# se agrega a nuestro Admin de Django la tabla con el historial de tareas.
@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'task_name', 'link_al_pedido', 'status','worker_hostname', 'start_time','error_message')
    list_filter = ('status', 'task_name', 'worker_hostname')
    search_fields = ('task_id', 'task_name', 'pedido__id_pedido_original') # Busca a través de la relación
    
    # Hacemos la vista de solo lectura
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Pedido Asociado')
    def link_al_pedido(self, obj):
        """
        Crea un enlace HTML al admin del PedidoProcesado.
        """
        if obj.pedido:
            # se construye la URL a la página de edición del PedidoProcesado
            url = reverse('admin:pedidos_app_pedidoprocesado_change', args=[obj.pedido.pk])
            return format_html('<a href="{}">{}</a>', url, obj.pedido.id_pedido_original)
        return "-"