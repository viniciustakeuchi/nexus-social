import re
from datetime import datetime, timedelta

from django import template
from django.urls import reverse
from django.utils import timezone
from django.utils.html import conditional_escape, format_html
from django.utils.http import urlencode
from django.utils.safestring import SafeString, mark_safe
from django.utils.timesince import timesince

from publicacoes.models import PADRAO_HASHTAG, PADRAO_MENCAO

register = template.Library()


@register.filter(needs_autoescape=True)
def enriquecer(texto: str, autoescape: bool = True) -> SafeString:
    """Escapa o texto e transforma #hashtags e @menções em links.

    O escape acontece antes da troca, então HTML digitado pelo usuário nunca é interpretado.
    """
    seguro = str(conditional_escape(texto)) if autoescape else texto

    def _hashtag(m: re.Match[str]) -> str:
        url = f"{reverse('explorar')}?{urlencode({'q': '#' + m.group(1)})}"
        return format_html('<a class="hashtag" href="{}">#{}</a>', url, m.group(1))

    def _mencao(m: re.Match[str]) -> str:
        username = m.group(1).rstrip(".")
        resto = m.group(1)[len(username) :]
        url = reverse("perfil", kwargs={"username": username})
        return format_html('<a class="mencao" href="{}">@{}</a>{}', url, username, resto)

    seguro = PADRAO_HASHTAG.sub(_hashtag, seguro)
    seguro = PADRAO_MENCAO.sub(_mencao, seguro)
    return mark_safe(seguro.replace("\n", "<br>"))  # noqa: S308


@register.filter
def tempo_relativo(momento: datetime) -> str:
    """ "agora" no primeiro minuto, depois "há 5 minutos", "há 2 dias"…"""
    if timezone.now() - momento < timedelta(minutes=1):
        return "agora"
    return f"há {timesince(momento, depth=1)}"
