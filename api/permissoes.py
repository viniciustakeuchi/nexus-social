from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class AutorOuSomenteLeitura(permissions.BasePermission):
    message = "Só o autor pode alterar ou excluir este conteúdo."

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(obj.autor_id == request.user.pk)
