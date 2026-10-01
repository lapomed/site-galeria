"""Settings só para rodar testes localmente.

O projeto é Postgres-first e a migration 0016 usa SQL específico de Postgres
que o SQLite não executa. Para testar sem Postgres, desativamos as migrations
(as tabelas são criadas direto a partir dos models) e usamos SQLite em memória.
"""
from lapomed_gallery.settings import *  # noqa: F401,F403

DEBUG = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}


class _DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = _DisableMigrations()

# Evita exigência de manifesto do WhiteNoise ao renderizar {% static %} nos testes
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
