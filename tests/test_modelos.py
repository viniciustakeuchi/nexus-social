import pytest
from django.db import IntegrityError

from contas.models import Seguimento
from publicacoes.models import Curtida, Publicacao, extrair_hashtags


def test_nome_e_iniciais(ana, criar_usuario):
    assert ana.nome == "Ana Ribeiro"
    assert ana.iniciais == "AR"
    sem_nome = criar_usuario("zeca")
    assert sem_nome.nome == "zeca"
    assert sem_nome.iniciais == "Z"
    assert str(ana) == "@ana"
    assert ana.get_absolute_url() == "/u/ana/"


def test_alternar_seguir(ana, bruno):
    assert ana.alternar_seguir(bruno) is True
    assert ana.segue(bruno)
    assert list(bruno.seguidores.all()) == [ana]
    assert not bruno.segue(ana)
    assert ana.alternar_seguir(bruno) is False
    assert not ana.segue(bruno)


def test_nao_segue_a_si_mesmo(ana):
    with pytest.raises(ValueError):
        ana.alternar_seguir(ana)


def test_banco_impede_seguir_a_si_mesmo(ana):
    with pytest.raises(IntegrityError):
        Seguimento.objects.create(seguidor=ana, seguido=ana)


def test_banco_impede_seguimento_duplicado(ana, bruno):
    Seguimento.objects.create(seguidor=ana, seguido=bruno)
    with pytest.raises(IntegrityError):
        Seguimento.objects.create(seguidor=ana, seguido=bruno)


def test_curtida_alterna_e_e_unica(ana, publicar):
    pub = publicar(ana)
    assert Curtida.alternar(ana, pub) is True
    assert Curtida.alternar(ana, pub) is False
    assert Curtida.alternar(ana, pub) is True
    assert pub.curtidas.count() == 1
    with pytest.raises(IntegrityError):
        Curtida.objects.create(usuario=ana, publicacao=pub)


def test_str_e_hashtags_da_publicacao(ana, publicar):
    pub = publicar(ana, "Curtindo #Django e #python, de novo #django " + "x" * 40)
    assert pub.hashtags == ["django", "python"]
    assert str(pub).startswith("@ana: Curtindo") and str(pub).endswith("…")
    assert pub.get_absolute_url() == f"/p/{pub.pk}/"
    curta = publicar(ana, "oi")
    assert str(curta) == "@ana: oi"


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("sem tags", []),
        ("#um #dois #um", ["um", "dois"]),
        ("e-mail&#39;s não conta, mas #sim", ["sim"]),
        ("palavra#colada não conta", []),
        ("acentos: #ação #café", ["ação", "café"]),
    ],
)
def test_extrair_hashtags(texto, esperado):
    assert extrair_hashtags(texto) == esperado


def test_ordenacao_mais_recente_primeiro(ana, publicar):
    primeira = publicar(ana, "1")
    segunda = publicar(ana, "2")
    assert list(Publicacao.objects.all()) == [segunda, primeira]


def test_strs_auxiliares(ana, bruno, publicar):
    pub = publicar(ana)
    seg = Seguimento.objects.create(seguidor=ana, seguido=bruno)
    curtida = Curtida.objects.create(usuario=bruno, publicacao=pub)
    comentario = pub.comentarios.create(autor=bruno, texto="legal")
    assert str(seg) == "@ana segue @bruno"
    assert str(curtida) == f"@bruno curtiu #{pub.pk}"
    assert str(comentario) == f"@bruno em #{pub.pk}"
