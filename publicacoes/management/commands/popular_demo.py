"""Cria usuários, publicações, curtidas e comentários de exemplo.

Uso: python manage.py popular_demo  (todos os usuários de demo usam a senha "nexus12345")
"""

import random
from typing import Any

from django.core.management.base import BaseCommand
from django.db import transaction

from contas.models import Seguimento, Usuario
from publicacoes.models import Comentario, Curtida, Publicacao

SENHA_DEMO = "nexus12345"

PESSOAS = [
    ("ana.dev", "Ana Ribeiro", "Backend em Python. Café, Django e testes que passam de primeira."),
    ("bruno", "Bruno Lima", "Engenheiro de dados. Pipelines, SQL e muita paciência."),
    ("carla", "Carla Souza", "Designer de produto apaixonada por roxo 💜"),
    ("diego.ml", "Diego Martins", "Machine learning e café coado."),
    ("elisa", "Elisa Nakamura", "Fotógrafa nas horas vagas, QA nas horas pagas."),
    ("felipe", "Felipe Araújo", "Estudante de ADS. Aprendendo em público."),
]

TEXTOS = [
    "Primeiro deploy do dia sem quebrar nada. Sexta-feira abençoada #deploy #python",
    "Alguém mais acha que #django continua sendo o framework mais produtivo para web?",
    "Paleta nova do produto ficou incrível, todo mundo de roxo agora 💜 #design",
    "Dica rápida: select_related e prefetch_related resolvem 90% dos N+1 #django #performance",
    "Hoje aprendi a escrever testes com pytest-django e não volto mais atrás #python #testes",
    "Fim de semana de fotos no parque. A luz das 17h é outra coisa #fotografia",
    "Quem vai no meetup de Python sábado? @ana.dev @bruno #comunidade",
    "Pipeline de dados rodando de hora em hora, logs limpos, coração tranquilo #dados",
    "Revisão de código boa é a que ensina, não a que só aponta erro #carreira",
    "Lendo sobre arquitetura hexagonal. Separar domínio de framework muda tudo #arquitetura",
    "Meu primeiro PR aceito num projeto open source! 🎉 #opensource",
    "Modelo treinado, métricas ok, agora é colocar em produção sem medo #ml #python",
]

COMENTARIOS = [
    "Concordo demais!",
    "Que massa, parabéns!",
    "Salvando essa dica 👀",
    "Isso me salvou semana passada.",
    "Bora! Estarei lá.",
    "Ficou lindo 💜",
]


class Command(BaseCommand):
    help = "Popula o banco com dados de demonstração."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument("--semente", type=int, default=42)

    @transaction.atomic
    def handle(self, *args: Any, **opcoes: Any) -> None:
        aleatorio = random.Random(opcoes["semente"])  # noqa: S311
        usuarios = []
        for username, nome, bio in PESSOAS:
            usuario, criado = Usuario.objects.get_or_create(
                username=username,
                defaults={"nome_exibicao": nome, "bio": bio, "email": f"{username}@exemplo.com"},
            )
            if criado:
                usuario.set_password(SENHA_DEMO)
                usuario.save()
            usuarios.append(usuario)

        for usuario in usuarios:
            for outro in aleatorio.sample(usuarios, k=4):
                if outro != usuario:
                    Seguimento.objects.get_or_create(seguidor=usuario, seguido=outro)

        if Publicacao.objects.filter(autor__in=usuarios).exists():
            self.stdout.write("Publicações de demo já existem; nada a fazer.")
            return

        for indice, texto in enumerate(TEXTOS):
            publicacao = Publicacao.objects.create(
                autor=usuarios[indice % len(usuarios)], texto=texto
            )
            for fa in aleatorio.sample(usuarios, k=aleatorio.randint(1, len(usuarios))):
                Curtida.objects.get_or_create(usuario=fa, publicacao=publicacao)
            for autor in aleatorio.sample(usuarios, k=aleatorio.randint(0, 2)):
                Comentario.objects.create(
                    autor=autor, publicacao=publicacao, texto=aleatorio.choice(COMENTARIOS)
                )

        self.stdout.write(
            self.style.SUCCESS(f"Pronto: {len(usuarios)} usuários, senha '{SENHA_DEMO}'.")
        )
