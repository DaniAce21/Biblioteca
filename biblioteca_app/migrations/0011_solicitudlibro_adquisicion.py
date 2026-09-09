"""
Migración para incorporar el flujo de adquisición de libros solicitados.

Las solicitudes existentes que ya estaban aprobadas se convierten a
ADQUIRIDA cuando el libro correspondiente ya existe en el catálogo.
"""

from django.db import migrations, models
from django.utils import timezone


def migrar_solicitudes_aprobadas(apps, schema_editor):
    """Conserva las solicitudes antiguas sin perder su relación con el libro."""

    SolicitudLibro = apps.get_model('biblioteca_app', 'SolicitudLibro')
    Libro = apps.get_model('biblioteca_app', 'Libro')

    for solicitud in SolicitudLibro.objects.filter(Estado='APROBADA'):
        libro = Libro.objects.filter(
            Titulo__iexact=solicitud.Titulo.strip()
        ).first()

        if libro is not None:
            solicitud.CodLibro_id = libro.pk
            solicitud.Estado = 'ADQUIRIDA'
            solicitud.FechaAdquisicion = (
                solicitud.FechaRespuesta or timezone.now()
            )
        else:
            # Caso excepcional: la solicitud estaba aprobada pero el
            # libro ya no aparece en el catálogo. La dejamos en proceso
            # para que el administrador pueda revisar su adquisición.
            solicitud.Estado = 'EN_ADQUISICION'

        solicitud.save(
            update_fields=[
                'CodLibro',
                'Estado',
                'FechaAdquisicion'
            ]
        )


def revertir_solicitudes_aprobadas(apps, schema_editor):
    """Restaura el estado histórico APROBADA al revertir la migración."""

    SolicitudLibro = apps.get_model('biblioteca_app', 'SolicitudLibro')

    SolicitudLibro.objects.filter(
        Estado__in=['ADQUIRIDA', 'EN_ADQUISICION']
    ).update(Estado='APROBADA')



class Migration(migrations.Migration):

    dependencies = [
        ('biblioteca_app', '0010_perfilusuario_2fa'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitudlibro',
            name='CodLibro',
            field=models.ForeignKey(
                blank=True,
                db_column='CodLibro',
                null=True,
                on_delete=models.deletion.PROTECT,
                related_name='solicitudes_incorporacion',
                to='biblioteca_app.libro',
            ),
        ),
        migrations.AddField(
            model_name='solicitudlibro',
            name='FechaAdquisicion',
            field=models.DateTimeField(
                blank=True,
                db_column='FechaAdquisicion',
                null=True,
            ),
        ),
        migrations.RunPython(
            migrar_solicitudes_aprobadas,
            revertir_solicitudes_aprobadas,
        ),
        migrations.AlterField(
            model_name='solicitudlibro',
            name='Estado',
            field=models.CharField(
                choices=[
                    ('PENDIENTE', 'Pendiente'),
                    ('EN_ADQUISICION', 'En adquisición'),
                    ('ADQUIRIDA', 'Adquirida'),
                    ('RECHAZADA', 'Rechazada'),
                ],
                db_column='Estado',
                default='PENDIENTE',
                max_length=20,
            ),
        ),
    ]
