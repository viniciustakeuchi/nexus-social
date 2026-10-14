from django.contrib import admin

from publicacoes.models import Comentario, Curtida, Publicacao


class ComentarioInline(admin.TabularInline):
    model = Comentario
    extra = 0
    raw_id_fields = ("autor",)


@admin.register(Publicacao)
class PublicacaoAdmin(admin.ModelAdmin):
    list_display = ("id", "autor", "__str__", "criada_em")
    list_select_related = ("autor",)
    search_fields = ("texto", "autor__username")
    raw_id_fields = ("autor",)
    inlines = [ComentarioInline]


@admin.register(Curtida)
class CurtidaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "publicacao", "criada_em")
    raw_id_fields = ("usuario", "publicacao")
