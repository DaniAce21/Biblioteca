"""Módulo forms.

Contiene la implementación de forms.py del Sistema de Biblioteca.
"""

from django import forms
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

import re

from .models import (
    Lector,
    Libro,
    Autor,
    Editorial,
    Prestamo,
    LibroAutor,
    LibroEditorial,
    PerfilUsuario,
)


# ============================================================
# REGISTRO DE USUARIO
# ============================================================

class RegistroUsuarioForm(forms.Form):

    """Representa la clase registro usuario form y encapsula la lógica relacionada con este componente."""
    username = forms.CharField(
        label='Nombre de usuario',
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ejemplo: daniel123',
                'autocomplete': 'username',
            }
        )
    )

    nombres = forms.CharField(
        label='Nombres',
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa tus nombres',
            }
        )
    )

    apellido_paterno = forms.CharField(
        label='Apellido paterno',
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa tu apellido paterno',
            }
        )
    )

    apellido_materno = forms.CharField(
        label='Apellido materno',
        max_length=100,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ingresa tu apellido materno',
            }
        )
    )

    RUT = forms.CharField(
        label='RUT',
        max_length=12,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ejemplo: 12.345.678-9',
                'autocomplete': 'off',
            }
        )
    )

    email = forms.EmailField(
        label='Correo electrónico',
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
                'autocomplete': 'email',
            }
        )
    )

    Telefono = forms.CharField(
        label='Número de teléfono',
        max_length=20,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': '+56 9 1234 5678',
                'autocomplete': 'tel',
            }
        )
    )

    Direccion = forms.CharField(
        label='Dirección',
        max_length=200,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Calle, número, comuna',
                'autocomplete': 'street-address',
            }
        )
    )

    password = forms.CharField(
        label='Contraseña',
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Mínimo 8 caracteres',
                'autocomplete': 'new-password',
            }
        )
    )

    password_confirm = forms.CharField(
        label='Confirmar contraseña',
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Repite tu contraseña',
                'autocomplete': 'new-password',
            }
        )
    )

    # ========================================================
    # VALIDAR USERNAME
    # ========================================================

    def clean_username(self):

        """Valida y normaliza el campo username antes de guardar los datos del formulario."""
        username = self.cleaned_data.get(
            'username'
        ).strip()

        if User.objects.filter(
            username__iexact=username
        ).exists():

            raise forms.ValidationError(
                'Este nombre de usuario ya está registrado.'
            )

        return username

    # ========================================================
    # VALIDAR RUT
    # ========================================================

    def clean_RUT(self):

        """Valida y normaliza el campo rut antes de guardar los datos del formulario."""
        rut = self.cleaned_data.get(
            'RUT'
        ).strip().upper()

        if PerfilUsuario.objects.filter(
            RUT__iexact=rut
        ).exists():

            raise forms.ValidationError(
                'Este RUT ya está registrado.'
            )

        return rut

    # ========================================================
    # VALIDAR EMAIL
    # ========================================================

    def clean_email(self):

        """Valida y normaliza el campo email antes de guardar los datos del formulario."""
        email = self.cleaned_data.get(
            'email'
        ).strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():

            raise forms.ValidationError(
                'Este correo electrónico ya está registrado.'
            )

        return email

    # ========================================================
    # VALIDAR TELÉFONO
    # ========================================================

    def clean_Telefono(self):
        """Valida que el número contenga una cantidad razonable de dígitos."""
        telefono = self.cleaned_data.get('Telefono', '').strip()
        digitos = re.sub(r'\D', '', telefono)

        if len(digitos) < 8 or len(digitos) > 15:
            raise forms.ValidationError(
                'Ingresa un número de teléfono válido.'
            )

        return telefono

    # ========================================================
    # VALIDAR DIRECCIÓN
    # ========================================================

    def clean_Direccion(self):
        """Normaliza la dirección ingresada durante el registro."""
        direccion = self.cleaned_data.get('Direccion', '').strip()

        if len(direccion) < 5:
            raise forms.ValidationError(
                'Ingresa una dirección válida.'
            )

        return direccion

    # ========================================================
    # VALIDAR CONTRASEÑA
    # ========================================================

    def clean_password(self):

        """Valida y normaliza el campo password antes de guardar los datos del formulario."""
        password = self.cleaned_data.get(
            'password'
        )

        if not password:
            return password

        # ----------------------------------------------------
        # MÍNIMO 8 CARACTERES
        # ----------------------------------------------------

        if len(password) < 8:

            raise forms.ValidationError(
                'La contraseña debe tener al menos 8 caracteres.'
            )

        # ----------------------------------------------------
        # MAYÚSCULA
        # ----------------------------------------------------

        if not re.search(
            r'[A-Z]',
            password
        ):

            raise forms.ValidationError(
                'La contraseña debe contener al menos una letra mayúscula.'
            )

        # ----------------------------------------------------
        # NÚMERO
        # ----------------------------------------------------

        if not re.search(
            r'[0-9]',
            password
        ):

            raise forms.ValidationError(
                'La contraseña debe contener al menos un número.'
            )

        # ----------------------------------------------------
        # CARÁCTER ESPECIAL
        # ----------------------------------------------------

        if not re.search(
            r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>/?]',
            password
        ):

            raise forms.ValidationError(
                'La contraseña debe contener al menos un carácter especial.'
            )

        return password

    # ========================================================
    # VALIDAR CONTRASEÑAS
    # ========================================================

    def clean(self):

        """Realiza las validaciones generales del formulario y comprueba la coherencia entre sus campos."""
        cleaned_data = super().clean()

        password = cleaned_data.get(
            'password'
        )

        password_confirm = cleaned_data.get(
            'password_confirm'
        )

        if (
            password
            and password_confirm
            and password != password_confirm
        ):

            raise forms.ValidationError(
                'Las contraseñas no coinciden.'
            )

        return cleaned_data

    # ========================================================
    # GUARDAR USUARIO + LECTOR + PERFIL
    # ========================================================

    def save(self):

        """Guarda los datos validados y ejecuta la lógica adicional necesaria para completar la operación."""
        username = self.cleaned_data['username']

        nombres = self.cleaned_data['nombres']

        apellido_paterno = self.cleaned_data[
            'apellido_paterno'
        ]

        apellido_materno = self.cleaned_data[
            'apellido_materno'
        ]

        rut = self.cleaned_data['RUT']

        email = self.cleaned_data['email']

        telefono = self.cleaned_data['Telefono']

        direccion = self.cleaned_data['Direccion']

        password = self.cleaned_data['password']

        # ====================================================
        # CREAR USUARIO DJANGO
        # ====================================================

        usuario = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=nombres,
            last_name=(
                f'{apellido_paterno} '
                f'{apellido_materno}'
            ).strip()
        )

        # ====================================================
        # CREAR LECTOR
        # ====================================================

        lector = Lector.objects.create(
            ApellidoP=apellido_paterno,
            ApellidoM=apellido_materno,
            Nombres=nombres,
            Telefono=telefono,
            Direccion=direccion
        )

        # ====================================================
        # CREAR PERFIL
        # ====================================================

        PerfilUsuario.objects.create(
            usuario=usuario,
            lector=lector,
            RUT=rut,
            tipo_usuario='LECTOR'
        )

        return usuario


# ============================================================
# REGISTRO POR PASOS - ESTILO CUENTA MODERNA
# ============================================================

class RegistroPasoNombreForm(forms.Form):

    """Primer paso del registro: datos personales básicos."""

    nombres = forms.CharField(
        label='Nombres',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'register-input',
            'placeholder': 'Nombres',
            'autocomplete': 'given-name',
            'autofocus': 'autofocus',
        })
    )

    apellido_paterno = forms.CharField(
        label='Apellido paterno',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'register-input',
            'placeholder': 'Apellido paterno',
            'autocomplete': 'family-name',
        })
    )

    apellido_materno = forms.CharField(
        label='Apellido materno',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'register-input',
            'placeholder': 'Apellido materno',
            'autocomplete': 'additional-name',
        })
    )

    # Datos de contacto obligatorios para completar el registro.
    Telefono = forms.CharField(
        label='Número de teléfono',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'register-input',
            'placeholder': '+56 9 1234 5678',
            'autocomplete': 'tel',
        })
    )

    Direccion = forms.CharField(
        label='Dirección',
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'register-input',
            'placeholder': 'Calle, número, comuna',
            'autocomplete': 'street-address',
        })
    )

    def clean_Telefono(self):
        """Valida la cantidad de dígitos del teléfono."""
        telefono = self.cleaned_data.get('Telefono', '').strip()
        digitos = re.sub(r'\D', '', telefono)
        if len(digitos) < 8 or len(digitos) > 15:
            raise forms.ValidationError('Ingresa un número de teléfono válido.')
        return telefono

    def clean_Direccion(self):
        """Valida que la dirección no quede vacía o demasiado corta."""
        direccion = self.cleaned_data.get('Direccion', '').strip()
        if len(direccion) < 5:
            raise forms.ValidationError('Ingresa una dirección válida.')
        return direccion


class RegistroPasoCuentaForm(forms.Form):

    """Segundo paso: identidad de acceso y correo."""

    username = forms.CharField(
        label='Nombre de usuario',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'register-input',
            'placeholder': 'Elige un nombre de usuario',
            'autocomplete': 'username',
            'autofocus': 'autofocus',
        })
    )

    email = forms.EmailField(
        label='Correo electrónico',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'register-input',
            'placeholder': 'tucorreo@ejemplo.com',
            'autocomplete': 'email',
        })
    )

    RUT = forms.CharField(
        label='RUT',
        max_length=12,
        widget=forms.TextInput(attrs={
            'class': 'register-input',
            'placeholder': '12.345.678-9',
            'autocomplete': 'off',
        })
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está registrado.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado.')
        return email

    def clean_RUT(self):
        rut = self.cleaned_data['RUT'].strip().upper()
        if PerfilUsuario.objects.filter(RUT__iexact=rut).exists():
            raise forms.ValidationError('Este RUT ya está registrado.')
        return rut


class RegistroPasoPasswordForm(forms.Form):

    """Tercer paso: contraseña y confirmación."""

    password = forms.CharField(
        label='Contraseña',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'register-input',
            'placeholder': 'Crea una contraseña segura',
            'autocomplete': 'new-password',
            'autofocus': 'autofocus',
        })
    )

    password_confirm = forms.CharField(
        label='Confirmar contraseña',
        min_length=8,
        widget=forms.PasswordInput(attrs={
            'class': 'register-input',
            'placeholder': 'Repite tu contraseña',
            'autocomplete': 'new-password',
        })
    )

    def clean_password(self):
        password = self.cleaned_data.get('password')
        if not password:
            return password
        if len(password) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres.')
        if not re.search(r'[A-Z]', password):
            raise forms.ValidationError('Debe contener al menos una letra mayúscula.')
        if not re.search(r'[0-9]', password):
            raise forms.ValidationError('Debe contener al menos un número.')
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>/?]', password):
            raise forms.ValidationError('Debe contener al menos un carácter especial.')
        return password

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') and cleaned.get('password_confirm') and cleaned['password'] != cleaned['password_confirm']:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned


# ============================================================
# LOGIN
# ============================================================

class LoginForm(forms.Form):

    """Representa la clase login form y encapsula la lógica relacionada con este componente."""
    username = forms.CharField(
        label='Nombre de usuario',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de usuario',
                'autocomplete': 'username',
            }
        )
    )

    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Contraseña',
                'autocomplete': 'current-password',
            }
        )
    )

    def __init__(self, *args, **kwargs):

        """Gestiona la operación   init   dentro de la aplicación."""
        super().__init__(
            *args,
            **kwargs
        )

        self.usuario = None

    def clean(self):

        """Realiza las validaciones generales del formulario y comprueba la coherencia entre sus campos."""
        cleaned_data = super().clean()

        username = cleaned_data.get(
            'username'
        )

        password = cleaned_data.get(
            'password'
        )

        if username and password:

            self.usuario = authenticate(
                username=username,
                password=password
            )

            if self.usuario is None:

                raise forms.ValidationError(
                    'El nombre de usuario o la contraseña son incorrectos.'
                )

            if not self.usuario.is_active:

                raise forms.ValidationError(
                    'Este usuario se encuentra desactivado.'
                )

        return cleaned_data


class TwoFactorCodeForm(forms.Form):

    """Formulario para validar un código TOTP de seis dígitos."""

    code = forms.CharField(
        label='Código de autenticación',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'register-input',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
            'pattern': '[0-9]{6}',
        })
    )

    def clean_code(self):
        """Acepta únicamente seis dígitos."""
        code = self.cleaned_data.get('code', '').strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError(
                'El código debe contener exactamente 6 dígitos.'
            )
        return code


class PerfilContactoForm(forms.ModelForm):

    """Permite al lector actualizar únicamente teléfono y dirección."""

    class Meta:
        model = Lector
        fields = ['Telefono', 'Direccion']
        labels = {
            'Telefono': 'Número de teléfono',
            'Direccion': 'Dirección',
        }
        widgets = {
            'Telefono': forms.TextInput(attrs={
                'class': 'register-input',
                'placeholder': '+56 9 1234 5678',
                'autocomplete': 'tel',
            }),
            'Direccion': forms.TextInput(attrs={
                'class': 'register-input',
                'placeholder': 'Calle, número, comuna',
                'autocomplete': 'street-address',
            }),
        }


# ============================================================
# FORMULARIO LECTOR
# ============================================================

class LectorForm(forms.ModelForm):

    """Representa la clase lector form y encapsula la lógica relacionada con este componente."""
    class Meta:

        model = Lector

        fields = [
            'ApellidoP',
            'ApellidoM',
            'Nombres',
            'Telefono',
            'Direccion',
        ]

        labels = {
            'ApellidoP': 'Apellido paterno',
            'ApellidoM': 'Apellido materno',
            'Nombres': 'Nombres',
            'Telefono': 'Número de teléfono',
            'Direccion': 'Dirección',
        }


# ============================================================
# FORMULARIO LIBRO
# ============================================================

class LibroForm(forms.ModelForm):

    """Representa la clase libro form y encapsula la lógica relacionada con este componente."""
    class Meta:

        model = Libro

        fields = [
            'Titulo',
        ]

        labels = {
            'Titulo': 'Título',
        }


# ============================================================
# FORMULARIO AUTOR
# ============================================================

class AutorForm(forms.ModelForm):

    """Representa la clase autor form y encapsula la lógica relacionada con este componente."""
    class Meta:

        model = Autor

        fields = [
            'NombreAutor',
        ]

        labels = {
            'NombreAutor': 'Nombre del autor',
        }


# ============================================================
# FORMULARIO EDITORIAL
# ============================================================

class EditorialForm(forms.ModelForm):

    """Representa la clase editorial form y encapsula la lógica relacionada con este componente."""
    class Meta:

        model = Editorial

        fields = [
            'NombreEditorial',
        ]

        labels = {
            'NombreEditorial': 'Nombre de la editorial',
        }


# ============================================================
# FORMULARIO PRESTAMO
# ============================================================

class PrestamoForm(forms.ModelForm):

    """Representa la clase prestamo form y encapsula la lógica relacionada con este componente."""
    class Meta:

        model = Prestamo

        fields = [
            'CodLibro',
            'CodLector',
            'FechaDev',
        ]

        labels = {
            'CodLibro': 'Libro',
            'CodLector': 'Lector',
            'FechaDev': 'Fecha de devolución',
        }

        widgets = {
            'FechaDev': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'type': 'date',
                    'class': 'form-control',
                }
            )
        }

    def __init__(
        self,
        *args,
        **kwargs
    ):

        """Gestiona la operación   init   dentro de la aplicación."""
        super().__init__(
            *args,
            **kwargs
        )

        hoy = timezone.localdate()

        self.fields[
            'FechaDev'
        ].widget.attrs[
            'min'
        ] = hoy.isoformat()

    def clean_FechaDev(self):

        """Valida y normaliza el campo fecha dev antes de guardar los datos del formulario."""
        fecha = self.cleaned_data.get(
            'FechaDev'
        )

        hoy = timezone.localdate()

        if fecha and fecha < hoy:

            raise forms.ValidationError(
                'La fecha de devolución no puede ser anterior a hoy.'
            )

        return fecha


# ============================================================
# LIBRO - AUTOR
# ============================================================

class LibroAutorForm(forms.Form):

    """Representa la clase libro autor form y encapsula la lógica relacionada con este componente."""
    CodLibro = forms.ModelChoiceField(
        queryset=Libro.objects.all(),
        label='Libro'
    )

    CodAutor = forms.ModelChoiceField(
        queryset=Autor.objects.all(),
        label='Autor'
    )


# ============================================================
# LIBRO - EDITORIAL
# ============================================================

class LibroEditorialForm(forms.Form):

    """Representa la clase libro editorial form y encapsula la lógica relacionada con este componente."""
    CodLibro = forms.ModelChoiceField(
        queryset=Libro.objects.all(),
        label='Libro'
    )

    CodEditorial = forms.ModelChoiceField(
        queryset=Editorial.objects.all(),
        label='Editorial'
    )