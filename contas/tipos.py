from django.http import HttpRequest

from contas.models import Usuario


class RequisicaoAutenticada(HttpRequest):
    """Tipo para views com @login_required: ali `request.user` é sempre um Usuario."""

    user: Usuario
