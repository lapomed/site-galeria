"""Sobe um arquivo LOCAL para o B2 e cria o registro no Repositório.

Serve para carregar arquivos de teste (ex.: o GLB do Engenho) direto do servidor,
sem passar pela tela. boto3 faz o multipart automaticamente para arquivos grandes.

    uv run python manage.py repo_ingest "/caminho/Engenho.glb" --name "Engenho (GLB)" --folder "Testes"

Roda contra o banco apontado por DATABASE_URL (local SQLite ou produção). Para que
o arquivo apareça na intranet de produção, rode com a DATABASE_URL de produção
DEPOIS que as migrações do app repositorio já tiverem sido aplicadas lá.
"""
import mimetypes
import os

from django.core.management.base import BaseCommand, CommandError

from repositorio import services
from repositorio.models import RepoFolder, RepoFile


class Command(BaseCommand):
    help = "Sobe um arquivo local para o B2 e cria o RepoFile correspondente."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Caminho do arquivo local a enviar.")
        parser.add_argument("--name", default=None, help="Nome exibido (padrão: nome do arquivo).")
        parser.add_argument("--folder", default=None, help="Nome da pasta de destino (criada na raiz se não existir).")
        parser.add_argument("--content-type", default=None, help="Força o content-type.")

    def handle(self, *args, **opts):
        if not services.is_configured():
            raise CommandError("B2 não configurado (defina as variáveis B2_*).")

        path = opts["path"]
        if not os.path.isfile(path):
            raise CommandError(f"Arquivo não encontrado: {path}")

        filename = os.path.basename(path)
        name = opts["name"] or filename
        size = os.path.getsize(path)
        content_type = opts["content_type"] or mimetypes.guess_type(filename)[0] or "application/octet-stream"

        folder = None
        if opts["folder"]:
            folder, _ = RepoFolder.objects.get_or_create(name=opts["folder"], parent=None)

        key = services.build_object_key(filename)
        self.stdout.write(f"Enviando {filename}")
        self.stdout.write(f"  tamanho: {size/1024/1024:.1f} MB | tipo: {content_type}")
        self.stdout.write(f"  chave:   {key}")

        from django.conf import settings
        try:
            from boto3.s3.transfer import TransferConfig
            cfg = TransferConfig(
                multipart_threshold=settings.B2_PART_SIZE,
                multipart_chunksize=settings.B2_PART_SIZE,
                max_concurrency=4,
            )
            client = services.b2_client()
            services.ensure_bucket()
            seen = {"pct": -1}

            def progress(bytes_amount, _seen=seen):
                _seen["done"] = _seen.get("done", 0) + bytes_amount
                pct = int(_seen["done"] * 100 / size) if size else 100
                if pct != _seen["pct"] and pct % 5 == 0:
                    _seen["pct"] = pct
                    self.stdout.write(f"  ... {pct}%")

            client.upload_file(
                path, settings.B2_BUCKET, key,
                ExtraArgs={"ContentType": content_type},
                Config=cfg, Callback=progress,
            )
        except Exception as exc:  # noqa: BLE001
            raise CommandError(f"Falha no upload para o B2: {exc}") from exc

        obj = RepoFile.objects.create(
            folder=folder, name=name, original_filename=filename,
            object_key=key, size=size, content_type=content_type, status="ready",
        )
        self.stdout.write(self.style.SUCCESS(
            f"\nOK — RepoFile #{obj.pk} criado"
            + (f" na pasta '{folder.name}'" if folder else " na raiz")
            + f". Veja em /intranet/repositorio/."
        ))
