FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_DEBUG=false \
    DJANGO_MEDIA_ROOT=/dados/media

WORKDIR /app

COPY pyproject.toml README.md ./
RUN pip install . && useradd --create-home nexus && mkdir -p /dados/media && chown nexus /dados/media

COPY . .
RUN DJANGO_SECRET_KEY=apenas-para-build python manage.py collectstatic --noinput \
    && chmod +x docker-entrypoint.sh

USER nexus
EXPOSE 8000
VOLUME ["/dados/media"]

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/saude/')"

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "nexus.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
