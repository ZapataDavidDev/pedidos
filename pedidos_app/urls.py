from django.urls import path
from .views import iniciar_procesamiento

urlpatterns = [
    path('iniciar/', iniciar_procesamiento, name='iniciar_procesamiento'),
]