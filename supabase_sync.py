import json
import mimetypes
import os
import socket
import urllib.error
import urllib.request
from pathlib import Path


class SupabaseSync:
    def __init__(self, url: str, service_role_key: str, bucket: str):
        self.url = url.rstrip("/")
        self.service_role_key = service_role_key
        self.bucket = bucket

    @classmethod
    def from_env(cls):
        url = os.getenv("SUPABASE_URL", "").strip()
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        bucket = os.getenv("SUPABASE_BUCKET", "bag-renders").strip()
        if not url or not key:
            return None
        return cls(url, key, bucket)

    def _json_request(self, method: str, path: str, payload):
        req = urllib.request.Request(
            f"{self.url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json",
                "Prefer": "resolution=merge-duplicates,return=minimal",
            },
            method=method,
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()

    def upsert_generation_row(self, row: dict, remote_image_path: str = "", remote_image_url: str = ""):
        payload = [
            {
                "id": f"{row['product_id']}_{row['variant']}",
                "product_id": row["product_id"],
                "bag_index": int(row["bag_index"]),
                "name": row["name"],
                "product_url": row["url"],
                "variant": row["variant"],
                "status": row["status"],
                "final_image_path": remote_image_path,
                "final_image_url": remote_image_url,
                "error": row.get("error", ""),
                "attempt_count": int(row.get("attempt_count") or 0),
                "last_attempt_at": row.get("last_attempt_at") or None,
                "generated_at": row.get("generated_at") or None,
            }
        ]
        self._json_request("POST", "/rest/v1/bag_generations", payload)

    def upload_file(self, local_path: str, remote_path: str):
        file_path = Path(local_path)
        if not file_path.exists():
            raise FileNotFoundError(local_path)

        mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        data = file_path.read_bytes()
        req = urllib.request.Request(
            f"{self.url}/storage/v1/object/{self.bucket}/{remote_path}",
            data=data,
            headers={
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": mime_type,
                "x-upsert": "true",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            # Retry with PUT in case object already exists and POST is rejected.
            req = urllib.request.Request(
                f"{self.url}/storage/v1/object/{self.bucket}/{remote_path}",
                data=data,
                headers={
                    "apikey": self.service_role_key,
                    "Authorization": f"Bearer {self.service_role_key}",
                    "Content-Type": mime_type,
                    "x-upsert": "true",
                },
                method="PUT",
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    return resp.read()
            except Exception as inner_exc:
                raise RuntimeError(
                    f"Supabase upload failed for {remote_path}: {inner_exc}"
                ) from inner_exc
        except socket.timeout as exc:
            raise RuntimeError(
                f"Timed out uploading {remote_path} to Supabase Storage. "
                "Check bucket setup and network connectivity."
            ) from exc

    def public_url(self, remote_path: str) -> str:
        return f"{self.url}/storage/v1/object/public/{self.bucket}/{remote_path}"
