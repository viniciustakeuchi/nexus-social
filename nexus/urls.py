from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from nexus.views import saude

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("saude/", saude, name="saude"),
    path("", include("contas.urls")),
    path("", include("publicacoes.urls")),
]

if settings.SERVIR_MIDIA:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
    ]

handler404 = "nexus.views.nao_encontrado"
