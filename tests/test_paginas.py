import pytest
from django.urls import reverse

from contas.models import Usuario
from publicacoes.models import Comentario, Curtida, Publicacao
from tests.conftest import SENHA, gerar_imagem


def test_boas_vindas_para_anonimo(client, ana, publicar):
    publicar(ana, "Destaque do dia")
    resposta = client.get("/")
    assert resposta.status_code == 200
    assert b"conex" in resposta.content
    assert b"Destaque do dia" in resposta.content
    assert resposta.context["total_usuarios"] == 1


def test_feed_logado(cliente_ana, ana, bruno, publicar):
    publicar(bruno, "post do bruno")
    publicar(ana, "post da ana")
    resposta = cliente_ana.get("/")
    assert b"post da ana" in resposta.content
    assert b"post do bruno" not in resposta.content
    assert b"Quem seguir" in resposta.content  # bruno aparece como sugestão


def test_cadastro_cria_conta_e_faz_login(client, db):
    dados = {
        "username": "novo",
        "nome_exibicao": "Novo Usuário",
        "email": "Novo@Exemplo.com",
        "password1": "uma-senha-bem-forte-9",
        "password2": "uma-senha-bem-forte-9",
    }
    resposta = client.post(reverse("cadastro"), dados)
    assert resposta.status_code == 302
    usuario = Usuario.objects.get(username="novo")
    assert usuario.email == "novo@exemplo.com"
    assert client.get("/").context["user"] == usuario


def test_cadastro_rejeita_email_repetido(client, ana):
    resposta = client.post(
        reverse("cadastro"),
        {
            "username": "outra",
            "email": "ANA@exemplo.com",
            "password1": "uma-senha-bem-forte-9",
            "password2": "uma-senha-bem-forte-9",
        },
    )
    assert resposta.status_code == 200
    assert "Já existe uma conta com este e-mail." in resposta.content.decode()


def test_cadastro_redireciona_logado(cliente_ana):
    assert cliente_ana.get(reverse("cadastro")).status_code == 302
    assert cliente_ana.get(reverse("cadastro")).url == "/"


def test_login_e_logout(client, ana):
    assert client.get(reverse("entrar")).status_code == 200
    resposta = client.post(reverse("entrar"), {"username": "ana", "password": SENHA})
    assert resposta.status_code == 302
    assert client.post(reverse("sair")).status_code == 302
    assert not client.get("/").context["user"].is_authenticated


def test_login_invalido_mostra_erro(client, ana):
    resposta = client.post(reverse("entrar"), {"username": "ana", "password": "errada"})
    assert "Usuário ou senha incorretos" in resposta.content.decode()


def test_publicar_texto_e_imagem(cliente_ana, ana):
    resposta = cliente_ana.post(
        reverse("publicar"),
        {"texto": "  Minha foto #roxo  ", "imagem": gerar_imagem(), "proximo": "/u/ana/"},
    )
    assert resposta.status_code == 302
    assert resposta.url == "/u/ana/"
    pub = Publicacao.objects.get()
    assert pub.texto == "Minha foto #roxo"
    assert pub.autor == ana
    assert pub.imagem.name.startswith(f"publicacoes/{ana.pk}/")


def test_publicar_vazio_nao_cria(cliente_ana):
    resposta = cliente_ana.post(reverse("publicar"), {"texto": "   "}, follow=True)
    assert Publicacao.objects.count() == 0
    assert "Escreva alguma coisa" in resposta.content.decode()


def test_publicar_rejeita_imagem_grande(cliente_ana, settings, monkeypatch):
    monkeypatch.setattr("publicacoes.forms.TAMANHO_MAXIMO_IMAGEM", 10)
    cliente_ana.post(reverse("publicar"), {"texto": "oi", "imagem": gerar_imagem()})
    assert Publicacao.objects.count() == 0


def test_publicar_ignora_redirecionamento_externo(cliente_ana):
    resposta = cliente_ana.post(
        reverse("publicar"), {"texto": "oi", "proximo": "https://malicioso.example/"}
    )
    assert resposta.url == "/"


def test_publicar_exige_login(client, db):
    resposta = client.post(reverse("publicar"), {"texto": "oi"})
    assert resposta.status_code == 302
    assert "/entrar/" in resposta.url
    assert Publicacao.objects.count() == 0


def test_publicar_so_aceita_post(cliente_ana):
    assert cliente_ana.get(reverse("publicar")).status_code == 405


def test_curtir_com_json_e_sem(cliente_ana, ana, bruno, publicar):
    pub = publicar(bruno)
    url = reverse("curtir", args=[pub.pk])
    resposta = cliente_ana.post(url, HTTP_ACCEPT="application/json")
    assert resposta.json() == {"curtida": True, "total": 1}
    resposta = cliente_ana.post(url)
    assert resposta.status_code == 302
    assert not Curtida.objects.exists()


def test_detalhe_e_comentarios(client, cliente_ana, ana, bruno, publicar):
    pub = publicar(bruno, "Comente aqui")
    resposta = cliente_ana.post(reverse("comentar", args=[pub.pk]), {"texto": "Comentei @bruno"})
    assert resposta.url.endswith("#comentarios")
    pagina = cliente_ana.get(pub.get_absolute_url()).content.decode()
    assert 'href="/u/bruno/">@bruno</a>' in pagina
    assert "Comentários (1)" in pagina

    client.logout()
    assert "para comentar" in client.get(pub.get_absolute_url()).content.decode()


def test_comentario_vazio(cliente_ana, ana, publicar):
    pub = publicar(ana)
    cliente_ana.post(reverse("comentar", args=[pub.pk]), {"texto": "  "})
    assert not Comentario.objects.exists()


def test_excluir_publicacao_so_do_autor(client, ana, bruno, publicar):
    pub_do_bruno = publicar(bruno)
    client.force_login(ana)
    assert client.post(reverse("excluir_publicacao", args=[pub_do_bruno.pk])).status_code == 403
    minha = publicar(ana)
    assert client.post(reverse("excluir_publicacao", args=[minha.pk])).status_code == 302
    assert list(Publicacao.objects.all()) == [pub_do_bruno]


@pytest.mark.parametrize(("quem", "codigo"), [("autor", 302), ("dono", 302), ("outro", 403)])
def test_excluir_comentario(client, ana, bruno, criar_usuario, publicar, quem, codigo):
    carla = criar_usuario("carla")
    pub = publicar(ana)
    comentario = Comentario.objects.create(autor=bruno, publicacao=pub, texto="oi")
    client.force_login({"autor": bruno, "dono": ana, "outro": carla}[quem])
    resposta = client.post(reverse("excluir_comentario", args=[comentario.pk]))
    assert resposta.status_code == codigo
    assert Comentario.objects.exists() is (codigo == 403)


def test_perfil(client, cliente_ana, ana, bruno, publicar):
    publicar(bruno, "post do bruno")
    ana.alternar_seguir(bruno)
    resposta = cliente_ana.get(reverse("perfil", args=["bruno"]))
    assert resposta.context["eu_sigo"] is True
    assert resposta.context["total_seguidores"] == 1
    assert resposta.context["form"] is None
    assert cliente_ana.get(reverse("perfil", args=["ana"])).context["form"] is not None
    assert client.get(reverse("perfil", args=["ninguem"])).status_code == 404


def test_perfil_inativo_nao_aparece(client, bruno):
    bruno.is_active = False
    bruno.save()
    assert client.get(reverse("perfil", args=["bruno"])).status_code == 404


def test_seguir_pela_pagina(cliente_ana, ana, bruno):
    url = reverse("seguir", args=["bruno"])
    resposta = cliente_ana.post(url, HTTP_ACCEPT="application/json")
    assert resposta.json() == {"seguindo": True, "seguidores": 1}
    resposta = cliente_ana.post(url, {"proximo": "/explorar/"})
    assert resposta.url == "/explorar/"
    assert not ana.segue(bruno)


def test_seguir_a_si_mesmo(cliente_ana):
    url = reverse("seguir", args=["ana"])
    assert cliente_ana.post(url, HTTP_ACCEPT="application/json").status_code == 400
    assert cliente_ana.post(url).status_code == 302


def test_listas_de_seguidores(client, cliente_ana, ana, bruno, criar_usuario):
    carla = criar_usuario("carla", nome_exibicao="Carla")
    bruno.alternar_seguir(ana)
    carla.alternar_seguir(ana)
    ana.alternar_seguir(carla)
    resposta = cliente_ana.get(reverse("seguidores", args=["ana"]))
    assert [p.username for p in resposta.context["pagina"]] == ["bruno", "carla"]
    assert resposta.context["ids_que_sigo"] == {carla.pk}
    resposta = client.get(reverse("seguindo", args=["ana"]))
    assert [p.username for p in resposta.context["pagina"]] == ["carla"]


def test_editar_perfil(cliente_ana, ana):
    assert cliente_ana.get(reverse("editar_perfil")).status_code == 200
    resposta = cliente_ana.post(
        reverse("editar_perfil"),
        {"nome_exibicao": "Ana R.", "bio": "Oi!", "avatar": gerar_imagem("eu.png")},
    )
    assert resposta.status_code == 302
    ana.refresh_from_db()
    assert ana.nome_exibicao == "Ana R."
    assert ana.avatar.name.startswith(f"avatares/{ana.pk}/")
    pagina = cliente_ana.get(reverse("perfil", args=["ana"])).content.decode()
    assert ana.avatar.url in pagina


def test_editar_perfil_avatar_grande(cliente_ana, monkeypatch):
    monkeypatch.setattr("contas.forms.TAMANHO_MAXIMO_AVATAR", 10)
    resposta = cliente_ana.post(
        reverse("editar_perfil"), {"nome_exibicao": "x", "avatar": gerar_imagem()}
    )
    assert "no máximo 2 MB" in resposta.content.decode()


def test_explorar(client, cliente_ana, ana, bruno, publicar):
    publicar(ana, "Primeiro #python")
    publicar(bruno, "Segundo #python #django")
    bruno.alternar_seguir(ana)
    resposta = client.get(reverse("explorar"))
    assert len(resposta.context["pagina"]) == 2
    assert resposta.context["hashtags_em_alta"] == [("python", 2), ("django", 1)]
    assert resposta.context["mais_seguidos"][0] == ana

    resposta = client.get(reverse("explorar"), {"q": "#django"})
    assert [p.autor for p in resposta.context["pagina"]] == [bruno]
    assert list(resposta.context["pessoas"]) == []

    resposta = cliente_ana.get(reverse("explorar"), {"q": "@bru"})
    assert list(resposta.context["pessoas"]) == [bruno]


def test_paginacao_mantem_busca(client, ana, publicar):
    for i in range(12):
        publicar(ana, f"post {i} #muitos")
    resposta = client.get(reverse("explorar"), {"q": "#muitos"})
    assert "q=%23muitos&pagina=2" in resposta.content.decode()


def test_404_personalizado(client, settings, db):
    settings.DEBUG = False
    resposta = client.get("/nao-existe/")
    assert resposta.status_code == 404
    assert "Essa conexão não existe" in resposta.content.decode()


def test_saude(client, db):
    assert client.get("/saude/").json() == {"status": "ok"}


def test_html_do_usuario_e_escapado(cliente_ana, ana, publicar):
    publicar(ana, "<script>alert(1)</script> #tag")
    pagina = cliente_ana.get("/").content.decode()
    assert "<script>alert(1)</script>" not in pagina
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in pagina
