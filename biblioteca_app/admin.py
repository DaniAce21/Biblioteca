"""Módulo admin.

Contiene la implementación de admin.py del Sistema de Biblioteca.
"""

from django.contrib import admin

from .models import LogActividad

# Register your models here.


@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    """Presenta el historial de auditoría en Django Admin como solo lectura."""
    list_display = ('fecha_hora', 'usuario', 'tipo', 'accion', 'nivel', 'modulo', 'resultado', 'ip')
    list_filter = ('tipo', 'nivel', 'accion', 'modulo', 'resultado', 'fecha_hora')
    search_fields = ('usuario__username', 'descripcion', 'ip')
    readonly_fields = (
        'usuario', 'tipo', 'accion', 'nivel', 'modulo', 'entidad', 'objeto_id',
        'descripcion', 'datos_anteriores', 'datos_nuevos', 'fecha_hora',
        'ip', 'user_agent', 'resultado'
    )
