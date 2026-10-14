from __future__ import annotations

import re

from django.conf import settings
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.urls import reverse

LIMITE_TEXTO = 500
LIMITE_COMENTARIO = 300
PADRAO_HASHTAG = re.compile(r"(?<![\w&])#(\w{1,50})", re.UNICODE)
PADRAO_MENCAO = re.compile(r"(?<![\w@])@([\w.@+-]{1,150})", re.UNICODE)


def caminho_imagem(instancia: Publicacao, nome_arquivo: str) -> str:
    return f"publicacoes/{instancia.autor_id}/{nome_arquivo}"


def extrair_hashtags(texto: str) -> list[str]:
    """Hashtags únicas e em minúsculas, na ordem em que aparecem."""
    vistas: dict[str, None] = {}
    for tag in PADRAO_HASHTAG.findall(texto):
        vistas.setdefault(tag.lower(), None)
    return list(vistas)


class Publicacao(models.Model):
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="publicacoes"
    )
    texto = models.TextField(validators=[MinLengthValidator(1), MaxLengthValidator(LIMITE_TEXTO)])
    imagem = models.ImageField(upload_to=caminho_imagem, blank=True)
    criada_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-criada_em", "-id"]
        verbose_name = "publicação"
        verbose_name_plural = "publicações"
        indexes = [models.Index(fields=["autor", "-criada_em"])]

    def __str__(self) -> str:
        resumo = self.texto if len(self.texto) <= 40 else f"{self.texto[:40]}…"
        return f"{self.autor}: {resumo}"

    def get_absolute_url(self) -> str:
        return reverse("publicacao", kwargs={"pk": self.pk})

    @property
    def hashtags(self) -> list[str]:
        return extrair_hashtags(self.texto)


class Curtida(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="curtidas"
    )
    publicacao = models.ForeignKey(Publicacao, on_delete=models.CASCADE, related_name="curtidas")
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["usuario", "publicacao"], name="curtida_unica"),
        ]

    def __str__(self) -> str:
        return f"{self.usuario} curtiu #{self.publicacao_id}"

    @classmethod
    def alternar(cls, usuario: models.Model, publicacao: Publicacao) -> bool:
        """Curte ou descurte. Devolve True se a publicação ficou curtida."""
        removidas, _ = cls.objects.filter(usuario=usuario, publicacao=publicacao).delete()
        if removidas:
            return False
        cls.objects.get_or_create(usuario=usuario, publicacao=publicacao)
        return True


class Comentario(models.Model):
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comentarios"
    )
    publicacao = models.ForeignKey(Publicacao, on_delete=models.CASCADE, related_name="comentarios")
    texto = models.TextField(
        validators=[MinLengthValidator(1), MaxLengthValidator(LIMITE_COMENTARIO)]
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["criado_em", "id"]
        verbose_name = "comentário"

    def __str__(self) -> str:
        return f"{self.autor} em #{self.publicacao_id}"
