import argparse
import csv
from datetime import datetime, timezone
import os
from pathlib import Path

from google import genai

from generate_bag_images import (
    API_KEY,
    CSV_PATH,
    EDITORIAL_REF_DIR,
    LIFESTYLE_REF_DIR,
    generate_variant,
)
from supabase_sync import SupabaseSync

MANIFEST_PATH = Path("generation_manifest.csv")
REF_DIRS = {
    "lifestyle": LIFESTYLE_REF_DIR,
    "editorial": EDITORIAL_REF_DIR,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_manifest(rows: list[dict]):
    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def sync_row(sync: SupabaseSync, row: dict):
    if not sync:
        return
    remote_path = ""
    remote_url = ""
    if row.get("status") == "done" and row.get("final_image_path"):
        remote_path = f"final/{row['variant']}/{row['product_id']}.png"
        sync.upload_file(row["final_image_path"], remote_path)
        remote_url = sync.public_url(remote_path)
    sync.upsert_generation_row(row, remote_path=remote_path, remote_image_url=remote_url)


def should_process(row: dict, args) -> bool:
    if args.product_id and row["product_id"] != args.product_id:
        return False
    if args.variant and row["variant"] != args.variant:
        return False
    if args.status and row["status"] != args.status:
        return False
    if args.regenerate:
        return True
    return row["status"] != "done"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--status")
    parser.add_argument("--variant", choices=["lifestyle", "editorial"])
    parser.add_argument("--product-id")
    parser.add_argument("--regenerate", action="store_true")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        raise SystemExit("Missing generation_manifest.csv. Run python3 init_manifest.py first.")

    manifest_rows = read_csv_rows(MANIFEST_PATH)
    products = read_csv_rows(Path(CSV_PATH))
    client = genai.Client(api_key=API_KEY)
    sync = SupabaseSync.from_env()

    selected = [row for row in manifest_rows if should_process(row, args)]
    if args.limit:
        selected = selected[: args.limit]

    if not selected:
        print("No rows to process.")
        return

    print(f"Processing {len(selected)} rows")

    for row in selected:
        bag_index = int(row["bag_index"])
        product = products[bag_index - 1]
        row["last_attempt_at"] = now_iso()
        row["attempt_count"] = str(int(row["attempt_count"] or "0") + 1)
        row["error"] = ""
        if row["status"] == "pending":
            row["status"] = "running"
        write_manifest(manifest_rows)
        sync_row(sync, row)

        result = generate_variant(
            client,
            product,
            bag_index,
            row["variant"],
            REF_DIRS[row["variant"]],
        )

        row["base_image_path"] = result["base_path"]
        row["final_image_path"] = result["final_path"]
        if result["ok"]:
            row["status"] = "done"
            row["generated_at"] = now_iso()
            row["error"] = ""
        else:
            row["status"] = "failed"
            row["error"] = result.get("error", "unknown error")
        write_manifest(manifest_rows)
        sync_row(sync, row)

    print("Batch complete.")


if __name__ == "__main__":
    main()
