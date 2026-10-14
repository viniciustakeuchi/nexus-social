from __future__ import annotations

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxLengthValidator
from django.db import models
from django.urls import reverse


def caminho_avatar(instancia: Usuario, nome_arquivo: str) -> str:
    return f"avatares/{instancia.pk or 'novo'}/{nome_arquivo}"


class Usuario(AbstractUser):
    nome_exibicao = models.CharField("nome de exibição", max_length=60, blank=True)
    bio = models.TextField(blank=True, validators=[MaxLengthValidator(280)])
    avatar = models.ImageField(upload_to=caminho_avatar, blank=True)
    seguindo = models.ManyToManyField(
        "self",
        through="Seguimento",
        symmetrical=False,
        related_name="seguidores",
        blank=True,
    )

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self) -> str:
        return f"@{self.username}"

    def get_absolute_url(self) -> str:
        return reverse("perfil", kwargs={"username": self.username})

    @property
    def nome(self) -> str:
        return self.nome_exibicao or self.username

    @property
    def iniciais(self) -> str:
        partes = self.nome.split()
        letras = "".join(parte[0] for parte in partes[:2]) if partes else self.username[:2]
        return letras.upper()

    def segue(self, outro: Usuario) -> bool:
        return Seguimento.objects.filter(seguidor=self, seguido=outro).exists()

    def alternar_seguir(self, outro: Usuario) -> bool:
        """Segue ou deixa de seguir `outro`. Devolve True se passou a seguir."""
        if outro.pk == self.pk:
            raise ValueError("Um usuário não pode seguir a si mesmo.")
        removidos, _ = Seguimento.objects.filter(seguidor=self, seguido=outro).delete()
        if removidos:
            return False
        Seguimento.objects.create(seguidor=self, seguido=outro)
        return True


class Seguimento(models.Model):
    seguidor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="+")
    seguido = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="+")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["seguidor", "seguido"], name="seguimento_unico"),
            models.CheckConstraint(
                condition=~models.Q(seguidor=models.F("seguido")),
                name="seguimento_nao_proprio",
            ),
        ]
        indexes = [models.Index(fields=["seguido", "-criado_em"])]

    def __str__(self) -> str:
        return f"{self.seguidor} segue {self.seguido}"
