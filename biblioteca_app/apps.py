"""Módulo apps.

Contiene la implementación de apps.py del Sistema de Biblioteca.
"""

from django.apps import AppConfig


class BibliotecaAppConfig(AppConfig):
    """Representa la clase biblioteca app config y encapsula la lógica relacionada con este componente."""
    name = 'biblioteca_app'
