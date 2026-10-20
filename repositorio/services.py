"""Integração com o Backblaze B2 (API S3-compatível) via boto3.

Toda a transferência do conteúdo do arquivo acontece DIRETO entre o navegador e o
B2, por URLs assinadas geradas aqui. O Django nunca recebe o corpo do arquivo.
"""
import uuid
import re

from django.conf import settings

try:
    import boto3
    from botocore.client import Config as BotoConfig
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # boto3 ausente no ambiente — endpoints devem degradar com 503
    boto3 = None
    BotoConfig = None
    BotoCoreError = ClientError = Exception


class StorageNotConfigured(RuntimeError):
    """B2 sem credenciais/endpoint configurados."""


def is_configured():
    return bool(
        boto3 and settings.B2_ENDPOINT and settings.B2_KEY_ID
        and settings.B2_APP_KEY and settings.B2_BUCKET
    )


def b2_client():
    if not is_configured():
        raise StorageNotConfigured(
            "Backblaze B2 não configurado. Defina B2_ENDPOINT, B2_REGION, "
            "B2_KEY_ID, B2_APP_KEY e B2_BUCKET nas variáveis de ambiente."
        )
    return boto3.client(
        "s3",
        endpoint_url=settings.B2_ENDPOINT,
        region_name=settings.B2_REGION or None,
        aws_access_key_id=settings.B2_KEY_ID,
        aws_secret_access_key=settings.B2_APP_KEY,
        config=BotoConfig(signature_version="s3v4"),
    )


_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def build_object_key(filename):
    """Chave única e segura: repo/<uuid>/<nome-saneado>."""
    safe = _SAFE.sub("_", (filename or "arquivo").strip()).strip("_") or "arquivo"
    return f"repo/{uuid.uuid4().hex}/{safe[:180]}"


def ensure_bucket():
    """Cria o bucket se ainda não existir (idempotente). Serve tanto para o B2
    quanto para MinIO/qualquer S3-compatível recém-provisionado."""
    client = b2_client()
    bucket = settings.B2_BUCKET
    try:
        client.head_bucket(Bucket=bucket)
    except (BotoCoreError, ClientError):
        client.create_bucket(Bucket=bucket)
    return bucket


def create_multipart(key, content_type=""):
    client = b2_client()
    ensure_bucket()
    resp = client.create_multipart_upload(
        Bucket=settings.B2_BUCKET, Key=key,
        ContentType=content_type or "application/octet-stream",
    )
    return resp["UploadId"]


def sign_part(key, upload_id, part_number, expires=3600):
    client = b2_client()
    return client.generate_presigned_url(
        "upload_part",
        Params={
            "Bucket": settings.B2_BUCKET, "Key": key,
            "UploadId": upload_id, "PartNumber": int(part_number),
        },
        ExpiresIn=expires,
    )


def complete_multipart(key, upload_id, parts):
    """parts = [{"PartNumber": int, "ETag": str}, ...] em ordem."""
    client = b2_client()
    ordered = sorted(parts, key=lambda p: int(p["PartNumber"]))
    client.complete_multipart_upload(
        Bucket=settings.B2_BUCKET, Key=key, UploadId=upload_id,
        MultipartUpload={"Parts": [
            {"PartNumber": int(p["PartNumber"]), "ETag": p["ETag"]} for p in ordered
        ]},
    )


def abort_multipart(key, upload_id):
    try:
        client = b2_client()
        client.abort_multipart_upload(
            Bucket=settings.B2_BUCKET, Key=key, UploadId=upload_id,
        )
    except (StorageNotConfigured, BotoCoreError, ClientError):
        pass  # best-effort: abortar nunca deve derrubar a requisição


def presign_get(key, filename=None, expires=3600):
    client = b2_client()
    params = {"Bucket": settings.B2_BUCKET, "Key": key}
    if filename:
        safe = filename.replace('"', "")
        params["ResponseContentDisposition"] = f'attachment; filename="{safe}"'
    return client.generate_presigned_url("get_object", Params=params, ExpiresIn=expires)


def head_size(key):
    """Tamanho real do objeto no bucket (bytes) após o upload concluir."""
    try:
        client = b2_client()
        resp = client.head_object(Bucket=settings.B2_BUCKET, Key=key)
        return int(resp.get("ContentLength", 0))
    except (StorageNotConfigured, BotoCoreError, ClientError):
        return 0


def delete_object(key):
    try:
        client = b2_client()
        client.delete_object(Bucket=settings.B2_BUCKET, Key=key)
        return True
    except (StorageNotConfigured, BotoCoreError, ClientError):
        return False
