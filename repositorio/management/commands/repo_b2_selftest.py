"""Valida a configuração do Backblaze B2 com um round-trip multipart real.

Não toca no banco. Faz: create_multipart -> 2 upload_part -> complete ->
head_object -> GET por URL assinada -> compara bytes -> delete. Use depois de
setar as variáveis B2_* para confirmar credenciais + bucket + permissões.

    uv run python manage.py repo_b2_selftest

Observação: isto valida o lado servidor. O **CORS** do bucket (ExposeHeaders: ETag)
só é exercido pelo upload do navegador — teste a tela depois de configurar o CORS.
"""
import os
import uuid
import urllib.request

from django.core.management.base import BaseCommand, CommandError

from repositorio import services


class Command(BaseCommand):
    help = "Testa a configuração do Backblaze B2 (round-trip multipart, sem banco)."

    def handle(self, *args, **opts):
        if not services.is_configured():
            raise CommandError(
                "B2 não configurado. Defina B2_ENDPOINT, B2_REGION, B2_KEY_ID, "
                "B2_APP_KEY e B2_BUCKET no ambiente antes de rodar este teste."
            )
        from django.conf import settings
        self.stdout.write(f"Endpoint: {settings.B2_ENDPOINT}")
        self.stdout.write(f"Bucket:   {settings.B2_BUCKET}")

        client = services.b2_client()
        bucket = settings.B2_BUCKET
        key = f"repo/_selftest/{uuid.uuid4().hex}.bin"
        part1 = os.urandom(5 * 1024 * 1024)   # 5 MB (mínimo de parte no S3/B2)
        part2 = os.urandom(1024)              # última parte pode ser pequena
        payload = part1 + part2

        upload_id = None
        try:
            self.stdout.write("1/6 create_multipart_upload...")
            upload_id = client.create_multipart_upload(Bucket=bucket, Key=key)["UploadId"]

            self.stdout.write("2/6 upload_part x2...")
            parts = []
            for n, chunk in enumerate((part1, part2), start=1):
                r = client.upload_part(Bucket=bucket, Key=key, UploadId=upload_id,
                                       PartNumber=n, Body=chunk)
                parts.append({"PartNumber": n, "ETag": r["ETag"]})

            self.stdout.write("3/6 complete_multipart_upload...")
            client.complete_multipart_upload(
                Bucket=bucket, Key=key, UploadId=upload_id,
                MultipartUpload={"Parts": parts},
            )
            upload_id = None  # concluído, não precisa abortar

            self.stdout.write("4/6 head_object...")
            size = int(client.head_object(Bucket=bucket, Key=key)["ContentLength"])
            if size != len(payload):
                raise CommandError(f"Tamanho divergente: {size} != {len(payload)}")

            self.stdout.write("5/6 GET por URL assinada...")
            url = services.presign_get(key)
            with urllib.request.urlopen(url, timeout=60) as resp:
                got = resp.read()
            if got != payload:
                raise CommandError("Conteúdo baixado difere do enviado.")

            self.stdout.write("6/6 delete_object...")
            services.delete_object(key)

            self.stdout.write(self.style.SUCCESS(
                "\nOK — B2 configurado corretamente (upload multipart, download "
                "assinado e exclusão funcionando). Falta só confirmar o CORS do "
                "bucket testando um upload pela tela do Repositório."
            ))
        except CommandError:
            if upload_id:
                services.abort_multipart(key, upload_id)
            raise
        except Exception as exc:  # noqa: BLE001
            if upload_id:
                services.abort_multipart(key, upload_id)
            raise CommandError(f"Falha ao falar com o B2: {exc}") from exc
