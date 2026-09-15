from django import template

from biblioteca_app.views import tiene_permiso_auditoria

register = template.Library()


@register.simple_tag(takes_context=True)
def puede_auditoria(context, codigo):
    """Permite consultar permisos de auditoría desde las plantillas."""
    return tiene_permiso_auditoria(context.get("user"), codigo)
