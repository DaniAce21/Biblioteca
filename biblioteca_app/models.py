"""Módulo models.

Contiene la implementación de models.py del Sistema de Biblioteca.
"""

from django.db import models
from django.contrib.auth.models import User


# ============================================================
# LECTOR
# ============================================================

class Lector(models.Model):

    """Representa la clase lector y encapsula la lógica relacionada con este componente."""
    CodLector = models.AutoField(
        primary_key=True,
        db_column='CodLector'
    )

    ApellidoP = models.CharField(
        max_length=100,
        db_column='ApellidoP'
    )

    ApellidoM = models.CharField(
        max_length=100,
        db_column='ApellidoM'
    )

    Nombres = models.CharField(
        max_length=100,
        db_column='Nombres'
    )

    Telefono = models.CharField(
        max_length=20,
        blank=True,
        default='',
        db_column='Telefono'
    )

    Direccion = models.CharField(
        max_length=200,
        blank=True,
        default='',
        db_column='Direccion'
    )

    class Meta:
        db_table = 'LECTOR'

    def __str__(self):
        """Devuelve una representación legible de la instancia para mostrarla en el sistema."""
        return f"{self.Nombres} {self.ApellidoP} {self.ApellidoM}"


# ============================================================
# LIBRO
# ============================================================

class Libro(models.Model):

    """Representa la clase libro y encapsula la lógica relacionada con este componente."""
    CodLibro = models.AutoField(
        primary_key=True,
        db_column='CodLibro'
    )

    Titulo = models.CharField(
        max_length=200,
        db_column='Titulo'
    )

    # URL de la carátula del libro.
    # Se obtiene principalmente desde Open Library.
    PortadaURL = models.URLField(
        max_length=500,
        blank=True,
        default='',
        db_column='PortadaURL'
    )

    class Meta:
        db_table = 'LIBRO'

    def __str__(self):
        """Devuelve una representación legible de la instancia para mostrarla en el sistema."""
        return self.Titulo


# ============================================================
# AUTOR
# ============================================================

class Autor(models.Model):

    """Representa la clase autor y encapsula la lógica relacionada con este componente."""
    CodAutor = models.AutoField(
        primary_key=True,
        db_column='CodAutor'
    )

    NombreAutor = models.CharField(
        max_length=150,
        db_column='NombreAutor'
    )

    class Meta:
        db_table = 'AUTOR'

    def __str__(self):
        """Devuelve una representación legible de la instancia para mostrarla en el sistema."""
        return self.NombreAutor


# ============================================================
# EDITORIAL
# ============================================================

class Editorial(models.Model):

    """Representa la clase editorial y encapsula la lógica relacionada con este componente."""
    CodEditorial = models.AutoField(
        primary_key=True,
        db_column='CodEditorial'
    )

    NombreEditorial = models.CharField(
        max_length=150,
        db_column='NombreEditorial'
    )

    class Meta:
        db_table = 'EDITORIAL'

    def __str__(self):
        """Devuelve una representación legible de la instancia para mostrarla en el sistema."""
        return self.NombreEditorial


# ============================================================
# PRESTAMO
# ============================================================

class Prestamo(models.Model):

    """Representa la clase prestamo y encapsula la lógica relacionada con este componente."""
    CodLibro = models.ForeignKey(
        Libro,
        on_delete=models.CASCADE,
        db_column='CodLibro',
        related_name='prestamos'
    )

    CodLector = models.ForeignKey(
        Lector,
        on_delete=models.CASCADE,
        db_column='CodLector',
        related_name='prestamos'
    )

    FechaDev = models.DateField(
        db_column='FechaDev'
    )

    # ========================================================
    # PK COMPUESTA
    # ========================================================

    pk = models.CompositePrimaryKey(
        'CodLibro_id',
        'CodLector_id'
    )

    class Meta:
        db_table = 'PRESTAMO'

    def __str__(self):
        """Devuelve una representación legible de la instancia para mostrarla en el sistema."""
        return (
            f"Libro {self.CodLibro_id} - "
            f"Lector {self.CodLector_id}"
        )


# ============================================================
# LIBRO_AUTOR
# ============================================================

class LibroAutor(models.Model):

    """Representa la clase libro autor y encapsula la lógica relacionada con este componente."""
    CodLibro = models.ForeignKey(
        Libro,
        on_delete=models.CASCADE,
        db_column='CodLibro',
        related_name='libro_autores'
    )

    CodAutor = models.ForeignKey(
        Autor,
        on_delete=models.CASCADE,
        db_column='CodAutor',
        related_name='libro_autores'
    )

    # ========================================================
    # PK COMPUESTA
    # ========================================================

    pk = models.CompositePrimaryKey(
        'CodLibro_id',
        'CodAutor_id'
    )

    class Meta:
        db_table = 'LIBRO_AUTOR'

    def __str__(self):
        """Devuelve una representación legible de la instancia para mostrarla en el sistema."""
        return (
            f"Libro {self.CodLibro_id} - "
            f"Autor {self.CodAutor_id}"
        )


# ============================================================
# LIBRO_EDITORIAL
# ============================================================

class LibroEditorial(models.Model):

    """Representa la clase libro editorial y encapsula la lógica relacionada con este componente."""
    CodLibro = models.ForeignKey(
        Libro,
        on_delete=models.CASCADE,
        db_column='CodLibro',
        related_name='libro_editoriales'
    )

    CodEditorial = models.ForeignKey(
        Editorial,
        on_delete=models.CASCADE,
        db_column='CodEditorial',
        related_name='libro_editoriales'
    )

    # ========================================================
    # PK COMPUESTA
    # ========================================================

    pk = models.CompositePrimaryKey(
        'CodLibro_id',
        'CodEditorial_id'
    )

    class Meta:
        db_table = 'LIBRO_EDITORIAL'

    def __str__(self):
        """Devuelve una representación legible de la instancia para mostrarla en el sistema."""
        return (
            f"Libro {self.CodLibro_id} - "
            f"Editorial {self.CodEditorial_id}"
        )


# ============================================================
# DEVOLUCIÓN / HISTORIAL DE PRÉSTAMOS
# ============================================================

class Devolucion(models.Model):

    """
    Registra cada devolución realizada.

    Se mantiene separada de PRESTAMO para conservar el historial
    sin tener que modificar la PK compuesta del modelo original.
    """

    ESTADO_CHOICES = [
        ('A_TIEMPO', 'Devuelto a tiempo'),
        ('ATRASADO', 'Devuelto con atraso'),
    ]

    CodDevolucion = models.AutoField(
        primary_key=True,
        db_column='CodDevolucion'
    )

    CodLibro = models.ForeignKey(
        Libro,
        on_delete=models.PROTECT,
        db_column='CodLibro',
        related_name='devoluciones'
    )

    CodLector = models.ForeignKey(
        Lector,
        on_delete=models.PROTECT,
        db_column='CodLector',
        related_name='devoluciones'
    )

    FechaDevProgramada = models.DateField(
        db_column='FechaDevProgramada'
    )

    FechaDevolucionReal = models.DateField(
        db_column='FechaDevolucionReal'
    )

    DiasAtraso = models.PositiveIntegerField(
        default=0,
        db_column='DiasAtraso'
    )

    Estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        db_column='Estado'
    )

    class Meta:
        db_table = 'DEVOLUCION'
        ordering = [
            '-FechaDevolucionReal',
            '-CodDevolucion'
        ]

    def __str__(self):
        """Devuelve una representación legible de la instancia para mostrarla en el sistema."""
        return (
            f"Devolución #{self.CodDevolucion} - "
            f"Libro {self.CodLibro_id} - "
            f"Lector {self.CodLector_id}"
        )


# ============================================================
# PERFIL DE USUARIO
# ============================================================

class PerfilUsuario(models.Model):

    # ========================================================
    # TIPOS DE USUARIO
    # ========================================================

    """Representa la clase perfil usuario y encapsula la lógica relacionada con este componente."""
    TIPO_USUARIO_CHOICES = [
        ('LECTOR', 'Lector'),
        ('ADMIN', 'Administrador'),
    ]

    # ========================================================
    # RELACIÓN CON EL USUARIO DE DJANGO
    # ========================================================

    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )

    # ========================================================
    # RELACIÓN CON LECTOR
    #
    # Un usuario puede estar asociado a un solo lector.
    #
    # null=True y blank=True permiten que los usuarios
    # administradores no necesiten tener un Lector asociado.
    # ========================================================

    lector = models.OneToOneField(
        Lector,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='perfil_usuario'
    )

    # ========================================================
    # RUT
    # ========================================================

    RUT = models.CharField(
        max_length=12,
        unique=True,
        db_column='RUT'
    )

    # ========================================================
    # TIPO DE USUARIO
    # ========================================================

    tipo_usuario = models.CharField(
        max_length=10,
        choices=TIPO_USUARIO_CHOICES,
        default='LECTOR',
        db_column='TipoUsuario'
    )

    # ========================================================
    # AUTENTICACIÓN DE DOS FACTORES (2FA)
    #
    # La clave secreta se utiliza para generar códigos TOTP de
    # seis dígitos con aplicaciones como Google Authenticator
    # o Microsoft Authenticator.
    # ========================================================

    two_factor_secret = models.CharField(
        max_length=64,
        blank=True,
        default='',
        db_column='TwoFactorSecret'
    )

    two_factor_enabled = models.BooleanField(
        default=False,
        db_column='TwoFactorEnabled'
    )

    two_factor_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        db_column='TwoFactorVerifiedAt'
    )

    class Meta:
        db_table = 'PERFIL_USUARIO'

    def __str__(self):
        """Devuelve una representación legible de la instancia para mostrarla en el sistema."""
        return (
            f"{self.usuario.username} - "
            f"{self.RUT}"
        )


# ============================================================
# SOLICITUD DE PRÉSTAMO
# ============================================================

class SolicitudPrestamo(models.Model):

    """Representa la clase solicitud prestamo y encapsula la lógica relacionada con este componente."""
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('COMPLETADA', 'Completada'),
    ]

    CodSolicitud = models.AutoField(
        primary_key=True,
        db_column='CodSolicitud'
    )

    CodLibro = models.ForeignKey(
        Libro,
        on_delete=models.PROTECT,
        db_column='CodLibro',
        related_name='solicitudes_prestamo'
    )

    CodLector = models.ForeignKey(
        Lector,
        on_delete=models.PROTECT,
        db_column='CodLector',
        related_name='solicitudes_prestamo'
    )

    FechaSolicitud = models.DateTimeField(
        auto_now_add=True,
        db_column='FechaSolicitud'
    )

    Estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        db_column='Estado'
    )

    FechaDevSolicitada = models.DateField(
        null=True,
        blank=True,
        db_column='FechaDevSolicitada'
    )

    FechaRespuesta = models.DateTimeField(
        null=True,
        blank=True,
        db_column='FechaRespuesta'
    )

    Observacion = models.TextField(
        blank=True,
        default='',
        db_column='Observacion'
    )

    class Meta:
        db_table = 'SOLICITUD_PRESTAMO'
        ordering = [
            '-FechaSolicitud',
            '-CodSolicitud'
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'CodLibro',
                    'CodLector'
                ],
                condition=models.Q(
                    Estado__in=[
                        'PENDIENTE',
                        'APROBADA'
                    ]
                ),
                name='solicitud_libro_lector_activa_unica'
            )
        ]

    def __str__(self):
        """Devuelve una representación legible de la instancia para mostrarla en el sistema."""
        return (
            f"Solicitud #{self.CodSolicitud} - "
            f"{self.CodLibro.Titulo} - "
            f"{self.CodLector}"
        )


# ============================================================
# SOLICITUD DE INCORPORACIÓN DE LIBRO
# ============================================================

class SolicitudLibro(models.Model):

    """Representa la clase solicitud libro y encapsula la lógica relacionada con este componente."""
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_ADQUISICION', 'En adquisición'),
        ('ADQUIRIDA', 'Adquirida'),
        ('RECHAZADA', 'Rechazada'),
    ]

    CodSolicitud = models.AutoField(
        primary_key=True,
        db_column='CodSolicitud'
    )

    CodLector = models.ForeignKey(
        Lector,
        on_delete=models.PROTECT,
        db_column='CodLector',
        related_name='solicitudes_libros'
    )

    # Libro asociado cuando la biblioteca confirma que el ejemplar
    # fue adquirido y ya forma parte del catálogo.
    CodLibro = models.ForeignKey(
        Libro,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        db_column='CodLibro',
        related_name='solicitudes_incorporacion'
    )

    Titulo = models.CharField(
        max_length=300,
        db_column='Titulo'
    )

    Autor = models.CharField(
        max_length=300,
        blank=True,
        default='',
        db_column='Autor'
    )

    Editorial = models.CharField(
        max_length=300,
        blank=True,
        default='',
        db_column='Editorial'
    )

    Anio = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_column='Anio'
    )

    PortadaURL = models.URLField(
        max_length=500,
        blank=True,
        default='',
        db_column='PortadaURL'
    )

    OpenLibraryKey = models.CharField(
        max_length=200,
        blank=True,
        default='',
        db_column='OpenLibraryKey'
    )

    FechaSolicitud = models.DateTimeField(
        auto_now_add=True,
        db_column='FechaSolicitud'
    )

    Estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        db_column='Estado'
    )

    FechaRespuesta = models.DateTimeField(
        null=True,
        blank=True,
        db_column='FechaRespuesta'
    )

    # Momento en que el libro fue adquirido e incorporado al catálogo.
    FechaAdquisicion = models.DateTimeField(
        null=True,
        blank=True,
        db_column='FechaAdquisicion'
    )

    Observacion = models.TextField(
        blank=True,
        default='',
        db_column='Observacion'
    )

    class Meta:
        db_table = 'SOLICITUD_LIBRO'
        ordering = [
            '-FechaSolicitud',
            '-CodSolicitud'
        ]

    def __str__(self):
        """Devuelve una representación legible de la instancia para mostrarla en el sistema."""
        return (
            f"Solicitud de libro #{self.CodSolicitud} - "
            f"{self.Titulo}"
        )

# ============================================================
# LOG DE ACTIVIDAD / AUDITORÍA
# ============================================================

class LogActividad(models.Model):

    """Registra de forma persistente las acciones importantes del sistema."""

    ACCION_CHOICES = [
        ('LOGIN', 'Inicio de sesión'),
        ('LOGOUT', 'Cierre de sesión'),
        ('REGISTRO', 'Registro de usuario'),
        ('2FA_CONFIGURADO', '2FA configurado'),
        ('2FA_VERIFICADO', '2FA verificado'),
        ('RECUPERACION_PASSWORD', 'Recuperación de contraseña'),
        ('CREAR', 'Creación'),
        ('EDITAR', 'Edición'),
        ('ELIMINAR', 'Eliminación'),
        ('PRESTAMO', 'Préstamo'),
        ('DEVOLUCION', 'Devolución'),
        ('SOLICITUD', 'Solicitud'),
        ('ADQUISICION', 'Adquisición de libro'),
        ('RECHAZO', 'Rechazo'),
    ]

    RESULTADO_CHOICES = [
        ('EXITO', 'Éxito'),
        ('ERROR', 'Error'),
        ('INFO', 'Información'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_actividad',
        db_column='UsuarioID',
    )

    accion = models.CharField(
        max_length=30,
        choices=ACCION_CHOICES,
        db_column='Accion',
    )

    modulo = models.CharField(
        max_length=50,
        db_column='Modulo',
    )

    descripcion = models.CharField(
        max_length=500,
        db_column='Descripcion',
    )

    fecha_hora = models.DateTimeField(
        auto_now_add=True,
        db_column='FechaHora',
    )

    ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        db_column='IP',
    )

    resultado = models.CharField(
        max_length=10,
        choices=RESULTADO_CHOICES,
        default='EXITO',
        db_column='Resultado',
    )

    class Meta:
        db_table = 'LOG_ACTIVIDAD'
        ordering = ['-fecha_hora', '-id']

    def __str__(self):
        """Devuelve una representación legible del registro de auditoría."""
        usuario = self.usuario.username if self.usuario else 'Sistema'
        return f"{self.fecha_hora:%d-%m-%Y %H:%M} - {usuario} - {self.accion}"
