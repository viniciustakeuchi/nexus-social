from typing import Any

from rest_framework import serializers

from contas.models import Usuario
from publicacoes.models import LIMITE_COMENTARIO, LIMITE_TEXTO, Comentario, Publicacao


class AutorSerializer(serializers.ModelSerializer):
    nome = serializers.CharField(read_only=True)
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = Usuario
        fields: tuple[str, ...] = ("username", "nome", "avatar")


class PerfilSerializer(AutorSerializer):
    seguidores = serializers.IntegerField(source="total_seguidores", read_only=True)
    seguindo = serializers.IntegerField(source="total_seguindo", read_only=True)
    publicacoes = serializers.IntegerField(source="total_publicacoes", read_only=True)
    eu_sigo = serializers.SerializerMethodField()

    class Meta(AutorSerializer.Meta):
        fields = (
            "username",
            "nome",
            "avatar",
            "bio",
            "date_joined",
            "seguidores",
            "seguindo",
            "publicacoes",
            "eu_sigo",
        )

    def get_eu_sigo(self, obj: Usuario) -> bool:
        usuario = self.context["request"].user
        return bool(usuario.is_authenticated and usuario.pk != obj.pk and usuario.segue(obj))


class PublicacaoSerializer(serializers.ModelSerializer):
    autor = AutorSerializer(read_only=True)
    texto = serializers.CharField(max_length=LIMITE_TEXTO, trim_whitespace=True)
    total_curtidas = serializers.IntegerField(read_only=True, default=0)
    total_comentarios = serializers.IntegerField(read_only=True, default=0)
    curtida_por_mim = serializers.BooleanField(read_only=True, default=False)
    hashtags = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta:
        model = Publicacao
        fields = (
            "id",
            "autor",
            "texto",
            "imagem",
            "hashtags",
            "criada_em",
            "total_curtidas",
            "total_comentarios",
            "curtida_por_mim",
        )
        read_only_fields = ("criada_em",)

    def validate_imagem(self, imagem: Any) -> Any:
        if imagem and imagem.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("A imagem pode ter no máximo 5 MB.")
        return imagem


class ComentarioSerializer(serializers.ModelSerializer):
    autor = AutorSerializer(read_only=True)
    texto = serializers.CharField(max_length=LIMITE_COMENTARIO, trim_whitespace=True)

    class Meta:
        model = Comentario
        fields = ("id", "autor", "texto", "criado_em")
        read_only_fields = ("criado_em",)
