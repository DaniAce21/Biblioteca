"""
URL configuration for biblioteca project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.shortcuts import render


def error_404(request, exception):
    """Gestiona la operación error 404 dentro de la aplicación."""
    return render(
        request,
        'biblioteca_app/errors/404.html',
        status=404
    )


# ============================================================
# FALLBACK 404 DURANTE EL DESARROLLO
# ============================================================
# Con DEBUG=True, Django puede mostrar su página técnica de 404.
# Esta vista de respaldo permite mantener nuestra plantilla
# personalizada también mientras desarrollamos localmente.
# ============================================================

def error_404_desarrollo(request):
    """Muestra la plantilla personalizada para URLs inexistentes."""
    return render(
        request,
        'biblioteca_app/errors/404.html',
        status=404,
    )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('biblioteca_app.urls')),

    # Última ruta: si ninguna URL anterior coincide, mostramos el 404 personalizado.
    re_path(r'^.*$', error_404_desarrollo),
]


handler404 = 'biblioteca.urls.error_404'