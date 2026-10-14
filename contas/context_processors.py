from typing import Any

from django.http import HttpRequest

from contas.models import Usuario


def sugestoes(request: HttpRequest) -> dict[str, Any]:
    """Sugere até 4 perfis que o usuário logado ainda não segue (barra lateral)."""
    usuario = request.user
    if not usuario.is_authenticated:
        return {}

    def _carregar() -> list[Usuario]:
        return list(
            Usuario.objects.filter(is_active=True)
            .exclude(pk=usuario.pk)
            .exclude(seguidores=usuario)
            .order_by("-date_joined")[:4]
        )

    # Avaliação preguiçosa: páginas que não mostram a barra lateral não pagam a consulta.
    return {"sugestoes_para_seguir": _carregar}
