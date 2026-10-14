from datetime import timedelta

from django.utils import timezone

from publicacoes.templatetags.nexus import enriquecer, tempo_relativo


def test_enriquecer_links():
    html = enriquecer("Oi @ana. veja #Django\nfim")
    assert '<a class="mencao" href="/u/ana/">@ana</a>.' in html
    assert '<a class="hashtag" href="/explorar/?q=%23Django">#Django</a>' in html
    assert "<br>fim" in html


def test_enriquecer_escapa_html():
    html = enriquecer('<img src=x onerror="alert(1)"> #ok')
    assert "<img" not in html
    assert "&lt;img" in html
    assert "#x27" not in html.replace("&#x27;", "")


def test_enriquecer_ignora_email_e_entidades():
    html = enriquecer("fale com ana@exemplo.com ou 'aspas'")
    assert "mencao" not in html
    assert "hashtag" not in html


def test_enriquecer_sem_autoescape():
    assert enriquecer("#a", autoescape=False).startswith('<a class="hashtag"')


def test_tempo_relativo():
    agora = timezone.now()
    assert tempo_relativo(agora) == "agora"
    assert tempo_relativo(agora - timedelta(hours=3)).startswith("há 3")
