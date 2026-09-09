"""Módulo validator.

Contiene la implementación de validator.py del Sistema de Biblioteca.
"""

import re

from django.core.exceptions import ValidationError


class PasswordSecurityValidator:
    """
    Validador de seguridad para las contraseñas
    del Sistema de Biblioteca.

    Requisitos:

    - Mínimo 8 caracteres.
    - Al menos una letra mayúscula.
    - Al menos un número.
    - Al menos un carácter especial.
    """

    def validate(self, password, user=None):

        # ========================================================
        # LONGITUD
        # ========================================================

        """Valida los datos recibidos y genera un error cuando no cumplen las reglas definidas."""
        if len(password) < 8:

            raise ValidationError(
                'La contraseña debe tener al menos 8 caracteres.'
            )


        # ========================================================
        # MAYÚSCULA
        # ========================================================

        if not re.search(
            r'[A-Z]',
            password
        ):

            raise ValidationError(
                'La contraseña debe contener al menos '
                'una letra mayúscula.'
            )


        # ========================================================
        # NÚMERO
        # ========================================================

        if not re.search(
            r'[0-9]',
            password
        ):

            raise ValidationError(
                'La contraseña debe contener al menos '
                'un número.'
            )


        # ========================================================
        # CARÁCTER ESPECIAL
        # ========================================================

        if not re.search(
            r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>/?]',
            password
        ):

            raise ValidationError(
                'La contraseña debe contener al menos '
                'un carácter especial.'
            )


    def get_help_text(self):

        """Devuelve el mensaje de ayuda asociado a esta validación."""
        return (
            'La contraseña debe tener al menos 8 caracteres, '
            'una letra mayúscula, un número y un carácter especial.'
        )