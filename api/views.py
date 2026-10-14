from typing import Any, cast

from django.db.models import Count, QuerySet
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import generics, mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissoes import AutorOuSomenteLeitura
from api.serializers import ComentarioSerializer, PerfilSerializer, PublicacaoSerializer
from contas.models import Usuario
from publicacoes.consultas import buscar, feed, publicacoes_anotadas
from publicacoes.models import Curtida, Publicacao

RespostaCurtida = inline_serializer(
    "RespostaCurtida", {"curtida": serializers.BooleanField(), "total": serializers.IntegerField()}
)
RespostaSeguir = inline_serializer(
    "RespostaSeguir",
    {"seguindo": serializers.BooleanField(), "seguidores": serializers.IntegerField()},
)


@extend_schema(
    parameters=[
        OpenApiParameter("q", str, description="Busca no texto; use #tag para hashtags."),
        OpenApiParameter("autor", str, description="Filtra pelo username do autor."),
    ]
)
class PublicacaoViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Publicações de todo mundo. Criar e excluir exigem autenticação."""

    serializer_class = PublicacaoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, AutorOuSomenteLeitura]

    def get_queryset(self) -> QuerySet[Publicacao]:
        termo = self.request.query_params.get("q", "").strip()
        consulta = (
            buscar(self.request.user, termo) if termo else publicacoes_anotadas(self.request.user)
        )
        autor = self.request.query_params.get("autor")
        if autor:
            consulta = consulta.filter(autor__username=autor)
        return consulta

    def perform_create(self, serializer: Any) -> None:
        serializer.save(autor=self.request.user)

    def perform_destroy(self, instance: Publicacao) -> None:
        instance.imagem.delete(save=False)
        instance.delete()

    @extend_schema(request=None, responses=RespostaCurtida)
    @action(
        detail=True,
        methods=["post", "delete"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def curtida(self, request: Request, pk: str | None = None) -> Response:
        """POST curte, DELETE descurte. As duas operações são idempotentes."""
        publicacao = get_object_or_404(Publicacao, pk=pk)
        usuario = cast(Usuario, request.user)
        codigo: int
        if request.method == "POST":
            Curtida.objects.get_or_create(usuario=usuario, publicacao=publicacao)
            codigo = status.HTTP_201_CREATED
        else:
            Curtida.objects.filter(usuario=usuario, publicacao=publicacao).delete()
            codigo = status.HTTP_200_OK
        return Response(
            {"curtida": request.method == "POST", "total": publicacao.curtidas.count()},
            status=codigo,
        )

    @extend_schema(methods=["get"], responses=ComentarioSerializer(many=True))
    @extend_schema(methods=["post"], request=ComentarioSerializer, responses=ComentarioSerializer)
    @action(detail=True, methods=["get", "post"])
    def comentarios(self, request: Request, pk: str | None = None) -> Response:
        publicacao = get_object_or_404(Publicacao, pk=pk)
        if request.method == "POST":
            serializer = ComentarioSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(autor=request.user, publicacao=publicacao)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        comentarios = publicacao.comentarios.select_related("autor")
        pagina = self.paginate_queryset(comentarios)
        dados = ComentarioSerializer(pagina, many=True, context={"request": request}).data
        return self.get_paginated_response(dados)


class FeedView(generics.ListAPIView):
    """Feed do usuário autenticado: as próprias publicações e as de quem ele segue."""

    serializer_class = PublicacaoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Publicacao]:
        return feed(self.request.user)  # type: ignore[arg-type]


class PerfilView(generics.RetrieveAPIView):
    """Perfil público com contadores de seguidores, seguindo e publicações."""

    serializer_class = PerfilSerializer
    lookup_field = "username"

    def get_queryset(self) -> QuerySet[Usuario]:
        return Usuario.objects.filter(is_active=True).annotate(
            total_seguidores=Count("seguidores", distinct=True),
            total_seguindo=Count("seguindo", distinct=True),
            total_publicacoes=Count("publicacoes", distinct=True),
        )


class SeguirView(APIView):
    """POST segue o usuário, DELETE deixa de seguir. Idempotente."""

    permission_classes = [permissions.IsAuthenticated]

    def _alvo(self, request: Request, username: str) -> Usuario:
        alvo = get_object_or_404(Usuario, username=username, is_active=True)
        if alvo.pk == request.user.pk:
            raise serializers.ValidationError({"detail": "Você não pode seguir a si mesmo."})
        return alvo

    @extend_schema(request=None, responses=RespostaSeguir)
    def post(self, request: Request, username: str) -> Response:
        alvo = self._alvo(request, username)
        alvo.seguidores.add(request.user)  # type: ignore[arg-type]
        return Response(
            {"seguindo": True, "seguidores": alvo.seguidores.count()},
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(request=None, responses=RespostaSeguir)
    def delete(self, request: Request, username: str) -> Response:
        alvo = self._alvo(request, username)
        alvo.seguidores.remove(request.user)  # type: ignore[arg-type]
        return Response({"seguindo": False, "seguidores": alvo.seguidores.count()})
