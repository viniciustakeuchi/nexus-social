from io import StringIO

from django.core.management import call_command

from contas.models import Usuario
from publicacoes.models import Publicacao


def test_popular_demo_e_idempotente(db):
    saida = StringIO()
    call_command("popular_demo", stdout=saida)
    assert "Pronto" in saida.getvalue()
    assert Usuario.objects.count() == 6
    total = Publicacao.objects.count()
    assert total == 12
    assert Usuario.objects.get(username="ana.dev").check_password("nexus12345")

    call_command("popular_demo", stdout=saida)
    assert Publicacao.objects.count() == total
    assert "já existem" in saida.getvalue()
