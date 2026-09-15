from django.db import migrations


def agregar_permiso_gestionar(apps, schema_editor):
    PermisoAuditoria = apps.get_model("biblioteca_app", "PermisoAuditoria")
    PerfilUsuario = apps.get_model("biblioteca_app", "PerfilUsuario")
    UsuarioPermisoAuditoria = apps.get_model("biblioteca_app", "UsuarioPermisoAuditoria")

    permiso, _ = PermisoAuditoria.objects.get_or_create(
        codigo="AUDITORIA_GESTIONAR",
        defaults={
            "nombre": "Gestionar permisos de auditoría",
            "descripcion": "Permite asignar o quitar permisos de auditoría a otros administradores.",
            "activo": True,
        },
    )

    for perfil in PerfilUsuario.objects.filter(tipo_usuario="ADMIN"):
        UsuarioPermisoAuditoria.objects.get_or_create(
            perfil=perfil,
            permiso=permiso,
            defaults={"activo": True},
        )


def revertir(apps, schema_editor):
    PermisoAuditoria = apps.get_model("biblioteca_app", "PermisoAuditoria")
    UsuarioPermisoAuditoria = apps.get_model("biblioteca_app", "UsuarioPermisoAuditoria")
    permiso = PermisoAuditoria.objects.filter(codigo="AUDITORIA_GESTIONAR").first()
    if permiso:
        UsuarioPermisoAuditoria.objects.filter(permiso=permiso).delete()
        permiso.delete()


class Migration(migrations.Migration):
    dependencies = [("biblioteca_app", "0016_asignar_permisos_auditoria")]
    operations = [migrations.RunPython(agregar_permiso_gestionar, revertir)]
