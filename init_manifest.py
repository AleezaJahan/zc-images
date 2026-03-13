import csv
from pathlib import Path

from generate_bag_images import CSV_PATH, build_output_paths

MANIFEST_PATH = Path("generation_manifest.csv")
VARIANTS = ["lifestyle", "editorial"]


def infer_status(base_path: str, final_path: str) -> str:
    if Path(final_path).exists():
        return "done"
    if Path(base_path).exists():
        return "base_done"
    return "pending"


def main():
    with open(CSV_PATH, encoding="utf-8") as f:
        products = list(csv.DictReader(f))

    rows = []
    for idx, product in enumerate(products, start=1):
        product_id = f"{idx:04d}"
        for variant in VARIANTS:
            paths = build_output_paths(product, idx, variant)
            rows.append(
                {
                    "product_id": product_id,
                    "bag_index": str(idx),
                    "variant": variant,
                    "name": product.get("name", ""),
                    "url": product.get("url", ""),
                    "image_url": product.get("image_url", ""),
                    "status": infer_status(paths["base_path"], paths["final_path"]),
                    "base_image_path": paths["base_path"],
                    "final_image_path": paths["final_path"],
                    "error": "",
                    "attempt_count": "0",
                    "last_attempt_at": "",
                    "generated_at": "",
                }
            )

    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "product_id",
                "bag_index",
                "variant",
                "name",
                "url",
                "image_url",
                "status",
                "base_image_path",
                "final_image_path",
                "error",
                "attempt_count",
                "last_attempt_at",
                "generated_at",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
