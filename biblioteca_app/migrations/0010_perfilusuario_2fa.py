"""
Migración para incorporar autenticación de dos factores al perfil de usuario.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('biblioteca_app', '0009_lector_telefono_direccion'),
    ]

    operations = [
        migrations.AddField(
            model_name='perfilusuario',
            name='two_factor_secret',
            field=models.CharField(
                blank=True,
                db_column='TwoFactorSecret',
                default='',
                max_length=64,
            ),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='two_factor_enabled',
            field=models.BooleanField(
                db_column='TwoFactorEnabled',
                default=False,
            ),
        ),
        migrations.AddField(
            model_name='perfilusuario',
            name='two_factor_verified_at',
            field=models.DateTimeField(
                blank=True,
                db_column='TwoFactorVerifiedAt',
                null=True,
            ),
        ),
    ]
