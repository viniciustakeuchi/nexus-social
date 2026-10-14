from django.contrib.auth.models import AnonymousUser

from publicacoes.consultas import buscar, feed, publicacoes_anotadas
from publicacoes.models import Curtida


def test_feed_traz_proprias_e_de_quem_sigo(ana, bruno, criar_usuario, publicar):
    carla = criar_usuario("carla")
    minha = publicar(ana, "minha")
    do_bruno = publicar(bruno, "do bruno")
    publicar(carla, "da carla, que não sigo")
    ana.alternar_seguir(bruno)
    assert list(feed(ana)) == [do_bruno, minha]


def test_anotacoes(ana, bruno, publicar):
    pub = publicar(bruno)
    Curtida.objects.create(usuario=ana, publicacao=pub)
    Curtida.objects.create(usuario=bruno, publicacao=pub)
    pub.comentarios.create(autor=ana, texto="oi")

    vista_pela_ana = publicacoes_anotadas(ana).get()
    assert vista_pela_ana.total_curtidas == 2
    assert vista_pela_ana.total_comentarios == 1
    assert vista_pela_ana.curtida_por_mim is True

    anonimo = publicacoes_anotadas(AnonymousUser()).get()
    assert anonimo.curtida_por_mim is False


def test_feed_nao_tem_n_mais_1(ana, criar_usuario, publicar, django_assert_num_queries):
    for i in range(15):
        autor = criar_usuario(f"autor{i}")
        ana.alternar_seguir(autor)
        pub = publicar(autor, f"post {i} #teste")
        Curtida.objects.create(usuario=ana, publicacao=pub)
        pub.comentarios.create(autor=ana, texto="!")
    with django_assert_num_queries(1):
        resultado = [(p.autor.username, p.total_curtidas, p.curtida_por_mim) for p in feed(ana)]
    assert len(resultado) == 15


def test_busca_por_texto_e_hashtag_exata(ana, publicar):
    py = publicar(ana, "Aprendendo #python hoje")
    publicar(ana, "Gosto de #pythonista também")
    django = publicar(ana, "Django é ótimo")
    assert list(buscar(ana, "#python")) == [py]
    assert list(buscar(ana, "#PYTHON")) == [py]
    assert list(buscar(ana, "django")) == [django]
    assert list(buscar(ana, "#c++")) == []
