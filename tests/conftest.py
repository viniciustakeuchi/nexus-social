from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from contas.models import Usuario
from publicacoes.models import Publicacao

SENHA = "senha-forte-123"


@pytest.fixture(autouse=True)
def _midia_temporaria(settings: Any, tmp_path: Path) -> None:
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": []}


@pytest.fixture
def criar_usuario(db: None) -> Callable[..., Usuario]:
    def _criar(username: str = "ana", **extra: Any) -> Usuario:
        extra.setdefault("email", f"{username}@exemplo.com")
        return Usuario.objects.create_user(username=username, password=SENHA, **extra)

    return _criar


@pytest.fixture
def ana(criar_usuario: Callable[..., Usuario]) -> Usuario:
    return criar_usuario("ana", nome_exibicao="Ana Ribeiro")


@pytest.fixture
def bruno(criar_usuario: Callable[..., Usuario]) -> Usuario:
    return criar_usuario("bruno")


@pytest.fixture
def cliente_ana(client: Client, ana: Usuario) -> Client:
    client.force_login(ana)
    return client


@pytest.fixture
def api(ana: Usuario) -> APIClient:
    cliente = APIClient()
    token = Token.objects.create(user=ana)
    cliente.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return cliente


@pytest.fixture
def publicar() -> Callable[..., Publicacao]:
    def _publicar(autor: Usuario, texto: str = "Olá, Nexus!") -> Publicacao:
        return Publicacao.objects.create(autor=autor, texto=texto)

    return _publicar


def gerar_imagem(nome: str = "foto.png", tamanho: tuple[int, int] = (20, 20)) -> SimpleUploadedFile:
    buffer = BytesIO()
    Image.new("RGB", tamanho, (124, 58, 237)).save(buffer, format="PNG")
    return SimpleUploadedFile(nome, buffer.getvalue(), content_type="image/png")
