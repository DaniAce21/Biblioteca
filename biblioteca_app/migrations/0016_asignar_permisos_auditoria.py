from django.db import migrations


def asignar_permisos_auditoria(apps, schema_editor):
    PerfilUsuario = apps.get_model("biblioteca_app", "PerfilUsuario")
    PermisoAuditoria = apps.get_model("biblioteca_app", "PermisoAuditoria")
    UsuarioPermisoAuditoria = apps.get_model("biblioteca_app", "UsuarioPermisoAuditoria")
    permisos = list(PermisoAuditoria.objects.filter(activo=True))
    for perfil in PerfilUsuario.objects.filter(tipo_usuario="ADMIN"):
        for permiso in permisos:
            UsuarioPermisoAuditoria.objects.get_or_create(
                perfil=perfil,
                permiso=permiso,
                defaults={"activo": True},
            )


def revertir(apps, schema_editor):
    # No se eliminan asignaciones existentes para no afectar configuraciones manuales.
    pass


class Migration(migrations.Migration):
    dependencies = [("biblioteca_app", "0015_permisos_auditoria")]
    operations = [migrations.RunPython(asignar_permisos_auditoria, revertir)]
