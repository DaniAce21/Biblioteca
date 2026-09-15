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
# PERMISOS DE AUDITORÍA
# ============================================================

class PermisoAuditoria(models.Model):
    """Catálogo de permisos independientes para la auditoría."""

    codigo = models.CharField(
        max_length=50,
        unique=True,
        db_column='Codigo'
    )

    nombre = models.CharField(
        max_length=100,
        db_column='Nombre'
    )

    descripcion = models.TextField(
        blank=True,
        db_column='Descripcion'
    )

    activo = models.BooleanField(
        default=True,
        db_column='Activo'
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        db_column='FechaCreacion'
    )

    class Meta:
        db_table = 'PERMISO_AUDITORIA'
        ordering = ['codigo']

    def __str__(self):
        return self.nombre


class UsuarioPermisoAuditoria(models.Model):
    """Asigna un permiso de auditoría a un perfil de usuario."""

    perfil = models.ForeignKey(
        'PerfilUsuario',
        on_delete=models.CASCADE,
        related_name='permisos_auditoria',
        db_column='PerfilId'
    )

    permiso = models.ForeignKey(
        PermisoAuditoria,
        on_delete=models.CASCADE,
        related_name='asignaciones',
        db_column='PermisoId'
    )

    fecha_asignacion = models.DateTimeField(
        auto_now_add=True,
        db_column='FechaAsignacion'
    )

    asignado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permisos_auditoria_asignados',
        db_column='AsignadoPorId'
    )

    activo = models.BooleanField(
        default=True,
        db_column='Activo'
    )

    class Meta:
        db_table = 'USUARIO_PERMISO_AUDITORIA'
        ordering = ['-fecha_asignacion']
        constraints = [
            models.UniqueConstraint(
                fields=['perfil', 'permiso'],
                name='perfil_permiso_auditoria_unico'
            )
        ]

    def __str__(self):
        return f'{self.perfil.usuario.username} - {self.permiso.codigo}'

# ============================================================
# LOG DE ACTIVIDAD / AUDITORÍA
# ============================================================

class LogActividad(models.Model):

    """Registra las acciones importantes y eventos de seguridad del sistema."""

    TIPO_CAMBIO = 'CAMBIO_DATOS'
    TIPO_SEGURIDAD = 'SEGURIDAD'

    TIPO_CHOICES = [
        (TIPO_CAMBIO, 'Cambio de datos'),
        (TIPO_SEGURIDAD, 'Seguridad'),
    ]

    NIVEL_INFO = 'INFO'
    NIVEL_ADVERTENCIA = 'ADVERTENCIA'
    NIVEL_CRITICO = 'CRITICO'

    NIVEL_CHOICES = [
        (NIVEL_INFO, 'Información'),
        (NIVEL_ADVERTENCIA, 'Advertencia'),
        (NIVEL_CRITICO, 'Crítico'),
    ]

    ACCION_CHOICES = [
        ('LOGIN', 'Inicio de sesión'),
        ('LOGIN_FALLIDO', 'Inicio de sesión fallido'),
        ('LOGOUT', 'Cierre de sesión'),
        ('ACCESO_NO_AUTORIZADO', 'Acceso no autorizado'),
        ('REGISTRO', 'Registro de usuario'),
        ('2FA_CONFIGURADO', '2FA configurado'),
        ('2FA_VERIFICADO', '2FA verificado'),
        ('RECUPERACION_PASSWORD', 'Recuperación de contraseña'),
        ('CAMBIAR_CONTRASENA', 'Cambio de contraseña'),
        ('CAMBIAR_PERMISOS', 'Cambio de permisos'),
        ('CAMBIAR_ROL', 'Cambio de rol'),
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
        ('BLOQUEADO', 'Bloqueado'),
    ]

    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_actividad',
        db_column='UsuarioID',
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default=TIPO_CAMBIO,
        db_column='Tipo',
    )

    accion = models.CharField(
        max_length=30,
        choices=ACCION_CHOICES,
        db_column='Accion',
    )

    nivel = models.CharField(
        max_length=15,
        choices=NIVEL_CHOICES,
        default=NIVEL_INFO,
        db_column='Nivel',
    )

    modulo = models.CharField(
        max_length=50,
        db_column='Modulo',
    )

    entidad = models.CharField(
        max_length=80,
        null=True,
        blank=True,
        db_column='Entidad',
    )

    objeto_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_column='ObjetoID',
    )

    descripcion = models.CharField(
        max_length=500,
        db_column='Descripcion',
    )

    datos_anteriores = models.JSONField(
        null=True,
        blank=True,
        db_column='DatosAnteriores',
    )

    datos_nuevos = models.JSONField(
        null=True,
        blank=True,
        db_column='DatosNuevos',
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

    user_agent = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        db_column='UserAgent',
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
        indexes = [
            models.Index(fields=['tipo', '-fecha_hora'], name='log_tipo_fecha_idx'),
            models.Index(fields=['nivel', '-fecha_hora'], name='log_nivel_fecha_idx'),
            models.Index(fields=['accion', '-fecha_hora'], name='log_accion_fecha_idx'),
        ]

    def __str__(self):
        """Devuelve una representación legible del registro de auditoría."""
        usuario = self.usuario.username if self.usuario else 'Sistema'
        return f"{self.fecha_hora:%d-%m-%Y %H:%M} - {usuario} - {self.accion}"
