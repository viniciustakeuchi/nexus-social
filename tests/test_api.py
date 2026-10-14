import pytest
from rest_framework.test import APIClient

from contas.models import Usuario
from publicacoes.models import Curtida, Publicacao
from tests.conftest import SENHA, gerar_imagem


def test_token(ana):
    cliente = APIClient()
    resposta = cliente.post("/api/token/", {"username": "ana", "password": SENHA})
    assert resposta.status_code == 200
    assert resposta.json()["token"]


def test_listar_publico_e_filtros(ana, bruno, publicar):
    publicar(ana, "da ana #python")
    publicar(bruno, "do bruno")
    cliente = APIClient()
    dados = cliente.get("/api/publicacoes/").json()
    assert dados["count"] == 2
    assert dados["results"][0]["autor"]["username"] == "bruno"
    assert cliente.get("/api/publicacoes/?autor=ana").json()["count"] == 1
    resultado = cliente.get("/api/publicacoes/?q=%23python").json()["results"]
    assert resultado[0]["hashtags"] == ["python"]


def test_criar_exige_autenticacao(db):
    assert APIClient().post("/api/publicacoes/", {"texto": "oi"}).status_code == 401


def test_criar_publicacao(api, ana):
    resposta = api.post("/api/publicacoes/", {"texto": " Pela API #rest "})
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["texto"] == "Pela API #rest"
    assert corpo["autor"]["username"] == "ana"
    assert Publicacao.objects.get().autor == ana


def test_criar_com_imagem(api):
    resposta = api.post(
        "/api/publicacoes/", {"texto": "foto", "imagem": gerar_imagem()}, format="multipart"
    )
    assert resposta.status_code == 201
    assert resposta.json()["imagem"].endswith(".png")


def test_criar_rejeita_imagem_grande(api, monkeypatch):
    from api import serializers

    monkeypatch.setattr(
        serializers.PublicacaoSerializer,
        "validate_imagem",
        lambda self, imagem: (_ for _ in ()).throw(
            serializers.serializers.ValidationError("A imagem pode ter no máximo 5 MB.")
        ),
    )
    resposta = api.post(
        "/api/publicacoes/", {"texto": "foto", "imagem": gerar_imagem()}, format="multipart"
    )
    assert resposta.status_code == 400


def test_validacao_tamanho_imagem_no_serializer():
    from api.serializers import PublicacaoSerializer

    class Falsa:
        size = 6 * 1024 * 1024

    with pytest.raises(Exception, match="5 MB"):
        PublicacaoSerializer().validate_imagem(Falsa())
    assert PublicacaoSerializer().validate_imagem(None) is None


def test_texto_longo_ou_vazio(api):
    assert api.post("/api/publicacoes/", {"texto": "x" * 501}).status_code == 400
    assert api.post("/api/publicacoes/", {"texto": "   "}).status_code == 400


def test_excluir_so_o_autor(api, ana, bruno, publicar):
    do_bruno = publicar(bruno)
    minha = publicar(ana)
    assert api.delete(f"/api/publicacoes/{do_bruno.pk}/").status_code == 403
    assert api.delete(f"/api/publicacoes/{minha.pk}/").status_code == 204
    assert list(Publicacao.objects.all()) == [do_bruno]


def test_curtida_idempotente(api, ana, bruno, publicar):
    pub = publicar(bruno)
    url = f"/api/publicacoes/{pub.pk}/curtida/"
    assert api.post(url).json() == {"curtida": True, "total": 1}
    assert api.post(url).status_code == 201
    assert Curtida.objects.count() == 1
    detalhe = api.get(f"/api/publicacoes/{pub.pk}/").json()
    assert detalhe["curtida_por_mim"] is True
    assert detalhe["total_curtidas"] == 1
    assert api.delete(url).json() == {"curtida": False, "total": 0}
    assert api.delete(url).status_code == 200


def test_curtida_anonima(ana, publicar):
    pub = publicar(ana)
    assert APIClient().post(f"/api/publicacoes/{pub.pk}/curtida/").status_code == 401


def test_comentarios(api, bruno, publicar):
    pub = publicar(bruno)
    url = f"/api/publicacoes/{pub.pk}/comentarios/"
    resposta = api.post(url, {"texto": "Muito bom"})
    assert resposta.status_code == 201
    assert resposta.json()["autor"]["username"] == "ana"
    assert api.post(url, {"texto": ""}).status_code == 400
    lista = APIClient().get(url).json()
    assert lista["count"] == 1
    assert lista["results"][0]["texto"] == "Muito bom"


def test_feed(api, ana, bruno, criar_usuario, publicar):
    carla = criar_usuario("carla")
    publicar(bruno, "bruno")
    publicar(carla, "carla")
    publicar(ana, "ana")
    ana.alternar_seguir(bruno)
    textos = [p["texto"] for p in api.get("/api/feed/").json()["results"]]
    assert textos == ["ana", "bruno"]
    assert APIClient().get("/api/feed/").status_code == 401


def test_perfil(api, ana, bruno, publicar):
    publicar(bruno)
    publicar(bruno)
    ana.alternar_seguir(bruno)
    dados = api.get("/api/usuarios/bruno/").json()
    assert dados["seguidores"] == 1
    assert dados["seguindo"] == 0
    assert dados["publicacoes"] == 2
    assert dados["eu_sigo"] is True
    assert APIClient().get("/api/usuarios/bruno/").json()["eu_sigo"] is False
    assert api.get("/api/usuarios/ninguem/").status_code == 404


def test_seguir(api, ana, bruno):
    url = "/api/usuarios/bruno/seguir/"
    assert api.post(url).json() == {"seguindo": True, "seguidores": 1}
    assert api.post(url).status_code == 201
    assert ana.segue(bruno)
    assert api.delete(url).json() == {"seguindo": False, "seguidores": 0}
    assert api.delete(url).status_code == 200
    assert api.post("/api/usuarios/ana/seguir/").status_code == 400


def test_schema_openapi(client, db):
    resposta = client.get("/api/schema/")
    assert resposta.status_code == 200
    assert b"Nexus Social API" in resposta.content
    assert client.get("/api/docs/").status_code == 200


def test_usuario_inativo_nao_aparece(api, bruno):
    Usuario.objects.filter(pk=bruno.pk).update(is_active=False)
    assert api.get("/api/usuarios/bruno/").status_code == 404
    assert api.post("/api/usuarios/bruno/seguir/").status_code == 404
