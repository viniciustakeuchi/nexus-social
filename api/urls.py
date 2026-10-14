from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.routers import DefaultRouter

from api import views

roteador = DefaultRouter()
roteador.register("publicacoes", views.PublicacaoViewSet, basename="api-publicacao")

urlpatterns = [
    path("token/", obtain_auth_token, name="api-token"),
    path("feed/", views.FeedView.as_view(), name="api-feed"),
    path("usuarios/<str:username>/", views.PerfilView.as_view(), name="api-perfil"),
    path("usuarios/<str:username>/seguir/", views.SeguirView.as_view(), name="api-seguir"),
    path("schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("", include(roteador.urls)),
]
