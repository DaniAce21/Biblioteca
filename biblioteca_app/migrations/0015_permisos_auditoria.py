from django.db import migrations, models


def crear_permisos_auditoria(apps, schema_editor):
    """Crea el catálogo inicial de permisos de auditoría."""
    PermisoAuditoria = apps.get_model('biblioteca_app', 'PermisoAuditoria')

    permisos = [
        (
            'AUDITORIA_VER',
            'Ver auditoría',
            'Permite consultar el listado de eventos de auditoría y utilizar filtros.',
        ),
        (
            'AUDITORIA_DETALLE',
            'Ver detalle de auditoría',
            'Permite consultar el detalle completo de un evento de auditoría.',
        ),
        (
            'AUDITORIA_EXPORTAR',
            'Exportar auditoría',
            'Permite exportar registros de auditoría.',
        ),
    ]

    for codigo, nombre, descripcion in permisos:
        PermisoAuditoria.objects.get_or_create(
            codigo=codigo,
            defaults={
                'nombre': nombre,
                'descripcion': descripcion,
                'activo': True,
            },
        )


def eliminar_permisos_auditoria(apps, schema_editor):
    """Elimina únicamente el catálogo creado por esta migración."""
    PermisoAuditoria = apps.get_model('biblioteca_app', 'PermisoAuditoria')
    PermisoAuditoria.objects.filter(
        codigo__in=[
            'AUDITORIA_VER',
            'AUDITORIA_DETALLE',
            'AUDITORIA_EXPORTAR',
        ]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('biblioteca_app', '0014_ampliar_auditoria'),
    ]

    operations = [
        migrations.CreateModel(
            name='PermisoAuditoria',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'codigo',
                    models.CharField(
                        db_column='Codigo',
                        max_length=50,
                        unique=True,
                    ),
                ),
                (
                    'nombre',
                    models.CharField(
                        db_column='Nombre',
                        max_length=100,
                    ),
                ),
                (
                    'descripcion',
                    models.TextField(
                        blank=True,
                        db_column='Descripcion',
                    ),
                ),
                (
                    'activo',
                    models.BooleanField(
                        db_column='Activo',
                        default=True,
                    ),
                ),
                (
                    'fecha_creacion',
                    models.DateTimeField(
                        auto_now_add=True,
                        db_column='FechaCreacion',
                    ),
                ),
            ],
            options={
                'db_table': 'PERMISO_AUDITORIA',
                'ordering': ['codigo'],
            },
        ),
        migrations.CreateModel(
            name='UsuarioPermisoAuditoria',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                (
                    'fecha_asignacion',
                    models.DateTimeField(
                        auto_now_add=True,
                        db_column='FechaAsignacion',
                    ),
                ),
                (
                    'activo',
                    models.BooleanField(
                        db_column='Activo',
                        default=True,
                    ),
                ),
                (
                    'asignado_por',
                    models.ForeignKey(
                        blank=True,
                        db_column='AsignadoPorId',
                        null=True,
                        on_delete=models.SET_NULL,
                        related_name='permisos_auditoria_asignados',
                        to='auth.user',
                    ),
                ),
                (
                    'perfil',
                    models.ForeignKey(
                        db_column='PerfilId',
                        on_delete=models.CASCADE,
                        related_name='permisos_auditoria',
                        to='biblioteca_app.perfilusuario',
                    ),
                ),
                (
                    'permiso',
                    models.ForeignKey(
                        db_column='PermisoId',
                        on_delete=models.CASCADE,
                        related_name='asignaciones',
                        to='biblioteca_app.permisoauditoria',
                    ),
                ),
            ],
            options={
                'db_table': 'USUARIO_PERMISO_AUDITORIA',
                'ordering': ['-fecha_asignacion'],
            },
        ),
        migrations.AddConstraint(
            model_name='usuariopermisoauditoria',
            constraint=models.UniqueConstraint(
                fields=('perfil', 'permiso'),
                name='perfil_permiso_auditoria_unico',
            ),
        ),
        migrations.RunPython(
            crear_permisos_auditoria,
            eliminar_permisos_auditoria,
        ),
    ]
