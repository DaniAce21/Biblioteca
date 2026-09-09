"""Módulo views.

Contiene la implementación de views.py del Sistema de Biblioteca.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from django.db import transaction
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils import timezone
from io import BytesIO
import base64
import pyotp
import qrcode
from datetime import date

import requests

from .models import (
    Lector,
    Libro,
    Autor,
    Editorial,
    Prestamo,
    Devolucion,
    LibroAutor,
    LibroEditorial,
    SolicitudPrestamo,
    SolicitudLibro,
    LogActividad,
)

from .forms import (
    RegistroUsuarioForm,
    RegistroPasoNombreForm,
    RegistroPasoCuentaForm,
    RegistroPasoPasswordForm,
    PerfilContactoForm,
    LoginForm,
    LectorForm,
    LibroForm,
    AutorForm,
    EditorialForm,
    PrestamoForm,
    LibroAutorForm,
    LibroEditorialForm,
    TwoFactorCodeForm,
)




# ============================================================
# AUDITORÍA / LOG DE ACTIVIDAD
# ============================================================

def obtener_ip(request):
    """Obtiene la IP del cliente para el registro de auditoría."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def registrar_log(request, accion, modulo, descripcion, resultado='EXITO', usuario=None):
    """Crea un registro de auditoría sin interrumpir la operación principal."""
    try:
        usuario_log = usuario

        if usuario_log is None and getattr(request, 'user', None) is not None:
            if request.user.is_authenticated:
                usuario_log = request.user

        LogActividad.objects.create(
            usuario=usuario_log,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion[:500],
            ip=obtener_ip(request),
            resultado=resultado,
        )
    except Exception:
        # La auditoría nunca debe impedir que la operación funcional continúe.
        pass


# ============================================================
# CONFIGURACIÓN OPEN LIBRARY
# ============================================================

OPEN_LIBRARY_SEARCH_URL = "https://openlibrary.org/search.json"

OPEN_LIBRARY_HEADERS = {
    "User-Agent": "SistemaBiblioteca/1.0 (proyecto academico)"
}


# ============================================================
# BÚSQUEDA DE LIBROS EN OPEN LIBRARY
# ============================================================

def buscar_libros_open_library(termino, limite=8):
    """
    Busca libros en Open Library y devuelve datos simplificados.

    La función se mantiene separada de la vista para que después pueda
    reutilizarse desde otras partes del sistema sin duplicar la llamada
    HTTP ni la transformación de los datos recibidos.
    """

    termino = (termino or "").strip()

    if not termino:
        return []

    try:
        response = requests.get(
            OPEN_LIBRARY_SEARCH_URL,
            params={
                "q": termino,
                "fields": (
                    "key,title,author_name,first_publish_year,"
                    "cover_i,publisher,isbn"
                ),
                "limit": max(1, min(int(limite), 20)),
            },
            headers=OPEN_LIBRARY_HEADERS,
            timeout=8,
        )

        response.raise_for_status()
        data = response.json()

    except (requests.RequestException, ValueError, TypeError):
        return []

    resultados = []

    for item in data.get("docs", []):
        titulo = str(item.get("title", "")).strip()

        if not titulo:
            continue

        autores = item.get("author_name", []) or []
        editoriales = item.get("publisher", []) or []
        isbn = item.get("isbn", []) or []
        cover_id = item.get("cover_i")
        key = str(item.get("key", "")).strip()

        portada_url = ""

        if cover_id:
            portada_url = (
                f"https://covers.openlibrary.org/b/id/"
                f"{cover_id}-M.jpg?default=false"
            )

        resultados.append({
            "key": key,
            "titulo": titulo,
            "autor": ", ".join(
                str(autor).strip()
                for autor in autores
                if str(autor).strip()
            ),
            "editorial": str(editoriales[0]).strip()
                if editoriales else "",
            "anio": item.get("first_publish_year"),
            "isbn": str(isbn[0]).strip() if isbn else "",
            "portada": portada_url,
            "openlibrary_url": (
                f"https://openlibrary.org{key}"
                if key.startswith("/") else ""
            ),
        })

    return resultados



# ============================================================
# FUNCIÓN AUXILIAR
# ============================================================

def admin_required(view_func):
    """Permite el acceso únicamente a administradores."""

    def wrapper(request, *args, **kwargs):
        """Gestiona la operación wrapper dentro de la aplicación."""
        if not request.user.is_authenticated:
            return redirect("login")

        if not (request.user.is_staff or request.user.is_superuser):
            return HttpResponseForbidden(
                "No tienes permisos para acceder a esta sección."
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def lector_required(view_func):
    """Permite el acceso únicamente a lectores registrados."""

    def wrapper(request, *args, **kwargs):
        """Gestiona la operación wrapper dentro de la aplicación."""
        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.is_staff or request.user.is_superuser:
            return HttpResponseForbidden(
                "Esta sección es exclusiva para lectores."
            )

        try:
            perfil = request.user.perfil
        except Exception:
            return HttpResponseForbidden(
                "El usuario no tiene un perfil de lector configurado."
            )

        if perfil.tipo_usuario != "LECTOR" or perfil.lector is None:
            return HttpResponseForbidden(
                "El usuario no tiene un lector asociado."
            )

        return view_func(request, *args, **kwargs)

    return wrapper


@lector_required
def open_library_buscar(request):
    """
    Expone una búsqueda sencilla de libros para la vista del lector.

    El frontend podrá consultar esta URL con AJAX/Fetch, mostrar las
    portadas y permitir que el lector seleccione el libro que desea
    solicitar para adquisición.
    """

    termino = request.GET.get("q", "").strip()

    if not termino:
        return JsonResponse(
            {
                "ok": True,
                "resultados": [],
            }
        )

    resultados = buscar_libros_open_library(termino)

    # Indicamos si cada título ya existe en nuestro catálogo local.
    for resultado in resultados:
        resultado["en_biblioteca"] = Libro.objects.filter(
            Titulo__iexact=resultado["titulo"]
        ).exists()

    return JsonResponse(
        {
            "ok": True,
            "resultados": resultados,
        }
    )


def normalizar_nombre(valor):

    """Gestiona la operación normalizar nombre dentro de la aplicación."""
    if isinstance(valor, str):
        return valor.strip()

    if isinstance(valor, dict):
        return str(
            valor.get("name", "")
        ).strip()

    return ""


# ============================================================
# AUTENTICACIÓN
# ============================================================

# ============================================================
# REGISTRO DE USUARIO
# ============================================================

def registro(request):
    """Registro de lector dividido en pasos, inspirado en el flujo de Google."""
    if request.user.is_authenticated:
        return redirect("inicio")

    pasos = {
        1: RegistroPasoNombreForm,
        2: RegistroPasoCuentaForm,
        3: RegistroPasoPasswordForm,
    }

    step = int(request.POST.get("step", request.GET.get("step", 1)))
    step = max(1, min(step, 3))

    session_data = request.session.get("registro_datos", {})

    if request.method == "POST":
        action = request.POST.get("action", "next")
        form_class = pasos[step]
        form = form_class(request.POST)

        if action == "back":
            previous = max(1, step - 1)
            return redirect(f"{reverse('registro')}?step={previous}")

        if form.is_valid():
            session_data.update(form.cleaned_data)
            request.session["registro_datos"] = session_data

            if step < 3:
                return redirect(f"{reverse('registro')}?step={step + 1}")

            # Validación final con el formulario original para conservar
            # todas las reglas de registro ya existentes.
            final_form = RegistroUsuarioForm(session_data)
            if final_form.is_valid():
                usuario = final_form.save()

                registrar_log(
                    request,
                    'REGISTRO',
                    'Autenticación',
                    f'Nuevo usuario registrado: {usuario.username}.',
                    usuario=usuario,
                )

                request.session.pop("registro_datos", None)

                # La cuenta recién creada debe configurar y verificar 2FA
                # antes de obtener acceso al dashboard.
                request.session['2fa_setup_user_id'] = usuario.pk
                request.session['2fa_setup_required'] = True
                return redirect('two_factor_setup')

            form.add_error(None, "No fue posible completar el registro. Revisa los datos ingresados.")
            for field_name, field_errors in final_form.errors.items():
                if field_name in form.fields:
                    for error in field_errors:
                        form.add_error(field_name, error)
        
    else:
        form = pasos[step](initial=session_data)

    return render(
        request,
        "biblioteca_app/auth/registro.html",
        {
            "form": form,
            "step": step,
            "total_steps": 3,
            "registro_data": session_data,
        },
    )


# ============================================================
# LOGIN
# ============================================================

def login_usuario(request):

    """Gestiona la operación login usuario dentro de la aplicación."""
    if request.user.is_authenticated:

        return redirect("inicio")

    if request.method == "POST":

        form = LoginForm(
            request.POST
        )

        if form.is_valid():

            usuario = form.usuario

            # Antes de iniciar la sesión definitiva comprobamos si
            # la cuenta tiene habilitada la autenticación de dos factores.
            try:
                perfil = usuario.perfil
            except Exception:
                perfil = None

            if perfil and perfil.two_factor_enabled:
                # Guardamos únicamente el identificador necesario para el
                # segundo paso. El usuario aún no queda autenticado.
                request.session['2fa_pending_user_id'] = usuario.pk

                registrar_log(
                    request,
                    'LOGIN',
                    'Autenticación',
                    f'Credenciales válidas para {usuario.username}; pendiente de 2FA.',
                    resultado='INFO',
                    usuario=usuario,
                )

                return redirect('two_factor_verify')

            # Las cuentas existentes que todavía no tengan 2FA conservan
            # el acceso normal hasta que configuren esta medida de seguridad.
            login(
                request,
                usuario
            )

            registrar_log(
                request,
                'LOGIN',
                'Autenticación',
                f'Inicio de sesión realizado por {usuario.username}.',
            )

            # Redirección según el tipo de usuario.
            if usuario.is_staff or usuario.is_superuser:
                return redirect("inicio")

            if perfil and perfil.tipo_usuario == "LECTOR" and perfil.lector is not None:
                return redirect("lector_dashboard")

            return redirect("inicio")

    else:

        form = LoginForm()

    return render(
        request,
        "biblioteca_app/auth/login.html",
        {
            "form": form
        }
    )


# ============================================================
# AUTENTICACIÓN DE DOS FACTORES (2FA)
# ============================================================

def _obtener_usuario_2fa_pendiente(request, session_key):
    """
    Recupera el usuario que está esperando el paso de autenticación 2FA.

    La identidad se obtiene desde la sesión y se comprueba nuevamente
    que el usuario exista y permanezca activo antes de continuar.
    """

    user_id = request.session.get(session_key)

    if not user_id:
        return None

    usuario = User.objects.filter(
        pk=user_id,
        is_active=True,
    ).first()

    return usuario


def two_factor_setup(request):
    """
    Configura el autenticador TOTP para una cuenta recién registrada.

    El usuario recibe un código QR para escanear desde una aplicación
    autenticadora. Después debe introducir el código de seis dígitos
    generado por la aplicación para confirmar que la configuración funciona.
    """

    usuario = _obtener_usuario_2fa_pendiente(
        request,
        '2fa_setup_user_id',
    )

    if usuario is None:
        return redirect('registro')

    perfil = getattr(usuario, 'perfil', None)

    if perfil is None:
        return redirect('login')

    # Si por alguna razón la cuenta ya quedó configurada, no repetimos el flujo.
    if perfil.two_factor_enabled and perfil.two_factor_secret:
        request.session.pop('2fa_setup_user_id', None)
        request.session.pop('2fa_setup_required', None)
        request.session['2fa_pending_user_id'] = usuario.pk
        return redirect('two_factor_verify')

    # Generamos el secreto únicamente cuando todavía no existe.
    if not perfil.two_factor_secret:
        perfil.two_factor_secret = pyotp.random_base32()
        perfil.save(update_fields=['two_factor_secret'])

    totp = pyotp.TOTP(perfil.two_factor_secret)

    # URI estándar para Google Authenticator, Microsoft Authenticator y compatibles.
    provisioning_uri = totp.provisioning_uri(
        name=usuario.email,
        issuer_name='Sistema de Biblioteca',
    )

    # Generamos el código QR en memoria para no crear archivos permanentes.
    qr = qrcode.make(provisioning_uri)
    buffer = BytesIO()
    qr.save(buffer, format='PNG')
    qr_code_data_uri = (
        'data:image/png;base64,'
        + base64.b64encode(buffer.getvalue()).decode('ascii')
    )

    if request.method == 'POST':
        form = TwoFactorCodeForm(request.POST)

        if form.is_valid():
            code = form.cleaned_data['code']

            if totp.verify(code, valid_window=1):
                perfil.two_factor_enabled = True
                perfil.two_factor_verified_at = timezone.now()
                perfil.save(
                    update_fields=[
                        'two_factor_enabled',
                        'two_factor_verified_at',
                    ]
                )

                registrar_log(
                    request,
                    '2FA_CONFIGURADO',
                    'Autenticación',
                    f'2FA configurado correctamente para {usuario.username}.',
                    usuario=usuario,
                )

                # El primer código válido confirma que la aplicación
                # autenticadora quedó correctamente vinculada.
                request.session.pop('2fa_setup_user_id', None)
                request.session.pop('2fa_setup_required', None)

                # Ahora sí iniciamos la sesión definitiva del usuario.
                login(request, usuario)

                if usuario.is_staff or usuario.is_superuser:
                    return redirect('inicio')

                if perfil.tipo_usuario == 'LECTOR' and perfil.lector is not None:
                    return redirect('lector_dashboard')

                return redirect('inicio')

            form.add_error(
                'code',
                'El código no es válido o ya expiró. Intenta nuevamente.',
            )
    else:
        form = TwoFactorCodeForm()

    return render(
        request,
        'biblioteca_app/auth/two_factor_setup.html',
        {
            'form': form,
            'usuario': usuario,
            'secret': perfil.two_factor_secret,
            'qr_code_data_uri': qr_code_data_uri,
        },
    )


def two_factor_verify(request):
    """
    Solicita el código 2FA antes de completar el inicio de sesión.

    La contraseña ya fue validada en ``login_usuario``. Esta vista agrega
    el segundo factor TOTP y solo entonces crea la sesión autenticada.
    """

    usuario = _obtener_usuario_2fa_pendiente(
        request,
        '2fa_pending_user_id',
    )

    if usuario is None:
        return redirect('login')

    perfil = getattr(usuario, 'perfil', None)

    if perfil is None or not perfil.two_factor_secret:
        request.session.pop('2fa_pending_user_id', None)
        return redirect('login')

    if request.method == 'POST':
        form = TwoFactorCodeForm(request.POST)

        if form.is_valid():
            code = form.cleaned_data['code']
            totp = pyotp.TOTP(perfil.two_factor_secret)

            if totp.verify(code, valid_window=1):
                request.session.pop('2fa_pending_user_id', None)
                login(request, usuario)

                registrar_log(
                    request,
                    '2FA_VERIFICADO',
                    'Autenticación',
                    f'Verificación 2FA completada para {usuario.username}.',
                    usuario=usuario,
                )

                if usuario.is_staff or usuario.is_superuser:
                    return redirect('inicio')

                if perfil.tipo_usuario == 'LECTOR' and perfil.lector is not None:
                    return redirect('lector_dashboard')

                return redirect('inicio')

            form.add_error(
                'code',
                'El código 2FA no es válido o ya expiró.',
            )
    else:
        form = TwoFactorCodeForm()

    return render(
        request,
        'biblioteca_app/auth/two_factor_verify.html',
        {
            'form': form,
            'usuario': usuario,
        },
    )


# ============================================================
# RECUPERACIÓN DE CONTRASEÑA
# ============================================================

def password_reset(request):
    """
    Muestra la pantalla inicial de recuperación de contraseña.

    GET:
        Presenta el formulario donde el usuario escribe su correo.

    POST:
        Delega el procesamiento a ``password_reset_usuario``.
    """

    # Cuando el usuario entra directamente a /password-reset/,
    # mostramos la plantilla inicial del proceso de recuperación.
    if request.method == "GET":
        return render(
            request,
            "biblioteca_app/auth/password/password_reset.html",
        )

    # Para POST reutilizamos la función que genera el token.
    return password_reset_usuario(request)


def password_reset_usuario(request):
    """Solicita recuperación y, en DEBUG, muestra el enlace local generado."""
    if request.method != "POST":
        return redirect("login")

    email = request.POST.get("email", "").strip().lower()
    usuario = User.objects.filter(email__iexact=email, is_active=True).first()
    reset_url = None

    if usuario:
        registrar_log(
            request,
            'RECUPERACION_PASSWORD',
            'Autenticación',
            f'Solicitud de recuperación de contraseña para {usuario.username}.',
            resultado='INFO',
            usuario=usuario,
        )

        uid = urlsafe_base64_encode(force_bytes(usuario.pk))
        token = default_token_generator.make_token(usuario)
        reset_url = request.build_absolute_uri(
            reverse(
                "password_reset_confirm",
                kwargs={"uidb64": uid, "token": token},
            )
        )

        send_mail(
            "Recuperación de contraseña - Sistema de Biblioteca",
            (
                f"Hola, {usuario.get_username()}.\n\n"
                "Recibimos una solicitud para restablecer tu contraseña.\n\n"
                f"Abre este enlace:\n{reset_url}\n"
            ),
            getattr(settings, "DEFAULT_FROM_EMAIL", "biblioteca@inacap.cl"),
            [usuario.email],
            fail_silently=True,
        )

    return render(
        request,
        "biblioteca_app/auth/password/password_reset_done.html",
        {
            "reset_url": reset_url if settings.DEBUG else None,
        },
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_usuario(request):

    """Cierra la sesión y registra el cierre en el historial de auditoría."""
    usuario = request.user if request.user.is_authenticated else None

    if usuario is not None:
        registrar_log(
            request,
            'LOGOUT',
            'Autenticación',
            f'Cierre de sesión de {usuario.username}.',
            usuario=usuario,
        )

    request.session.pop('2fa_pending_user_id', None)
    request.session.pop('2fa_setup_user_id', None)
    request.session.pop('2fa_setup_required', None)

    logout(request)

    return redirect("login")


# ============================================================
# DASHBOARD ADMINISTRATIVO
# ============================================================

@admin_required
def admin_dashboard(request):
    """
    Ruta alternativa para el dashboard administrativo.
    Redirige al dashboard principal para mantener una sola pantalla
    de administración.
    """
    return redirect("inicio")


# ============================================================
# DASHBOARD PRINCIPAL
# ============================================================

def inicio(request):
    """Dashboard administrativo principal."""
    if not request.user.is_authenticated:
        return redirect("login")

    if not (request.user.is_staff or request.user.is_superuser):
        return redirect("lector_dashboard")

    # La actividad reciente ahora proviene del historial persistente de auditoría.
    logs = LogActividad.objects.select_related("usuario").all()[:8]

    iconos = {
        'LOGIN': 'bi-box-arrow-in-right',
        'LOGOUT': 'bi-box-arrow-right',
        'REGISTRO': 'bi-person-plus',
        '2FA_CONFIGURADO': 'bi-shield-lock',
        '2FA_VERIFICADO': 'bi-shield-check',
        'RECUPERACION_PASSWORD': 'bi-key',
        'CREAR': 'bi-plus-circle',
        'EDITAR': 'bi-pencil-square',
        'ELIMINAR': 'bi-trash3',
        'PRESTAMO': 'bi-journal-check',
        'DEVOLUCION': 'bi-arrow-return-left',
        'SOLICITUD': 'bi-inbox',
        'ADQUISICION': 'bi-cart-check',
        'RECHAZO': 'bi-x-circle',
    }

    actividades = []

    for log in logs:
        nombre_usuario = log.usuario.username if log.usuario else "Sistema"
        actividades.append({
            "icon": iconos.get(log.accion, "bi-clock-history"),
            "text": log.descripcion,
            "when": f"{nombre_usuario} · {log.fecha_hora:%d/%m/%Y %H:%M}",
        })

    stats = [
        ("Libros registrados", Libro.objects.count(), "bi-book", "Títulos disponibles en el sistema"),
        ("Autores registrados", Autor.objects.count(), "bi-person-vcard", "Autores asociados al catálogo"),
        ("Editoriales registradas", Editorial.objects.count(), "bi-building", "Editoriales del catálogo"),
        ("Lectores registrados", Lector.objects.count(), "bi-people", "Lectores registrados"),
    ]

    context = {
        "cantidad_libros": Libro.objects.count(),
        "cantidad_autores": Autor.objects.count(),
        "cantidad_editoriales": Editorial.objects.count(),
        "cantidad_lectores": Lector.objects.count(),
        "cantidad_prestamos": Prestamo.objects.count(),
        "stats": stats,
        "actividades": actividades,
    }

    return render(request, "biblioteca_app/inicio.html", context)


# ============================================================
# DASHBOARD DEL LECTOR
# ============================================================

@lector_required
def lector_dashboard(request):
    """Gestiona la operación lector dashboard dentro de la aplicación."""
    perfil = request.user.perfil
    lector = perfil.lector

    prestamos = Prestamo.objects.select_related(
        "CodLibro",
        "CodLector"
    ).filter(
        CodLector=lector
    ).order_by(
        "FechaDev"
    )

    # Calculamos los tres estados visibles del dashboard.
    # "Por vencer" considera los próximos siete días.
    from datetime import timedelta

    today = date.today()
    limit_date = today + timedelta(days=7)

    prestamos_vencidos = prestamos.filter(FechaDev__lt=today).count()
    prestamos_por_vencer = prestamos.filter(
        FechaDev__gte=today,
        FechaDev__lte=limit_date,
    ).count()
    prestamos_vigentes = prestamos.filter(
        FechaDev__gt=limit_date
    ).count()

    context = {
        "perfil": perfil,
        "lector": lector,
        "prestamos": prestamos,
        "cantidad_prestamos": prestamos.count(),
        "prestamos_vigentes": prestamos_vigentes,
        "prestamos_por_vencer": prestamos_por_vencer,
        "prestamos_vencidos": prestamos_vencidos,
        "today": today,
    }

    return render(
        request,
        "biblioteca_app/lector/dashboard.html",
        context
    )


# ============================================================
# PRÉSTAMOS DEL LECTOR
# ============================================================

@lector_required
def mis_prestamos(request):
    """Gestiona la operación mis prestamos dentro de la aplicación."""
    lector = request.user.perfil.lector

    prestamos = Prestamo.objects.select_related(
        "CodLibro",
        "CodLector"
    ).filter(
        CodLector=lector
    ).order_by(
        "FechaDev"
    )

    return render(
        request,
        "biblioteca_app/lector/prestamo.html",
        {
            "prestamos": prestamos,
            "lector": lector,
        }
    )


# ============================================================
# LECTOR - LISTAR LIBROS
# ============================================================

@lector_required
def libros_lector(request):
    """Muestra al lector todos los libros de la biblioteca."""

    libros = Libro.objects.all().order_by("Titulo")

    # Mostramos al lector sus solicitudes de incorporación para que
    # pueda revisar si están pendientes, en adquisición o ya adquiridas.
    solicitudes_libro = SolicitudLibro.objects.filter(
        CodLector=request.user.perfil.lector
    ).order_by(
        "-FechaSolicitud"
    )[:10]

    return render(
        request,
        "biblioteca_app/lector/libros.html",
        {
            "libros": libros,
            "solicitudes_libro": solicitudes_libro,
        }
    )


# ============================================================
# LECTOR - HISTORIAL DE DEVOLUCIONES
# ============================================================

@lector_required
def historial_lector(request):
    """Muestra al lector únicamente su historial de devoluciones."""

    lector = request.user.perfil.lector

    devoluciones = Devolucion.objects.select_related(
        "CodLibro",
        "CodLector"
    ).filter(
        CodLector=lector
    ).order_by(
        "-FechaDevolucionReal",
        "-CodDevolucion"
    )

    return render(
        request,
        "biblioteca_app/lector/historial.html",
        {
            "devoluciones": devoluciones,
            "lector": lector,
        }
    )


# ============================================================
# LECTOR - MIS DATOS
# ============================================================

@lector_required
def mis_datos(request):
    """Consulta y actualización de teléfono y dirección del lector."""
    perfil = request.user.perfil
    lector = perfil.lector

    if request.method == "POST":
        form = PerfilContactoForm(request.POST, instance=lector)
        if form.is_valid():
            form.save()
            return redirect("mis_datos")
    else:
        form = PerfilContactoForm(instance=lector)

    return render(
        request,
        "biblioteca_app/lector/datos.html",
        {
            "perfil": perfil,
            "lector": lector,
            "usuario": request.user,
            "form": form,
        },
    )


# ============================================================
# LECTOR - CANCELAR SU PROPIO PRÉSTAMO
# ============================================================

@lector_required
def prestamo_delete_propio(request, codlibro, codlector):
    """Gestiona la operación prestamo delete propio dentro de la aplicación."""
    lector = request.user.perfil.lector

    prestamo = get_object_or_404(
        Prestamo,
        CodLibro_id=codlibro,
        CodLector_id=codlector
    )

    # Seguridad: el lector solo puede eliminar préstamos asociados
    # a su propio registro de Lector.
    if prestamo.CodLector_id != lector.CodLector:
        return HttpResponseForbidden(
            "No puedes cancelar el préstamo de otro lector."
        )

    if request.method == "POST":
        prestamo.delete()
        return redirect("lector_dashboard")

    return render(
        request,
        "biblioteca_app/prestamo/delete.html",
        {
            "prestamo": prestamo,
            "es_lector": True,
        }
    )


# ============================================================
# DASHBOARD DE LIBROS
# ============================================================

@admin_required
def libro_dashboard(request):

    """Gestiona la operación libro dashboard dentro de la aplicación."""
    libros = Libro.objects.order_by(
        "-CodLibro"
    )[:8]

    context = {
        "cantidad_libros": Libro.objects.count(),
        "cantidad_autores": Autor.objects.count(),
        "cantidad_editoriales": Editorial.objects.count(),
        "libros": libros,
    }

    return render(
        request,
        "biblioteca_app/libro/dashboard.html",
        context
    )


# ============================================================
# DASHBOARD DE AUTORES
# ============================================================

@admin_required
def autor_dashboard(request):

    """Gestiona la operación autor dashboard dentro de la aplicación."""
    # La relación inversa se define en LibroAutor.CodAutor como
    # ``libro_autores``. Prefetch evita una consulta por cada autor.
    autores = Autor.objects.prefetch_related(
        "libro_autores__CodLibro"
    ).order_by(
        "NombreAutor"
    )

    context = {
        "cantidad_autores": Autor.objects.count(),
        "cantidad_libros": Libro.objects.count(),
        "autores": autores,
    }

    return render(
        request,
        "biblioteca_app/autor/dashboard.html",
        context
    )


# ============================================================
# DASHBOARD DE EDITORIALES
# ============================================================

@admin_required
def editorial_dashboard(request):

    """Gestiona la operación editorial dashboard dentro de la aplicación."""
    # La relación inversa se define en LibroEditorial.CodEditorial como
    # ``libro_editoriales``. Prefetch evita una consulta por cada editorial.
    editoriales = Editorial.objects.prefetch_related(
        "libro_editoriales__CodLibro"
    ).order_by(
        "NombreEditorial"
    )

    context = {
        "cantidad_editoriales": Editorial.objects.count(),
        "cantidad_libros": Libro.objects.count(),
        "editoriales": editoriales,
    }

    return render(
        request,
        "biblioteca_app/editorial/dashboard.html",
        context
    )


# ============================================================
# LECTOR - LISTAR
# ============================================================

@admin_required
def lector_list(request):
    """Lista y filtra lectores."""
    lectores = Lector.objects.all().order_by("ApellidoP", "ApellidoM", "Nombres")
    q = request.GET.get("q", "").strip()
    if q:
        from django.db.models import Q
        lectores = lectores.filter(
            Q(Nombres__icontains=q) |
            Q(ApellidoP__icontains=q) |
            Q(ApellidoM__icontains=q)
        )

    return render(
        request,
        "biblioteca_app/lector/list.html",
        {
            "lectores": lectores
        }
    )


# ============================================================
# LECTOR - CREAR
# ============================================================

@admin_required
def lector_create(request):

    """Gestiona la operación lector create dentro de la aplicación."""
    if request.method == "POST":

        form = LectorForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect(
                "lector_list"
            )

    else:

        form = LectorForm()

    return render(
        request,
        "biblioteca_app/lector/form.html",
        {
            "form": form,
            "titulo": "Nuevo lector",
        }
    )


# ============================================================
# LECTOR - EDITAR
# ============================================================

@admin_required
def lector_update(request, pk):

    """Gestiona la operación lector update dentro de la aplicación."""
    lector = get_object_or_404(
        Lector,
        pk=pk
    )

    if request.method == "POST":

        form = LectorForm(
            request.POST,
            instance=lector
        )

        if form.is_valid():

            form.save()

            registrar_log(request, 'EDITAR', 'Lectores', f'Lector editado: {lector}.')

            return redirect(
                "lector_list"
            )

    else:

        form = LectorForm(
            instance=lector
        )

    return render(
        request,
        "biblioteca_app/lector/form.html",
        {
            "form": form,
            "titulo": "Editar lector",
        }
    )


# ============================================================
# LECTOR - ELIMINAR
# ============================================================

@admin_required
def lector_delete(request, pk):

    """Gestiona la operación lector delete dentro de la aplicación."""
    lector = get_object_or_404(
        Lector,
        pk=pk
    )

    if request.method == "POST":

        registrar_log(request, 'ELIMINAR', 'Lectores', f'Lector eliminado: {lector}.')
        lector.delete()

        return redirect(
            "lector_list"
        )

    return render(
        request,
        "biblioteca_app/lector/delete.html",
        {
            "lector": lector
        }
    )


# ============================================================
# LIBRO - LISTAR
# ============================================================

@admin_required
def libro_list(request):
    """Lista y filtra libros del catálogo."""
    libros = Libro.objects.all().order_by("Titulo")
    q = request.GET.get("q", "").strip()
    if q:
        libros = libros.filter(Titulo__icontains=q)

    return render(
        request,
        "biblioteca_app/libro/list.html",
        {
            "libros": libros
        }
    )


# ============================================================
# LIBRO - CREAR
# ============================================================

@admin_required
def libro_create(request):

    """Gestiona la operación libro create dentro de la aplicación."""
    if request.method == "POST":

        indice = request.POST.get(
            "result_index"
        )

        resultados = request.session.get(
            "libro_busqueda_resultados",
            []
        )

        if indice is None:

            return render(
                request,
                "biblioteca_app/libro/form.html",
                {
                    "error": "No se seleccionó ningún libro.",
                    "resultados": resultados,
                    "query": request.GET.get(
                        "q",
                        ""
                    ),
                }
            )

        try:

            indice = int(indice)

        except (
            ValueError,
            TypeError
        ):

            return render(
                request,
                "biblioteca_app/libro/form.html",
                {
                    "error": "La selección del libro no es válida.",
                    "resultados": resultados,
                }
            )

        if (
            indice < 0
            or indice >= len(resultados)
        ):

            return render(
                request,
                "biblioteca_app/libro/form.html",
                {
                    "error": (
                        "El resultado seleccionado ya no está "
                        "disponible. Realiza nuevamente la búsqueda."
                    ),
                    "resultados": resultados,
                }
            )

        resultado = resultados[indice]

        titulo = resultado.get(
            "title",
            ""
        ).strip()

        autores = [
            normalizar_nombre(nombre)
            for nombre in resultado.get(
                "authors",
                []
            )
        ]

        autores = list(
            dict.fromkeys(
                nombre
                for nombre in autores
                if nombre
            )
        )

        editoriales = [
            normalizar_nombre(nombre)
            for nombre in resultado.get(
                "publishers",
                []
            )
        ]

        editoriales = list(
            dict.fromkeys(
                nombre
                for nombre in editoriales
                if nombre
            )
        )

        if not titulo:

            return render(
                request,
                "biblioteca_app/libro/form.html",
                {
                    "error": (
                        "Open Library no entregó "
                        "un título válido."
                    ),
                    "resultados": resultados,
                }
            )

        if not autores:

            return render(
                request,
                "biblioteca_app/libro/form.html",
                {
                    "error": (
                        "El libro seleccionado no tiene "
                        "autores disponibles en el catálogo."
                    ),
                    "resultados": resultados,
                }
            )

        # ====================================================
        # BUSCAR EDITORIAL SI NO VIENE EN LA BÚSQUEDA
        # ====================================================

        if not editoriales:

            key = resultado.get(
                "key",
                ""
            )

            if key.startswith(
                "/works/"
            ):

                try:

                    editions_url = (
                        f"https://openlibrary.org"
                        f"{key}/editions.json"
                    )

                    response = requests.get(
                        editions_url,
                        params={
                            "limit": 5
                        },
                        headers=OPEN_LIBRARY_HEADERS,
                        timeout=10
                    )

                    response.raise_for_status()

                    editions_data = response.json()

                    entradas = editions_data.get(
                        "entries",
                        []
                    )

                    for edition in entradas:

                        publishers = edition.get(
                            "publishers",
                            []
                        )

                        for publisher in publishers:

                            nombre_editorial = (
                                normalizar_nombre(
                                    publisher
                                )
                            )

                            if nombre_editorial:

                                editoriales.append(
                                    nombre_editorial
                                )

                        if editoriales:
                            break

                    editoriales = list(
                        dict.fromkeys(
                            editoriales
                        )
                    )

                except (
                    requests.RequestException,
                    ValueError
                ):

                    editoriales = []

        if not editoriales:

            return render(
                request,
                "biblioteca_app/libro/form.html",
                {
                    "error": (
                        "No fue posible obtener una editorial "
                        "para este libro desde el catálogo."
                    ),
                    "resultados": resultados,
                }
            )

        nombre_editorial = editoriales[0]

        # ====================================================
        # COMPROBAR LIBRO DUPLICADO
        # ====================================================

        libro_existente = Libro.objects.filter(
            Titulo__iexact=titulo
        ).first()

        if libro_existente:

            return render(
                request,
                "biblioteca_app/libro/form.html",
                {
                    "error": (
                        f'El libro "{titulo}" ya existe '
                        f'en la biblioteca.'
                    ),
                    "resultados": resultados,
                }
            )

        # ====================================================
        # CREAR LIBRO Y RELACIONES
        # ====================================================

        try:

            with transaction.atomic():

                libro = Libro.objects.create(
                    Titulo=titulo,
                    PortadaURL=resultado.get("cover", "") or ""
                )

                # ============================================
                # AUTORES
                # ============================================

                for nombre_autor in autores:

                    autor = Autor.objects.filter(
                        NombreAutor__iexact=nombre_autor
                    ).first()

                    if not autor:

                        autor = Autor.objects.create(
                            NombreAutor=nombre_autor
                        )

                    relacion_existe = (
                        LibroAutor.objects.filter(
                            CodLibro=libro,
                            CodAutor=autor
                        ).exists()
                    )

                    if not relacion_existe:

                        LibroAutor.objects.create(
                            CodLibro=libro,
                            CodAutor=autor
                        )

                # ============================================
                # EDITORIAL
                # ============================================

                editorial = Editorial.objects.filter(
                    NombreEditorial__iexact=nombre_editorial
                ).first()

                if not editorial:

                    editorial = Editorial.objects.create(
                        NombreEditorial=nombre_editorial
                    )

                relacion_editorial_existe = (
                    LibroEditorial.objects.filter(
                        CodLibro=libro,
                        CodEditorial=editorial
                    ).exists()
                )

                if not relacion_editorial_existe:

                    LibroEditorial.objects.create(
                        CodLibro=libro,
                        CodEditorial=editorial
                    )

        except Exception as error:

            return render(
                request,
                "biblioteca_app/libro/form.html",
                {
                    "error": (
                        "Ocurrió un error al registrar "
                        f"el libro: {error}"
                    ),
                    "resultados": resultados,
                }
            )

        request.session.pop(
            "libro_busqueda_resultados",
            None
        )

        return redirect(
            "libro_dashboard"
        )

    # ========================================================
    # BÚSQUEDA OPEN LIBRARY
    # ========================================================

    query = request.GET.get(
        "q",
        ""
    ).strip()

    resultados = []

    error = None

    if query:

        try:

            response = requests.get(
                OPEN_LIBRARY_SEARCH_URL,
                params={
                    "q": query,
                    "limit": 10,
                    "fields": (
                        "key,title,author_name,"
                        "publisher,first_publish_year,cover_i"
                    ),
                },
                headers=OPEN_LIBRARY_HEADERS,
                timeout=10
            )

            response.raise_for_status()

            data = response.json()

            for doc in data.get(
                "docs",
                []
            ):

                titulo = doc.get(
                    "title",
                    ""
                )

                autores = doc.get(
                    "author_name",
                    []
                )

                editoriales = doc.get(
                    "publisher",
                    []
                )

                cover_id = doc.get(
                    "cover_i"
                )

                cover_url = ""

                if cover_id:

                    cover_url = (
                        "https://covers.openlibrary.org/"
                        f"b/id/{cover_id}-M.jpg"
                    )

                resultados.append(
                    {
                        "key": doc.get(
                            "key",
                            ""
                        ),

                        "title": titulo,

                        "authors": autores[:10],

                        "publishers": editoriales[:5],

                        "year": doc.get(
                            "first_publish_year"
                        ),

                        "cover": cover_url,
                    }
                )

            request.session[
                "libro_busqueda_resultados"
            ] = resultados

        except requests.RequestException:

            error = (
                "No fue posible conectarse con Open Library. "
                "Verifica tu conexión a Internet e inténtalo nuevamente."
            )

        except ValueError:

            error = (
                "Open Library devolvió una respuesta no válida."
            )

    return render(
        request,
        "biblioteca_app/libro/form.html",
        {
            "resultados": resultados,
            "query": query,
            "error": error,
        }
    )



# ============================================================
# LECTOR - PEDIR PRÉSTAMO
# ============================================================

@lector_required
def pedir_prestamo(request, codlibro):
    """Permite al lector solicitar un préstamo de un libro."""

    lector = request.user.perfil.lector

    # Esta vista corresponde únicamente al préstamo de un libro del catálogo.
    # La búsqueda de libros externos utiliza la vista independiente solicitar_libro.
    if request.method != "POST":
        return redirect("libros_lector")
    libro = get_object_or_404(Libro, CodLibro=codlibro)

    # Evitar solicitudes duplicadas activas.
    solicitud_activa = SolicitudPrestamo.objects.filter(
        CodLibro=libro,
        CodLector=lector,
        Estado__in=["PENDIENTE", "APROBADA"]
    ).exists()

    if solicitud_activa:
        return redirect("libros_lector")

    # Evitar solicitar un libro que ya tiene un préstamo activo.
    prestamo_activo = Prestamo.objects.filter(
        CodLibro=libro,
        CodLector=lector
    ).exists()

    if prestamo_activo:
        return redirect("mis_prestamos")

    fecha_solicitada = request.POST.get("FechaDevSolicitada") or None

    SolicitudPrestamo.objects.create(
        CodLibro=libro,
        CodLector=lector,
        FechaDevSolicitada=fecha_solicitada,
        Estado="PENDIENTE",
        Observacion=""
    )

    registrar_log(
        request,
        'SOLICITUD',
        'Solicitudes de libros',
        f'{lector} solicitó incorporar el libro: {solicitud.Titulo}.',
    )

    return redirect("libros_lector")


# ============================================================
# SOLICITUDES DE PRÉSTAMO - ADMINISTRACIÓN
# ============================================================

@admin_required
def solicitud_prestamo_list(request):
    """Lista las solicitudes de préstamo para administración."""

    solicitudes = SolicitudPrestamo.objects.select_related(
        "CodLibro",
        "CodLector"
    ).all()

    filtro = request.GET.get("estado", "").upper().strip()

    if filtro in {"PENDIENTE", "APROBADA", "RECHAZADA", "COMPLETADA"}:
        solicitudes = solicitudes.filter(Estado=filtro)

    return render(
        request,
        "biblioteca_app/solicitud_prestamo/list.html",
        {
            "solicitudes": solicitudes,
            "filtro_actual": filtro,
        }
    )


@admin_required
def solicitud_prestamo_aprobar(request, pk):
    """Aprueba una solicitud y genera el préstamo activo."""

    solicitud = get_object_or_404(
        SolicitudPrestamo,
        CodSolicitud=pk
    )

    if request.method != "POST":
        return redirect("solicitud_prestamo_list")

    if solicitud.Estado != "PENDIENTE":
        return redirect("solicitud_prestamo_list")

    fecha_dev = solicitud.FechaDevSolicitada

    if not fecha_dev:
        return redirect("solicitud_prestamo_list")

    # No permitir aprobar si ya existe un préstamo activo.
    existe = Prestamo.objects.filter(
        CodLibro=solicitud.CodLibro,
        CodLector=solicitud.CodLector
    ).exists()

    if existe:
        registrar_log(request, 'PRESTAMO', 'Solicitudes de préstamo', f'Solicitud #{solicitud.CodSolicitud} aprobada y préstamo generado para {solicitud.CodLector}.')
        solicitud.Estado = "APROBADA"
        solicitud.FechaRespuesta = timezone.now()
        solicitud.Observacion = "Ya existía un préstamo activo para este libro."
        solicitud.save(
            update_fields=[
                "Estado",
                "FechaRespuesta",
                "Observacion"
            ]
        )
        return redirect("solicitud_prestamo_list")

    with transaction.atomic():
        Prestamo.objects.create(
            CodLibro=solicitud.CodLibro,
            CodLector=solicitud.CodLector,
            FechaDev=fecha_dev
        )

        solicitud.Estado = "APROBADA"
        solicitud.FechaRespuesta = timezone.now()
        solicitud.Observacion = "Solicitud aprobada y préstamo generado."
        solicitud.save(
            update_fields=[
                "Estado",
                "FechaRespuesta",
                "Observacion"
            ]
        )

    return redirect("solicitud_prestamo_list")


@admin_required
def solicitud_prestamo_rechazar(request, pk):
    """Rechaza una solicitud de préstamo."""

    solicitud = get_object_or_404(
        SolicitudPrestamo,
        CodSolicitud=pk
    )

    if request.method == "POST":
        observacion = request.POST.get("Observacion", "").strip()

        registrar_log(
            request,
            'RECHAZO',
            'Solicitudes de libros',
            f'Solicitud #{solicitud.CodSolicitud} rechazada: {solicitud.Titulo}.',
        )

        registrar_log(request, 'RECHAZO', 'Solicitudes de préstamo', f'Solicitud #{solicitud.CodSolicitud} rechazada para {solicitud.CodLector}.')
        solicitud.Estado = "RECHAZADA"
        solicitud.FechaRespuesta = timezone.now()
        solicitud.Observacion = (
            observacion
            or "Solicitud rechazada por el administrador."
        )

        solicitud.save(
            update_fields=[
                "Estado",
                "FechaRespuesta",
                "Observacion"
            ]
        )

    return redirect("solicitud_prestamo_list")


# ============================================================
# SOLICITUD DE INCORPORACIÓN DE LIBROS
# ============================================================

@lector_required
def solicitar_libro(request):
    """
    Permite al lector solicitar que la biblioteca incorpore
    un libro que no se encuentra en el catálogo local.
    """

    lector = request.user.perfil.lector

    # En GET mostramos la vista exclusiva de solicitud de libros.
    # En POST conservamos el procesamiento de la solicitud existente.
    if request.method == "GET":
        solicitudes_libro = SolicitudLibro.objects.filter(
            CodLector=lector
        ).order_by("-FechaSolicitud")[:10]

        return render(
            request,
            "biblioteca_app/lector/solicitar_libro.html",
            {"solicitudes_libro": solicitudes_libro},
        )

    if request.method != "POST":
        return redirect("solicitar_libro")

    titulo = request.POST.get("Titulo", "").strip()
    autor = request.POST.get("Autor", "").strip()
    editorial = request.POST.get("Editorial", "").strip()
    anio_raw = request.POST.get("Anio", "").strip()
    portada = request.POST.get("PortadaURL", "").strip()

    # Convertimos el año a entero solamente cuando el usuario lo entrega.
    # Esto evita guardar texto no válido en el campo numérico del modelo.
    anio = None

    if anio_raw:
        try:
            anio = int(anio_raw)
        except ValueError:
            anio = None
    open_library_key = request.POST.get("OpenLibraryKey", "").strip()

    if not titulo:
        return redirect("solicitar_libro")

    # Si el libro ya existe en el catálogo, no corresponde crear
    # una solicitud de incorporación. El lector puede solicitar
    # directamente un préstamo desde el catálogo.
    libro_existente = Libro.objects.filter(
        Titulo__iexact=titulo
    ).exists()

    if libro_existente:
        return redirect("solicitar_libro")

    # Evitar solicitudes duplicadas que todavía estén activas.
    duplicada = SolicitudLibro.objects.filter(
        CodLector=lector,
        Titulo__iexact=titulo,
        Estado__in=["PENDIENTE", "EN_ADQUISICION"]
    ).exists()

    if duplicada:
        return redirect("solicitar_libro")

    solicitud = SolicitudLibro.objects.create(
        CodLector=lector,
        Titulo=titulo,
        Autor=autor,
        Editorial=editorial,
        Anio=anio,
        PortadaURL=portada,
        OpenLibraryKey=open_library_key,
        Estado="PENDIENTE",
        Observacion=""
    )

    return redirect("solicitar_libro")


@admin_required
def solicitud_libro_list(request):
    """Lista las solicitudes de incorporación de libros."""

    solicitudes = SolicitudLibro.objects.select_related(
        "CodLector",
        "CodLibro"
    ).all()

    filtro = request.GET.get("estado", "").upper().strip()

    if filtro in {
        "PENDIENTE",
        "EN_ADQUISICION",
        "ADQUIRIDA",
        "RECHAZADA"
    }:
        solicitudes = solicitudes.filter(Estado=filtro)

    return render(
        request,
        "biblioteca_app/solicitud_libro/list.html",
        {
            "solicitudes": solicitudes,
            "filtro_actual": filtro,
        }
    )


@admin_required
def solicitud_libro_aprobar(request, pk):
    """
    Marca una solicitud como EN_ADQUISICION.

    Esta acción no crea todavía el libro en el catálogo porque la
    aprobación administrativa significa que la biblioteca decidió
    gestionar la adquisición, pero el libro aún no ha llegado.
    """

    solicitud = get_object_or_404(
        SolicitudLibro,
        CodSolicitud=pk
    )

    if request.method != "POST":
        return redirect("solicitud_libro_list")

    if solicitud.Estado != "PENDIENTE":
        return redirect("solicitud_libro_list")

    registrar_log(
        request,
        'SOLICITUD',
        'Solicitudes de libros',
        f'Solicitud #{solicitud.CodSolicitud} aprobada para adquisición: {solicitud.Titulo}.',
    )

    solicitud.Estado = "EN_ADQUISICION"
    solicitud.FechaRespuesta = timezone.now()
    solicitud.Observacion = (
        "Solicitud aprobada. La biblioteca gestionará la adquisición "
        "del libro."
    )
    solicitud.save(
        update_fields=[
            "Estado",
            "FechaRespuesta",
            "Observacion"
        ]
    )

    return redirect("solicitud_libro_list")


@admin_required
def solicitud_libro_adquirir(request, pk):
    """
    Registra que el libro solicitado fue adquirido e incorpora
    la obra al catálogo, asociando autor y editorial cuando existen.
    """

    solicitud = get_object_or_404(
        SolicitudLibro,
        CodSolicitud=pk
    )

    if request.method != "POST":
        return redirect("solicitud_libro_list")

    if solicitud.Estado != "EN_ADQUISICION":
        return redirect("solicitud_libro_list")

    titulo = solicitud.Titulo.strip()

    if not titulo:
        return redirect("solicitud_libro_list")

    with transaction.atomic():

        # Reutilizar un libro existente evita duplicar el catálogo.
        libro = Libro.objects.filter(
            Titulo__iexact=titulo
        ).first()

        if not libro:
            libro = Libro.objects.create(
                Titulo=titulo,
                PortadaURL=solicitud.PortadaURL or ""
            )
        elif not libro.PortadaURL and solicitud.PortadaURL:
            libro.PortadaURL = solicitud.PortadaURL
            libro.save(update_fields=["PortadaURL"])

        # ========================================================
        # AUTORES
        # ========================================================

        if solicitud.Autor.strip():
            nombres_autores = [
                nombre.strip()
                for nombre in solicitud.Autor.split(",")
                if nombre.strip()
            ]

            for nombre_autor in nombres_autores:

                autor = Autor.objects.filter(
                    NombreAutor__iexact=nombre_autor
                ).first()

                if not autor:
                    autor = Autor.objects.create(
                        NombreAutor=nombre_autor
                    )

                if not LibroAutor.objects.filter(
                    CodLibro=libro,
                    CodAutor=autor
                ).exists():
                    LibroAutor.objects.create(
                        CodLibro=libro,
                        CodAutor=autor
                    )

        # ========================================================
        # EDITORIAL
        # ========================================================

        if solicitud.Editorial.strip():
            editorial = Editorial.objects.filter(
                NombreEditorial__iexact=solicitud.Editorial.strip()
            ).first()

            if not editorial:
                editorial = Editorial.objects.create(
                    NombreEditorial=solicitud.Editorial.strip()
                )

            if not LibroEditorial.objects.filter(
                CodLibro=libro,
                CodEditorial=editorial
            ).exists():
                LibroEditorial.objects.create(
                    CodLibro=libro,
                    CodEditorial=editorial
                )

        # ========================================================
        # CERRAR SOLICITUD COMO ADQUIRIDA
        # ========================================================

        registrar_log(
            request,
            'ADQUISICION',
            'Solicitudes de libros',
            f'Libro adquirido e incorporado al catálogo: {libro.Titulo}.',
        )

        solicitud.CodLibro = libro
        solicitud.Estado = "ADQUIRIDA"
        solicitud.FechaAdquisicion = timezone.now()
        solicitud.Observacion = (
            "Libro adquirido e incorporado al catálogo. "
            "Ya puede ser solicitado para préstamo."
        )

        solicitud.save(
            update_fields=[
                "CodLibro",
                "Estado",
                "FechaAdquisicion",
                "Observacion"
            ]
        )

    return redirect("solicitud_libro_list")


@admin_required
def solicitud_libro_rechazar(request, pk):
    """Rechaza una solicitud de incorporación de libro."""

    solicitud = get_object_or_404(
        SolicitudLibro,
        CodSolicitud=pk
    )

    if request.method == "POST" and solicitud.Estado in {
        "PENDIENTE",
        "EN_ADQUISICION"
    }:
        observacion = request.POST.get("Observacion", "").strip()

        solicitud.Estado = "RECHAZADA"
        solicitud.FechaRespuesta = timezone.now()
        solicitud.Observacion = (
            observacion
            or "Solicitud rechazada por el administrador."
        )

        solicitud.save(
            update_fields=[
                "Estado",
                "FechaRespuesta",
                "Observacion"
            ]
        )

    return redirect("solicitud_libro_list")


# ============================================================
# LIBRO - EDITAR
# ============================================================

@admin_required
def libro_update(request, pk):

    """Gestiona la operación libro update dentro de la aplicación."""
    libro = get_object_or_404(
        Libro,
        pk=pk
    )

    if request.method == "POST":

        form = LibroForm(
            request.POST,
            instance=libro
        )

        if form.is_valid():

            form.save()

            registrar_log(request, 'EDITAR', 'Libros', f'Libro editado: {libro.Titulo}.')

            return redirect(
                "libro_list"
            )

    else:

        form = LibroForm(
            instance=libro
        )

    return render(
        request,
        "biblioteca_app/libro/form.html",
        {
            "form": form,
            "titulo": "Editar libro",
            "modo_edicion": True,
        }
    )


# ============================================================
# LIBRO - ELIMINAR
# ============================================================

@admin_required
def libro_delete(request, pk):

    """Gestiona la operación libro delete dentro de la aplicación."""
    libro = get_object_or_404(
        Libro,
        pk=pk
    )

    if request.method == "POST":

        registrar_log(request, 'ELIMINAR', 'Libros', f'Libro eliminado: {libro.Titulo}.')
        libro.delete()

        return redirect(
            "libro_list"
        )

    return render(
        request,
        "biblioteca_app/libro/delete.html",
        {
            "libro": libro
        }
    )


# ============================================================
# AUTOR - LISTAR
# ============================================================

@admin_required
def autor_list(request):
    """Lista y filtra autores."""
    autores = Autor.objects.all().order_by("NombreAutor")
    q = request.GET.get("q", "").strip()
    if q:
        autores = autores.filter(NombreAutor__icontains=q)

    return render(
        request,
        "biblioteca_app/autor/list.html",
        {
            "autores": autores
        }
    )


# ============================================================
# AUTOR - CREAR
# ============================================================

@admin_required
def autor_create(request):

    """Gestiona la operación autor create dentro de la aplicación."""
    if request.method == "POST":

        form = AutorForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect(
                "autor_list"
            )

    else:

        form = AutorForm()

    return render(
        request,
        "biblioteca_app/autor/form.html",
        {
            "form": form,
            "titulo": "Nuevo autor",
        }
    )


# ============================================================
# AUTOR - EDITAR
# ============================================================

@admin_required
def autor_update(request, pk):

    """Gestiona la operación autor update dentro de la aplicación."""
    autor = get_object_or_404(
        Autor,
        pk=pk
    )

    if request.method == "POST":

        form = AutorForm(
            request.POST,
            instance=autor
        )

        if form.is_valid():

            form.save()

            registrar_log(request, 'EDITAR', 'Autores', f'Autor editado: {autor.NombreAutor}.')

            return redirect(
                "autor_list"
            )

    else:

        form = AutorForm(
            instance=autor
        )

    return render(
        request,
        "biblioteca_app/autor/form.html",
        {
            "form": form,
            "titulo": "Editar autor",
        }
    )


# ============================================================
# AUTOR - ELIMINAR
# ============================================================

@admin_required
def autor_delete(request, pk):

    """Gestiona la operación autor delete dentro de la aplicación."""
    autor = get_object_or_404(
        Autor,
        pk=pk
    )

    if request.method == "POST":

        registrar_log(request, 'ELIMINAR', 'Autores', f'Autor eliminado: {autor.NombreAutor}.')
        autor.delete()

        return redirect(
            "autor_list"
        )

    return render(
        request,
        "biblioteca_app/autor/delete.html",
        {
            "autor": autor
        }
    )


# ============================================================
# EDITORIAL - LISTAR
# ============================================================

@admin_required
def editorial_list(request):
    """Lista y filtra editoriales."""
    editoriales = Editorial.objects.all().order_by("NombreEditorial")
    q = request.GET.get("q", "").strip()
    if q:
        editoriales = editoriales.filter(NombreEditorial__icontains=q)

    return render(
        request,
        "biblioteca_app/editorial/list.html",
        {
            "editoriales": editoriales
        }
    )


# ============================================================
# EDITORIAL - CREAR
# ============================================================

@admin_required
def editorial_create(request):

    """Gestiona la operación editorial create dentro de la aplicación."""
    if request.method == "POST":

        form = EditorialForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect(
                "editorial_list"
            )

    else:

        form = EditorialForm()

    return render(
        request,
        "biblioteca_app/editorial/form.html",
        {
            "form": form,
            "titulo": "Nueva editorial",
        }
    )


# ============================================================
# EDITORIAL - EDITAR
# ============================================================

@admin_required
def editorial_update(request, pk):

    """Gestiona la operación editorial update dentro de la aplicación."""
    editorial = get_object_or_404(
        Editorial,
        pk=pk
    )

    if request.method == "POST":

        form = EditorialForm(
            request.POST,
            instance=editorial
        )

        if form.is_valid():

            form.save()

            registrar_log(request, 'EDITAR', 'Editoriales', f'Editorial editada: {editorial.NombreEditorial}.')

            return redirect(
                "editorial_list"
            )

    else:

        form = EditorialForm(
            instance=editorial
        )

    return render(
        request,
        "biblioteca_app/editorial/form.html",
        {
            "form": form,
            "titulo": "Editar editorial",
        }
    )


# ============================================================
# EDITORIAL - ELIMINAR
# ============================================================

@admin_required
def editorial_delete(request, pk):

    """Gestiona la operación editorial delete dentro de la aplicación."""
    editorial = get_object_or_404(
        Editorial,
        pk=pk
    )

    if request.method == "POST":

        registrar_log(request, 'ELIMINAR', 'Editoriales', f'Editorial eliminada: {editorial.NombreEditorial}.')
        editorial.delete()

        return redirect(
            "editorial_list"
        )

    return render(
        request,
        "biblioteca_app/editorial/delete.html",
        {
            "editorial": editorial
        }
    )


# ============================================================
# PRESTAMO - LISTAR
# ============================================================

@admin_required
def prestamo_list(request):
    """
    Panel de préstamos para administración.

    El estado se calcula automáticamente usando la fecha actual:
    - VIGENTE: faltan más de 3 días.
    - POR VENCER: faltan entre 1 y 3 días.
    - VENCE HOY: la devolución corresponde hoy.
    - VENCIDO: la fecha de devolución ya pasó.

    No requiere modificar el modelo ni crear una migración.
    """

    hoy = date.today()

    prestamos = list(
        Prestamo.objects.select_related(
            "CodLibro",
            "CodLector"
        ).all().order_by(
            "FechaDev"
        )
    )

    for prestamo in prestamos:
        diferencia = (prestamo.FechaDev - hoy).days
        prestamo.dias_restantes = diferencia

        if diferencia < 0:
            prestamo.estado = "VENCIDO"
            prestamo.estado_clase = "vencido"
            prestamo.estado_descripcion = (
                f"{abs(diferencia)} día(s) de atraso"
            )
        elif diferencia == 0:
            prestamo.estado = "VENCE HOY"
            prestamo.estado_clase = "hoy"
            prestamo.estado_descripcion = "Devolución programada para hoy"
        elif diferencia <= 3:
            prestamo.estado = "POR VENCER"
            prestamo.estado_clase = "por-vencer"
            prestamo.estado_descripcion = (
                f"{diferencia} día(s) restante(s)"
            )
        else:
            prestamo.estado = "VIGENTE"
            prestamo.estado_clase = "vigente"
            prestamo.estado_descripcion = (
                f"{diferencia} día(s) restante(s)"
            )

    filtro = request.GET.get("estado", "").upper().strip()

    if filtro in {"VIGENTE", "POR VENCER", "VENCE HOY", "VENCIDO"}:
        prestamos = [
            prestamo
            for prestamo in prestamos
            if prestamo.estado == filtro
        ]

    prestamos_todos = Prestamo.objects.all()

    cantidad_total = prestamos_todos.count()
    cantidad_vigentes = 0
    cantidad_por_vencer = 0
    cantidad_hoy = 0
    cantidad_vencidos = 0

    for prestamo in prestamos_todos:
        diferencia = (prestamo.FechaDev - hoy).days

        if diferencia < 0:
            cantidad_vencidos += 1
        elif diferencia == 0:
            cantidad_hoy += 1
        elif diferencia <= 3:
            cantidad_por_vencer += 1
        else:
            cantidad_vigentes += 1

    context = {
        "prestamos": prestamos,
        "cantidad_total": cantidad_total,
        "cantidad_vigentes": cantidad_vigentes,
        "cantidad_por_vencer": cantidad_por_vencer,
        "cantidad_hoy": cantidad_hoy,
        "cantidad_vencidos": cantidad_vencidos,
        "filtro_actual": filtro,
        "hoy": hoy,
    }

    return render(
        request,
        "biblioteca_app/prestamo/list.html",
        context
    )


# ============================================================
# PRESTAMO - CREAR
# ============================================================

@admin_required
def prestamo_create(request):

    """Gestiona la operación prestamo create dentro de la aplicación."""
    if request.method == "POST":

        form = PrestamoForm(
            request.POST
        )

        if form.is_valid():

            libro = form.cleaned_data[
                "CodLibro"
            ]

            lector = form.cleaned_data[
                "CodLector"
            ]

            fecha = form.cleaned_data[
                "FechaDev"
            ]

            existe = Prestamo.objects.filter(
                CodLibro=libro,
                CodLector=lector
            ).exists()

            if existe:

                form.add_error(
                    None,
                    "Este lector ya tiene un préstamo registrado para este libro."
                )

            else:

                Prestamo.objects.create(
                    CodLibro=libro,
                    CodLector=lector,
                    FechaDev=fecha
                )

                registrar_log(request, 'PRESTAMO', 'Préstamos', f'Préstamo creado: {libro.Titulo} para {lector}.')

                return redirect(
                    "prestamo_list"
                )

    else:

        form = PrestamoForm()

    return render(
        request,
        "biblioteca_app/prestamo/form.html",
        {
            "form": form,
            "titulo": "Nuevo préstamo",
        }
    )


# ============================================================
# PRESTAMO - EDITAR
# ============================================================

@admin_required
def prestamo_update(
    request,
    codlibro,
    codlector
):

    """Gestiona la operación prestamo update dentro de la aplicación."""
    prestamo = get_object_or_404(
        Prestamo,
        CodLibro_id=codlibro,
        CodLector_id=codlector
    )

    if request.method == "POST":

        form = PrestamoForm(
            request.POST,
            instance=prestamo
        )

        if form.is_valid():

            nuevo_libro = form.cleaned_data[
                "CodLibro"
            ]

            nuevo_lector = form.cleaned_data[
                "CodLector"
            ]

            existe = Prestamo.objects.filter(
                CodLibro=nuevo_libro,
                CodLector=nuevo_lector
            ).exclude(
                CodLibro_id=codlibro,
                CodLector_id=codlector
            ).exists()

            if existe:

                form.add_error(
                    None,
                    "Ya existe un préstamo con ese libro y lector."
                )

            else:

                form.save()

                registrar_log(request, 'EDITAR', 'Préstamos', f'Préstamo editado: {prestamo.CodLibro.Titulo} para {prestamo.CodLector}.')

                return redirect(
                    "prestamo_list"
                )

    else:

        form = PrestamoForm(
            instance=prestamo
        )

    return render(
        request,
        "biblioteca_app/prestamo/form.html",
        {
            "form": form,
            "titulo": "Editar préstamo",
        }
    )


# ============================================================
# PRÉSTAMO - REGISTRAR DEVOLUCIÓN
# ============================================================

@admin_required
def prestamo_devolver(request, codlibro, codlector):
    """
    Registra la devolución del préstamo y conserva el historial.
    """

    prestamo = get_object_or_404(
        Prestamo,
        CodLibro_id=codlibro,
        CodLector_id=codlector
    )

    hoy = date.today()
    dias_atraso = max((hoy - prestamo.FechaDev).days, 0)
    estado = 'ATRASADO' if dias_atraso > 0 else 'A_TIEMPO'

    if request.method == 'POST':
        Devolucion.objects.create(
            CodLibro=prestamo.CodLibro,
            CodLector=prestamo.CodLector,
            FechaDevProgramada=prestamo.FechaDev,
            FechaDevolucionReal=hoy,
            DiasAtraso=dias_atraso,
            Estado=estado,
        )

        registrar_log(request, 'DEVOLUCION', 'Devoluciones', f'Devolución registrada: {prestamo.CodLibro.Titulo} / {prestamo.CodLector}.')
        prestamo.delete()

        return redirect('prestamo_list')

    return render(
        request,
        'biblioteca_app/prestamo/devolver.html',
        {
            'prestamo': prestamo,
            'hoy': hoy,
            'dias_atraso': dias_atraso,
            'estado': estado,
        }
    )


# ============================================================
# HISTORIAL DE DEVOLUCIONES
# ============================================================

@admin_required
def devolucion_list(request):
    """Gestiona la operación devolucion list dentro de la aplicación."""
    devoluciones = Devolucion.objects.select_related(
        'CodLibro',
        'CodLector'
    ).all().order_by('-FechaDevolucionReal')

    return render(
        request,
        'biblioteca_app/devolucion/list.html',
        {
            'devoluciones': devoluciones,
        }
    )


# ============================================================
# PRESTAMO - ELIMINAR
# ============================================================

@admin_required
def prestamo_delete(
    request,
    codlibro,
    codlector
):

    """Gestiona la operación prestamo delete dentro de la aplicación."""
    prestamo = get_object_or_404(
        Prestamo,
        CodLibro_id=codlibro,
        CodLector_id=codlector
    )

    if request.method == "POST":

        prestamo.delete()

        return redirect(
            "prestamo_list"
        )

    return render(
        request,
        "biblioteca_app/prestamo/delete.html",
        {
            "prestamo": prestamo
        }
    )


# ============================================================
# LIBRO_AUTOR - LISTAR
# ============================================================

@admin_required
def libro_autor_list(request):

    """Gestiona la operación libro autor list dentro de la aplicación."""
    relaciones = LibroAutor.objects.select_related(
        "CodLibro",
        "CodAutor"
    ).all()

    return render(
        request,
        "biblioteca_app/libro_autor/list.html",
        {
            "relaciones": relaciones
        }
    )


# ============================================================
# LIBRO_AUTOR - CREAR
# ============================================================

@admin_required
def libro_autor_create(request):

    """Gestiona la operación libro autor create dentro de la aplicación."""
    if request.method == "POST":

        form = LibroAutorForm(
            request.POST
        )

        if form.is_valid():

            libro = form.cleaned_data[
                "CodLibro"
            ]

            autor = form.cleaned_data[
                "CodAutor"
            ]

            existe = LibroAutor.objects.filter(
                CodLibro=libro,
                CodAutor=autor
            ).exists()

            if existe:

                form.add_error(
                    None,
                    "Esta relación entre libro y autor ya existe."
                )

            else:

                LibroAutor.objects.create(
                    CodLibro=libro,
                    CodAutor=autor
                )

                return redirect(
                    "libro_autor_list"
                )

    else:

        form = LibroAutorForm()

    return render(
        request,
        "biblioteca_app/libro_autor/form.html",
        {
            "form": form
        }
    )


# ============================================================
# LIBRO_AUTOR - ELIMINAR
# ============================================================

@admin_required
def libro_autor_delete(
    request,
    codlibro,
    codautor
):

    """Gestiona la operación libro autor delete dentro de la aplicación."""
    relacion = get_object_or_404(
        LibroAutor,
        CodLibro_id=codlibro,
        CodAutor_id=codautor
    )

    if request.method == "POST":

        relacion.delete()

        return redirect(
            "libro_autor_list"
        )

    return render(
        request,
        "biblioteca_app/libro_autor/delete.html",
        {
            "relacion": relacion
        }
    )


# ============================================================
# LIBRO_EDITORIAL - LISTAR
# ============================================================

@admin_required
def libro_editorial_list(request):

    """Gestiona la operación libro editorial list dentro de la aplicación."""
    relaciones = LibroEditorial.objects.select_related(
        "CodLibro",
        "CodEditorial"
    ).all()

    return render(
        request,
        "biblioteca_app/libro_editorial/list.html",
        {
            "relaciones": relaciones
        }
    )


# ============================================================
# LIBRO_EDITORIAL - CREAR
# ============================================================

@admin_required
def libro_editorial_create(request):

    """Gestiona la operación libro editorial create dentro de la aplicación."""
    if request.method == "POST":

        form = LibroEditorialForm(
            request.POST
        )

        if form.is_valid():

            libro = form.cleaned_data[
                "CodLibro"
            ]

            editorial = form.cleaned_data[
                "CodEditorial"
            ]

            existe = LibroEditorial.objects.filter(
                CodLibro=libro,
                CodEditorial=editorial
            ).exists()

            if existe:

                form.add_error(
                    None,
                    "Esta relación entre libro y editorial ya existe."
                )

            else:

                LibroEditorial.objects.create(
                    CodLibro=libro,
                    CodEditorial=editorial
                )

                return redirect(
                    "libro_editorial_list"
                )

    else:

        form = LibroEditorialForm()

    return render(
        request,
        "biblioteca_app/libro_editorial/form.html",
        {
            "form": form
        }
    )


# ============================================================
# LIBRO_EDITORIAL - ELIMINAR
# ============================================================

@admin_required
def libro_editorial_delete(
    request,
    codlibro,
    codeditorial
):

    """Gestiona la operación libro editorial delete dentro de la aplicación."""
    relacion = get_object_or_404(
        LibroEditorial,
        CodLibro_id=codlibro,
        CodEditorial_id=codeditorial
    )

    if request.method == "POST":

        relacion.delete()

        return redirect(
            "libro_editorial_list"
        )

    return render(
        request,
        "biblioteca_app/libro_editorial/delete.html",
        {
            "relacion": relacion
        }
    )