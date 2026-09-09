"""
URLs de la aplicación Sistema de Biblioteca.

Este archivo conecta cada dirección web con la vista que debe atenderla.
Las rutas de autenticación y recuperación de contraseña están agrupadas
para que sea sencillo seguir el flujo completo.
"""

# Importa la función utilizada para declarar cada ruta.
from django.urls import path

# Importa las vistas de autenticación de Django.
# Se utilizan para validar el token y completar el cambio de contraseña.
from django.contrib.auth import views as auth_views

# Importa las vistas personalizadas de nuestra aplicación.
from . import views


urlpatterns = [

    # ============================================================
    # AUTENTICACIÓN
    # ============================================================

    # Registro de nuevos lectores mediante un formulario dividido en pasos.
    path("registro/", views.registro, name="registro"),

    # Inicio de sesión del usuario.
    path("login/", views.login_usuario, name="login"),

    # Cierre de sesión.
    path("logout/", views.logout_usuario, name="logout"),

    # Configuración inicial del autenticador 2FA para cuentas nuevas.
    path(
        "two-factor/setup/",
        views.two_factor_setup,
        name="two_factor_setup",
    ),

    # Verificación del código 2FA durante el inicio de sesión.
    path(
        "two-factor/verify/",
        views.two_factor_verify,
        name="two_factor_verify",
    ),

    # ============================================================
    # RECUPERACIÓN DE CONTRASEÑA
    # ============================================================

    # Muestra el formulario de recuperación de contraseña.
    # La vista también puede recibir POST porque controla el formulario.
    path(
        "password-reset/",
        views.password_reset,
        name="password_reset",
    ),

    # Recibe el correo enviado desde password_reset.html,
    # genera el token y prepara el enlace de recuperación.
    path(
        "password-reset/request/",
        views.password_reset_usuario,
        name="password_reset_request",
    ),

    # Valida el token enviado en el enlace de recuperación
    # y muestra el formulario para definir la nueva contraseña.
    path(
        "password-reset/confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name=(
                "biblioteca_app/auth/password/"
                "password_reset_confirm.html"
            )
        ),
        name="password_reset_confirm",
    ),

    # Página mostrada cuando la contraseña ya fue cambiada correctamente.
    path(
        "password-reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name=(
                "biblioteca_app/auth/password/"
                "password_reset_complete.html"
            )
        ),
        name="password_reset_complete",
    ),

    # ============================================================
    # PÁGINA PRINCIPAL Y DASHBOARDS
    # ============================================================

    # Dashboard principal del sistema.
    path("", views.inicio, name="inicio"),

    # Ruta alternativa para el dashboard administrativo.
    path(
        "admin-dashboard/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),

    # Dashboard destinado a los lectores.
    path(
        "lector-dashboard/",
        views.lector_dashboard,
        name="lector_dashboard",
    ),

    # ============================================================
    # LECTORES
    # ============================================================

    # Lista todos los lectores.
    path("lectores/", views.lector_list, name="lector_list"),

    # Formulario para crear un lector.
    path(
        "lectores/nuevo/",
        views.lector_create,
        name="lector_create",
    ),

    # Formulario para editar un lector existente.
    path(
        "lectores/<int:pk>/editar/",
        views.lector_update,
        name="lector_update",
    ),

    # Confirmación para eliminar un lector.
    path(
        "lectores/<int:pk>/eliminar/",
        views.lector_delete,
        name="lector_delete",
    ),

    # ============================================================
    # LIBROS
    # ============================================================

    path(
        "libros/dashboard/",
        views.libro_dashboard,
        name="libro_dashboard",
    ),

    path("libros/", views.libro_list, name="libro_list"),

    path(
        "libros/nuevo/",
        views.libro_create,
        name="libro_create",
    ),

    path(
        "libros/<int:pk>/editar/",
        views.libro_update,
        name="libro_update",
    ),

    path(
        "libros/<int:pk>/eliminar/",
        views.libro_delete,
        name="libro_delete",
    ),

    # ============================================================
    # AUTORES
    # ============================================================

    path(
        "autores/dashboard/",
        views.autor_dashboard,
        name="autor_dashboard",
    ),

    path("autores/", views.autor_list, name="autor_list"),

    path(
        "autores/nuevo/",
        views.autor_create,
        name="autor_create",
    ),

    path(
        "autores/<int:pk>/editar/",
        views.autor_update,
        name="autor_update",
    ),

    path(
        "autores/<int:pk>/eliminar/",
        views.autor_delete,
        name="autor_delete",
    ),

    # ============================================================
    # EDITORIALES
    # ============================================================

    path(
        "editoriales/dashboard/",
        views.editorial_dashboard,
        name="editorial_dashboard",
    ),

    path(
        "editoriales/",
        views.editorial_list,
        name="editorial_list",
    ),

    path(
        "editoriales/nuevo/",
        views.editorial_create,
        name="editorial_create",
    ),

    path(
        "editoriales/<int:pk>/editar/",
        views.editorial_update,
        name="editorial_update",
    ),

    path(
        "editoriales/<int:pk>/eliminar/",
        views.editorial_delete,
        name="editorial_delete",
    ),

    # ============================================================
    # PRÉSTAMOS
    # ============================================================

    path("prestamos/", views.prestamo_list, name="prestamo_list"),

    path(
        "prestamos/nuevo/",
        views.prestamo_create,
        name="prestamo_create",
    ),

    path(
        "prestamos/<int:codlibro>/<int:codlector>/editar/",
        views.prestamo_update,
        name="prestamo_update",
    ),

    path(
        "prestamos/<int:codlibro>/<int:codlector>/devolver/",
        views.prestamo_devolver,
        name="prestamo_devolver",
    ),

    path(
        "prestamos/<int:codlibro>/<int:codlector>/eliminar/",
        views.prestamo_delete,
        name="prestamo_delete",
    ),

    # ============================================================
    # DEVOLUCIONES
    # ============================================================

    path(
        "devoluciones/",
        views.devolucion_list,
        name="devolucion_list",
    ),

    # ============================================================
    # RELACIONES LIBRO - AUTOR
    # ============================================================

    path(
        "libro-autor/",
        views.libro_autor_list,
        name="libro_autor_list",
    ),

    path(
        "libro-autor/nuevo/",
        views.libro_autor_create,
        name="libro_autor_create",
    ),

    path(
        "libro-autor/<int:codlibro>/<int:codautor>/eliminar/",
        views.libro_autor_delete,
        name="libro_autor_delete",
    ),

    # ============================================================
    # RELACIONES LIBRO - EDITORIAL
    # ============================================================

    path(
        "libro-editorial/",
        views.libro_editorial_list,
        name="libro_editorial_list",
    ),

    path(
        "libro-editorial/nuevo/",
        views.libro_editorial_create,
        name="libro_editorial_create",
    ),

    path(
        "libro-editorial/<int:codlibro>/<int:codeditorial>/eliminar/",
        views.libro_editorial_delete,
        name="libro_editorial_delete",
    ),

    # ============================================================
    # FUNCIONES DEL LECTOR
    # ============================================================

    path("mis-prestamos/", views.mis_prestamos, name="mis_prestamos"),

    path(
        "mis-prestamos/<int:codlibro>/<int:codlector>/eliminar/",
        views.prestamo_delete_propio,
        name="mi_prestamo_delete",
    ),

    path(
        "libros-lector/",
        views.libros_lector,
        name="libros_lector",
    ),

    path(
        "libros-lector/pedir/<int:codlibro>/",
        views.pedir_prestamo,
        name="pedir_prestamo",
    ),

    # Endpoint JSON para buscar libros externos mediante Open Library.
    path(
        "lector/open-library/search/",
        views.open_library_buscar,
        name="open_library_buscar",
    ),

    # Vista exclusiva para buscar y solicitar libros que no están en el catálogo.
    path(
        "solicitar-libro/",
        views.solicitar_libro,
        name="solicitar_libro",
    ),

    # Se conserva la URL anterior como alias para no romper enlaces existentes.
    path(
        "libros-lector/solicitar-incorporacion/",
        views.solicitar_libro,
        name="solicitar_libro_legacy",
    ),

    path(
        "historial/",
        views.historial_lector,
        name="historial_lector",
    ),

    path(
        "mis-datos/",
        views.mis_datos,
        name="mis_datos",
    ),

    # ============================================================
    # SOLICITUDES DE PRÉSTAMO
    # ============================================================

    path(
        "solicitudes-prestamos/",
        views.solicitud_prestamo_list,
        name="solicitud_prestamo_list",
    ),

    path(
        "solicitudes-prestamos/<int:pk>/aprobar/",
        views.solicitud_prestamo_aprobar,
        name="solicitud_prestamo_aprobar",
    ),

    path(
        "solicitudes-prestamos/<int:pk>/rechazar/",
        views.solicitud_prestamo_rechazar,
        name="solicitud_prestamo_rechazar",
    ),

    # ============================================================
    # SOLICITUDES DE INCORPORACIÓN DE LIBROS
    # ============================================================

    path(
        "solicitudes-libros/",
        views.solicitud_libro_list,
        name="solicitud_libro_list",
    ),

    path(
        "solicitudes-libros/<int:pk>/aprobar/",
        views.solicitud_libro_aprobar,
        name="solicitud_libro_aprobar",
    ),

    path(
        "solicitudes-libros/<int:pk>/adquirir/",
        views.solicitud_libro_adquirir,
        name="solicitud_libro_adquirir",
    ),

    path(
        "solicitudes-libros/<int:pk>/rechazar/",
        views.solicitud_libro_rechazar,
        name="solicitud_libro_rechazar",
    ),
]
