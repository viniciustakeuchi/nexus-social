from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from contas.forms import CadastroForm, PerfilForm
from contas.models import Usuario
from contas.tipos import RequisicaoAutenticada
from publicacoes.consultas import publicacoes_anotadas
from publicacoes.forms import PublicacaoForm


def _quer_json(request: HttpRequest) -> bool:
    return "application/json" in request.headers.get("Accept", "")


def cadastro(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("inicio")
    form = CadastroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, f"Bem-vindo ao Nexus, {usuario.nome}!")
        return redirect("inicio")
    return render(request, "registration/cadastro.html", {"form": form})


def perfil(request: HttpRequest, username: str) -> HttpResponse:
    dono = get_object_or_404(Usuario, username=username, is_active=True)
    publicacoes = publicacoes_anotadas(request.user).filter(autor=dono)
    pagina = Paginator(publicacoes, 10).get_page(request.GET.get("pagina"))
    contexto = {
        "dono": dono,
        "pagina": pagina,
        "total_seguidores": dono.seguidores.count(),
        "total_seguindo": dono.seguindo.count(),
        "total_publicacoes": publicacoes.count(),
        "eu_sigo": request.user.is_authenticated
        and request.user.pk != dono.pk
        and request.user.segue(dono),
        "form": PublicacaoForm() if request.user == dono else None,
    }
    return render(request, "contas/perfil.html", contexto)


@login_required
def editar_perfil(request: RequisicaoAutenticada) -> HttpResponse:
    usuario = request.user
    form = PerfilForm(request.POST or None, request.FILES or None, instance=usuario)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Perfil atualizado.")
        return redirect(usuario)
    return render(request, "contas/editar_perfil.html", {"form": form})


@login_required
@require_POST
def seguir(request: RequisicaoAutenticada, username: str) -> HttpResponse:
    usuario = request.user
    alvo = get_object_or_404(Usuario, username=username, is_active=True)
    if alvo.pk == usuario.pk:
        if _quer_json(request):
            return JsonResponse({"erro": "Você não pode seguir a si mesmo."}, status=400)
        return redirect(alvo)
    seguindo = usuario.alternar_seguir(alvo)
    if _quer_json(request):
        return JsonResponse({"seguindo": seguindo, "seguidores": alvo.seguidores.count()})
    return redirect(request.POST.get("proximo") or alvo.get_absolute_url())


def _lista_de_pessoas(
    request: HttpRequest, dono: Usuario, pessoas: QuerySet[Usuario], titulo: str
) -> HttpResponse:
    pagina = Paginator(pessoas.order_by("username"), 30).get_page(request.GET.get("pagina"))
    ids_que_sigo: set[int] = set()
    if request.user.is_authenticated:
        ids_que_sigo = set(request.user.seguindo.values_list("pk", flat=True))
    return render(
        request,
        "contas/lista_pessoas.html",
        {"dono": dono, "pagina": pagina, "titulo": titulo, "ids_que_sigo": ids_que_sigo},
    )


def seguidores(request: HttpRequest, username: str) -> HttpResponse:
    dono = get_object_or_404(Usuario, username=username, is_active=True)
    return _lista_de_pessoas(request, dono, dono.seguidores.filter(is_active=True), "Seguidores")


def seguindo(request: HttpRequest, username: str) -> HttpResponse:
    dono = get_object_or_404(Usuario, username=username, is_active=True)
    return _lista_de_pessoas(request, dono, dono.seguindo.filter(is_active=True), "Seguindo")
