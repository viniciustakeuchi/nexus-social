import importlib

import pytest

from nexus import settings as configuracoes


def test_producao_exige_secret_key(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "false")
    monkeypatch.delenv("DJANGO_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        importlib.reload(configuracoes)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "x" * 50)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "nexus.exemplo.com, www.nexus.exemplo.com")
    recarregado = importlib.reload(configuracoes)
    assert recarregado.DEBUG is False
    assert recarregado.SESSION_COOKIE_SECURE is True
    assert recarregado.ALLOWED_HOSTS == ["nexus.exemplo.com", "www.nexus.exemplo.com"]
    monkeypatch.undo()
    importlib.reload(configuracoes)
