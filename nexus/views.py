from django.db import connection
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render


def saude(request: HttpRequest) -> JsonResponse:
    """Health check usado pelo Docker: confirma que o banco responde."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return JsonResponse({"status": "ok"})


def nao_encontrado(request: HttpRequest, exception: Exception) -> HttpResponse:
    return render(request, "404.html", status=404)
