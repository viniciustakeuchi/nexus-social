from django.contrib.auth import views as auth_views
from django.urls import path

from contas import views

urlpatterns = [
    path("cadastro/", views.cadastro, name="cadastro"),
    path(
        "entrar/",
        auth_views.LoginView.as_view(redirect_authenticated_user=True),
        name="entrar",
    ),
    path("sair/", auth_views.LogoutView.as_view(), name="sair"),
    path("conta/editar/", views.editar_perfil, name="editar_perfil"),
    path("u/<str:username>/", views.perfil, name="perfil"),
    path("u/<str:username>/seguir/", views.seguir, name="seguir"),
    path("u/<str:username>/seguidores/", views.seguidores, name="seguidores"),
    path("u/<str:username>/seguindo/", views.seguindo, name="seguindo"),
]
