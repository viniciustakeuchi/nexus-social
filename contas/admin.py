from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from contas.models import Seguimento, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = (
        *(UserAdmin.fieldsets or ()),
        ("Perfil", {"fields": ("nome_exibicao", "bio", "avatar")}),
    )
    list_display = ("username", "nome_exibicao", "email", "is_staff", "date_joined")


@admin.register(Seguimento)
class SeguimentoAdmin(admin.ModelAdmin):
    list_display = ("seguidor", "seguido", "criado_em")
    list_select_related = ("seguidor", "seguido")
