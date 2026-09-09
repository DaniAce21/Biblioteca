# Migración del historial persistente de auditoría del sistema.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('biblioteca_app', '0011_solicitudlibro_adquisicion'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LogActividad',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('accion', models.CharField(db_column='Accion', max_length=30)),
                ('modulo', models.CharField(db_column='Modulo', max_length=50)),
                ('descripcion', models.CharField(db_column='Descripcion', max_length=500)),
                ('fecha_hora', models.DateTimeField(auto_now_add=True, db_column='FechaHora')),
                ('ip', models.GenericIPAddressField(blank=True, db_column='IP', null=True)),
                ('resultado', models.CharField(db_column='Resultado', default='EXITO', max_length=10)),
                ('usuario', models.ForeignKey(blank=True, db_column='UsuarioID', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='logs_actividad', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'LOG_ACTIVIDAD',
                'ordering': ['-fecha_hora', '-id'],
            },
        ),
    ]
