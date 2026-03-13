import csv
from pathlib import Path

from init_manifest import MANIFEST_PATH
from supabase_sync import SupabaseSync


def main():
    sync = SupabaseSync.from_env()
    if not sync:
        raise SystemExit(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY. "
            "Export them before running this script."
        )

    with MANIFEST_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    uploaded = 0
    failed_uploads = 0
    for row in rows:
        remote_path = ""
        remote_url = ""
        if row["status"] == "done" and row["final_image_path"] and Path(row["final_image_path"]).exists():
            remote_path = f"final/{row['variant']}/{row['product_id']}.png"
            try:
                sync.upload_file(row["final_image_path"], remote_path)
                remote_url = sync.public_url(remote_path)
                uploaded += 1
            except Exception as exc:
                failed_uploads += 1
                print(
                    f"Upload failed for {row['product_id']} {row['variant']}: {exc}. "
                    "Seeding row without remote image URL."
                )
                remote_path = ""
                remote_url = ""
        sync.upsert_generation_row(row, remote_image_path=remote_path, remote_image_url=remote_url)

    print(
        f"Seeded {len(rows)} rows to Supabase. "
        f"Uploaded {uploaded} images, {failed_uploads} uploads failed."
    )


if __name__ == "__main__":
    main()
