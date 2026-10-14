from typing import Any

from django import forms

from publicacoes.models import LIMITE_COMENTARIO, LIMITE_TEXTO, Comentario, Publicacao

TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024


class PublicacaoForm(forms.ModelForm):
    class Meta:
        model = Publicacao
        fields = ("texto", "imagem")
        widgets = {
            "texto": forms.Textarea(
                attrs={
                    "rows": 3,
                    "maxlength": LIMITE_TEXTO,
                    "placeholder": "O que está acontecendo na sua rede?",
                    "data-contador": LIMITE_TEXTO,
                }
            ),
            "imagem": forms.FileInput(attrs={"accept": "image/*"}),
        }
        labels = {"texto": "", "imagem": "Imagem"}
        error_messages = {"texto": {"required": "Escreva alguma coisa antes de publicar."}}

    def clean_imagem(self) -> Any:
        imagem = self.cleaned_data.get("imagem")
        if imagem and getattr(imagem, "size", 0) > TAMANHO_MAXIMO_IMAGEM:
            raise forms.ValidationError("A imagem pode ter no máximo 5 MB.")
        return imagem


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = Comentario
        fields = ("texto",)
        widgets = {
            "texto": forms.TextInput(
                attrs={
                    "class": "entrada",
                    "maxlength": LIMITE_COMENTARIO,
                    "placeholder": "Escreva um comentário…",
                }
            )
        }
        labels = {"texto": ""}
