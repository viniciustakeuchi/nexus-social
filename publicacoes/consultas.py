"""Consultas do feed, montadas para não cair em N+1.

Cada publicação já vem com autor (JOIN), total de curtidas e comentários (subconsultas
correlacionadas) e se o usuário atual curtiu (EXISTS). Uma página do feed custa uma única
consulta, independente de quantas publicações ela tenha.
"""

from django.contrib.auth.models import AbstractBaseUser, AnonymousUser
from django.db.models import Count, Exists, IntegerField, OuterRef, Q, QuerySet, Subquery, Value
from django.db.models.functions import Coalesce

from contas.models import Seguimento
from publicacoes.models import Comentario, Curtida, Publicacao


def _contagem(modelo: type[Curtida] | type[Comentario]) -> Coalesce:
    sub = (
        modelo.objects.filter(publicacao=OuterRef("pk"))
        .order_by()
        .values("publicacao")
        .annotate(total=Count("pk"))
        .values("total")
    )
    return Coalesce(Subquery(sub, output_field=IntegerField()), Value(0))


def publicacoes_anotadas(usuario: AbstractBaseUser | AnonymousUser) -> QuerySet[Publicacao]:
    consulta = Publicacao.objects.select_related("autor").annotate(
        total_curtidas=_contagem(Curtida),
        total_comentarios=_contagem(Comentario),
    )
    if usuario.is_authenticated:
        return consulta.annotate(
            curtida_por_mim=Exists(
                Curtida.objects.filter(publicacao=OuterRef("pk"), usuario_id=usuario.pk)
            )
        )
    return consulta.annotate(curtida_por_mim=Value(False))


def feed(usuario: AbstractBaseUser) -> QuerySet[Publicacao]:
    """Publicações do próprio usuário e de quem ele segue, mais recentes primeiro."""
    seguidos = Seguimento.objects.filter(seguidor_id=usuario.pk).values("seguido_id")
    return publicacoes_anotadas(usuario).filter(Q(autor_id=usuario.pk) | Q(autor_id__in=seguidos))


def buscar(usuario: AbstractBaseUser | AnonymousUser, termo: str) -> QuerySet[Publicacao]:
    termo = termo.strip()
    consulta = publicacoes_anotadas(usuario)
    if termo.startswith("#"):
        tag = termo[1:]
        # Casa a hashtag inteira: "#py" não deve trazer "#python".
        return consulta.filter(texto__iregex=rf"#{_escapar_regex(tag)}(\W|$)")
    return consulta.filter(texto__icontains=termo)


def _escapar_regex(texto: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else f"\\{c}" for c in texto)
