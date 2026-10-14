from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from contas.models import Usuario
from contas.tipos import RequisicaoAutenticada
from publicacoes.consultas import buscar, feed, publicacoes_anotadas
from publicacoes.forms import ComentarioForm, PublicacaoForm
from publicacoes.models import Comentario, Curtida, Publicacao

POR_PAGINA = 10


def _quer_json(request: HttpRequest) -> bool:
    return "application/json" in request.headers.get("Accept", "")


def _voltar(request: HttpRequest, padrao: str) -> HttpResponse:
    destino = request.POST.get("proximo", "")
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(destino)
    return redirect(padrao)


def inicio(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        destaques = publicacoes_anotadas(request.user).order_by(
            F("total_curtidas").desc(), "-criada_em"
        )
        return render(
            request,
            "publicacoes/boas_vindas.html",
            {
                "destaques": destaques[:3],
                "total_usuarios": Usuario.objects.filter(is_active=True).count(),
                "total_publicacoes": Publicacao.objects.count(),
            },
        )
    pagina = Paginator(feed(request.user), POR_PAGINA).get_page(request.GET.get("pagina"))
    return render(request, "publicacoes/feed.html", {"pagina": pagina, "form": PublicacaoForm()})


def explorar(request: HttpRequest) -> HttpResponse:
    termo = request.GET.get("q", "").strip()[:100]
    if termo:
        publicacoes = buscar(request.user, termo)
        pessoas = (
            Usuario.objects.filter(is_active=True)
            .filter(Q(username__icontains=termo.lstrip("@")) | Q(nome_exibicao__icontains=termo))
            .order_by("username")[:6]
            if not termo.startswith("#")
            else Usuario.objects.none()
        )
    else:
        publicacoes = publicacoes_anotadas(request.user)
        pessoas = Usuario.objects.none()
    pagina = Paginator(publicacoes, POR_PAGINA).get_page(request.GET.get("pagina"))
    em_alta = (
        Publicacao.objects.filter(texto__contains="#")
        .order_by("-criada_em")
        .values_list("texto", flat=True)[:200]
    )
    return render(
        request,
        "publicacoes/explorar.html",
        {
            "pagina": pagina,
            "termo": termo,
            "pessoas": pessoas,
            "hashtags_em_alta": _hashtags_em_alta(list(em_alta)),
            "mais_seguidos": Usuario.objects.filter(is_active=True)
            .annotate(n=Count("seguidores"))
            .order_by("-n", "username")[:5],
        },
    )


def _hashtags_em_alta(textos: list[str], limite: int = 8) -> list[tuple[str, int]]:
    from collections import Counter

    from publicacoes.models import extrair_hashtags

    contagem: Counter[str] = Counter()
    for texto in textos:
        contagem.update(extrair_hashtags(texto))
    return sorted(contagem.items(), key=lambda item: (-item[1], item[0]))[:limite]


def detalhe(request: HttpRequest, pk: int) -> HttpResponse:
    publicacao = get_object_or_404(publicacoes_anotadas(request.user), pk=pk)
    comentarios = publicacao.comentarios.select_related("autor")
    return render(
        request,
        "publicacoes/detalhe.html",
        {"publicacao": publicacao, "comentarios": comentarios, "form": ComentarioForm()},
    )


@login_required
@require_POST
def publicar(request: RequisicaoAutenticada) -> HttpResponse:
    form = PublicacaoForm(request.POST, request.FILES)
    if form.is_valid():
        publicacao = form.save(commit=False)
        publicacao.autor = request.user
        publicacao.save()
        messages.success(request, "Publicado!")
    else:
        for erros in form.errors.values():
            for erro in erros:
                messages.error(request, str(erro))
    return _voltar(request, "inicio")


@login_required
@require_POST
def curtir(request: RequisicaoAutenticada, pk: int) -> HttpResponse:
    publicacao = get_object_or_404(Publicacao, pk=pk)
    curtida = Curtida.alternar(request.user, publicacao)
    if _quer_json(request):
        return JsonResponse({"curtida": curtida, "total": publicacao.curtidas.count()})
    return _voltar(request, publicacao.get_absolute_url())


@login_required
@require_POST
def comentar(request: RequisicaoAutenticada, pk: int) -> HttpResponse:
    publicacao = get_object_or_404(Publicacao, pk=pk)
    form = ComentarioForm(request.POST)
    if form.is_valid():
        comentario = form.save(commit=False)
        comentario.autor = request.user
        comentario.publicacao = publicacao
        comentario.save()
    else:
        messages.error(request, "O comentário está vazio ou é longo demais.")
    return redirect(f"{publicacao.get_absolute_url()}#comentarios")


@login_required
@require_POST
def excluir(request: RequisicaoAutenticada, pk: int) -> HttpResponse:
    publicacao = get_object_or_404(Publicacao, pk=pk)
    if publicacao.autor_id != request.user.pk:
        return HttpResponseForbidden("Você só pode excluir as suas publicações.")
    publicacao.imagem.delete(save=False)
    publicacao.delete()
    messages.success(request, "Publicação excluída.")
    return redirect("inicio")


@login_required
@require_POST
def excluir_comentario(request: RequisicaoAutenticada, pk: int) -> HttpResponse:
    comentario = get_object_or_404(Comentario.objects.select_related("publicacao"), pk=pk)
    # Pode apagar quem escreveu o comentário ou o dono da publicação.
    if request.user.pk not in {comentario.autor_id, comentario.publicacao.autor_id}:
        return HttpResponseForbidden("Você não pode excluir este comentário.")
    comentario.delete()
    return redirect(f"{comentario.publicacao.get_absolute_url()}#comentarios")
