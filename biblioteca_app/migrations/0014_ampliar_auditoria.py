# Migración para ampliar el sistema de auditoría y separar
# eventos de seguridad de cambios de datos.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('biblioteca_app', '0013_alter_logactividad_accion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='logactividad',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('CAMBIO_DATOS', 'Cambio de datos'),
                    ('SEGURIDAD', 'Seguridad'),
                ],
                db_column='Tipo',
                default='CAMBIO_DATOS',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='logactividad',
            name='nivel',
            field=models.CharField(
                choices=[
                    ('INFO', 'Información'),
                    ('ADVERTENCIA', 'Advertencia'),
                    ('CRITICO', 'Crítico'),
                ],
                db_column='Nivel',
                default='INFO',
                max_length=15,
            ),
        ),
        migrations.AddField(
            model_name='logactividad',
            name='entidad',
            field=models.CharField(
                blank=True,
                db_column='Entidad',
                max_length=80,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='logactividad',
            name='objeto_id',
            field=models.CharField(
                blank=True,
                db_column='ObjetoID',
                max_length=50,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='logactividad',
            name='datos_anteriores',
            field=models.JSONField(
                blank=True,
                db_column='DatosAnteriores',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='logactividad',
            name='datos_nuevos',
            field=models.JSONField(
                blank=True,
                db_column='DatosNuevos',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='logactividad',
            name='user_agent',
            field=models.CharField(
                blank=True,
                db_column='UserAgent',
                max_length=500,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='logactividad',
            name='accion',
            field=models.CharField(
                choices=[
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
                ],
                db_column='Accion',
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name='logactividad',
            name='resultado',
            field=models.CharField(
                choices=[
                    ('EXITO', 'Éxito'),
                    ('ERROR', 'Error'),
                    ('INFO', 'Información'),
                    ('BLOQUEADO', 'Bloqueado'),
                ],
                db_column='Resultado',
                default='EXITO',
                max_length=10,
            ),
        ),
        migrations.AddIndex(
            model_name='logactividad',
            index=models.Index(fields=['tipo', '-fecha_hora'], name='log_tipo_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='logactividad',
            index=models.Index(fields=['nivel', '-fecha_hora'], name='log_nivel_fecha_idx'),
        ),
        migrations.AddIndex(
            model_name='logactividad',
            index=models.Index(fields=['accion', '-fecha_hora'], name='log_accion_fecha_idx'),
        ),
    ]
