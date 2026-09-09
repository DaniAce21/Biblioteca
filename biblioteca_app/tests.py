"""
Pruebas del Sistema de Biblioteca.

Estas pruebas verifican el flujo de solicitud y adquisición de libros.
"""

from datetime import date
from unittest.mock import Mock, patch

from django.test import Client, TestCase
from django.urls import reverse

from .models import (
    Lector,
    Libro,
    SolicitudLibro,
    LibroAutor,
    LibroEditorial,
    LogActividad,
    PerfilUsuario,
)


class SolicitudLibroAdquisicionTests(TestCase):
    """Pruebas principales del flujo de adquisición de un libro."""

    def setUp(self):
        """Prepara un administrador y un lector para cada prueba."""

        self.admin = User.objects.create_user(
            username="admin_test",
            password="Admin123!",
            is_staff=True,
        )

        self.usuario_lector = User.objects.create_user(
            username="lector_test",
            password="Lector123!",
            email="lector@test.cl",
        )

        self.lector = Lector.objects.create(
            ApellidoP="Prueba",
            ApellidoM="Usuario",
            Nombres="Lector",
            Telefono="+56912345678",
            Direccion="Temuco",
        )

        # PerfilUsuario es creado por el flujo real de registro.
        # Para las pruebas se obtiene desde el modelo y se crea directamente.
        from .models import PerfilUsuario

        PerfilUsuario.objects.create(
            usuario=self.usuario_lector,
            lector=self.lector,
            RUT="11.111.111-1",
            tipo_usuario="LECTOR",
        )

    def test_solicitud_lector_se_crea_pendiente(self):
        """Una solicitud nueva debe iniciar en estado PENDIENTE."""

        self.client.login(
            username="lector_test",
            password="Lector123!",
        )

        response = self.client.post(
            reverse("solicitar_libro"),
            {
                "Titulo": "Clean Code",
                "Autor": "Robert C. Martin",
                "Editorial": "Prentice Hall",
                "Anio": "2008",
            },
        )

        self.assertRedirects(response, reverse("libros_lector"))

        solicitud = SolicitudLibro.objects.get(
            Titulo="Clean Code"
        )

        self.assertEqual(solicitud.Estado, "PENDIENTE")
        self.assertIsNone(solicitud.CodLibro)

    def test_admin_puede_pasar_a_adquisicion_y_luego_adquirir(self):
        """El administrador debe separar la aprobación de la adquisición real."""

        solicitud = SolicitudLibro.objects.create(
            CodLector=self.lector,
            Titulo="Clean Architecture",
            Autor="Robert C. Martin",
            Editorial="Prentice Hall",
            Anio=2017,
            Estado="PENDIENTE",
        )

        self.client.login(
            username="admin_test",
            password="Admin123!",
        )

        response = self.client.post(
            reverse(
                "solicitud_libro_aprobar",
                args=[solicitud.CodSolicitud],
            )
        )

        self.assertRedirects(
            response,
            reverse("solicitud_libro_list"),
        )

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.Estado, "EN_ADQUISICION")
        self.assertIsNone(solicitud.CodLibro)

        response = self.client.post(
            reverse(
                "solicitud_libro_adquirir",
                args=[solicitud.CodSolicitud],
            )
        )

        self.assertRedirects(
            response,
            reverse("solicitud_libro_list"),
        )

        solicitud.refresh_from_db()
        self.assertEqual(solicitud.Estado, "ADQUIRIDA")
        self.assertIsNotNone(solicitud.CodLibro)
        self.assertIsNotNone(solicitud.FechaAdquisicion)

        self.assertTrue(
            Libro.objects.filter(
                Titulo__iexact="Clean Architecture"
            ).exists()
        )
        self.assertTrue(
            LibroAutor.objects.filter(
                CodLibro=solicitud.CodLibro,
            ).exists()
        )
        self.assertTrue(
            LibroEditorial.objects.filter(
                CodLibro=solicitud.CodLibro,
            ).exists()
        )


class LogActividadTests(TestCase):
    """Verifica la persistencia de un evento de auditoría al iniciar sesión."""

    def test_login_genera_log(self):
        usuario = User.objects.create_user(
            username='auditor_test',
            password='Auditor123!',
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': 'auditor_test',
                'password': 'Auditor123!',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            LogActividad.objects.filter(
                usuario=usuario,
                accion='LOGIN',
            ).exists()
        )


# ============================================================
# PRUEBAS DE OPEN LIBRARY
# ============================================================

class OpenLibrarySearchTests(TestCase):
    """Comprueba la búsqueda externa sin depender de Internet real."""

    def setUp(self):
        """Crea un lector de prueba y lo autentica para consumir el endpoint."""
        self.user = User.objects.create_user(
            username="lector_openlibrary",
            password="PruebaSegura123!",
        )

        lector = Lector.objects.create(
            ApellidoP="Prueba",
            ApellidoM="Lector",
            Nombres="Open Library",
            Telefono="",
            Direccion="",
        )

        PerfilUsuario.objects.create(
            usuario=self.user,
            RUT="99.999.999-9",
            tipo_usuario="LECTOR",
            lector=lector,
        )

        self.client = Client()
        self.client.force_login(self.user)

    @patch("biblioteca_app.views.requests.get")
    def test_busqueda_open_library_devuelve_libro(self, mock_get):
        """Verifica que el endpoint transforme correctamente los datos recibidos."""
        response_mock = Mock()
        response_mock.raise_for_status.return_value = None
        response_mock.json.return_value = {
            "docs": [
                {
                    "key": "/works/OL123W",
                    "title": "Clean Code",
                    "author_name": ["Robert C. Martin"],
                    "publisher": ["Prentice Hall"],
                    "first_publish_year": 2008,
                    "cover_i": 123456,
                    "isbn": ["9780132350884"],
                }
            ]
        }
        mock_get.return_value = response_mock

        response = self.client.get(
            "/lector/open-library/search/?q=Clean%20Code"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["resultados"]), 1)
        self.assertEqual(data["resultados"][0]["titulo"], "Clean Code")
        self.assertEqual(data["resultados"][0]["autor"], "Robert C. Martin")
        self.assertIn("covers.openlibrary.org", data["resultados"][0]["portada"])

