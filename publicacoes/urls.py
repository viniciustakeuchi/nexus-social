from django.urls import path

from publicacoes import views

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("explorar/", views.explorar, name="explorar"),
    path("p/nova/", views.publicar, name="publicar"),
    path("p/<int:pk>/", views.detalhe, name="publicacao"),
    path("p/<int:pk>/curtir/", views.curtir, name="curtir"),
    path("p/<int:pk>/comentar/", views.comentar, name="comentar"),
    path("p/<int:pk>/excluir/", views.excluir, name="excluir_publicacao"),
    path("c/<int:pk>/excluir/", views.excluir_comentario, name="excluir_comentario"),
]
