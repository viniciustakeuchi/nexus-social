from typing import Any

from django import forms
from django.contrib.auth.forms import UserCreationForm

from contas.models import Usuario

TAMANHO_MAXIMO_AVATAR = 2 * 1024 * 1024


class CadastroForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ("username", "nome_exibicao", "email")
        labels = {"username": "Nome de usuário", "email": "E-mail"}
        help_texts = {"username": "Letras, números e @ . + - _ (até 150 caracteres)."}

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True

    def clean_email(self) -> str:
        email: str = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Já existe uma conta com este e-mail.")
        return email


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ("nome_exibicao", "bio", "avatar")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3, "maxlength": 280}),
            "avatar": forms.FileInput(attrs={"accept": "image/*"}),
        }

    def clean_avatar(self) -> Any:
        avatar = self.cleaned_data.get("avatar")
        if avatar and getattr(avatar, "size", 0) > TAMANHO_MAXIMO_AVATAR:
            raise forms.ValidationError("A foto pode ter no máximo 2 MB.")
        return avatar
