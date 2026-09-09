"""Módulo admin.

Contiene la implementación de admin.py del Sistema de Biblioteca.
"""

from django.contrib import admin

from .models import LogActividad

# Register your models here.


@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    """Presenta el historial de auditoría en Django Admin como solo lectura."""
    list_display = ('fecha_hora', 'usuario', 'accion', 'modulo', 'resultado', 'ip')
    list_filter = ('accion', 'modulo', 'resultado', 'fecha_hora')
    search_fields = ('usuario__username', 'descripcion', 'ip')
    readonly_fields = ('usuario', 'accion', 'modulo', 'descripcion', 'fecha_hora', 'ip', 'resultado')
