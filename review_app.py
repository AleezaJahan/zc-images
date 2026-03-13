import csv
from pathlib import Path

from flask import Flask, render_template_string, request, send_file, url_for

MANIFEST_PATH = Path("generation_manifest.csv")
APP = Flask(__name__)

HTML = """
<!doctype html>
<title>Bag Generation Status</title>
<style>
body { font-family: sans-serif; margin: 24px; }
form { margin-bottom: 20px; display: flex; gap: 12px; flex-wrap: wrap; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.card { border: 1px solid #ddd; border-radius: 10px; padding: 12px; }
.thumb { margin: 10px 0; }
.thumb img { width: 100%; aspect-ratio: 1 / 1; object-fit: cover; border-radius: 8px; border: 1px solid #eee; }
.empty { width: 100%; aspect-ratio: 1 / 1; border-radius: 8px; border: 1px dashed #ddd; display: grid; place-items: center; color: #888; background: #fafafa; }
.meta { font-size: 13px; color: #555; margin: 4px 0; }
.actions a { margin-right: 10px; font-size: 13px; }
.status { font-weight: 700; }
.summary { display: flex; gap: 12px; flex-wrap: wrap; margin: 0 0 18px; }
.pill { border: 1px solid #ddd; border-radius: 999px; padding: 6px 10px; font-size: 13px; }
</style>
<h1>Bag Generation Status</h1>
<div class="summary">
  <div class="pill">Total: {{ summary.total }}</div>
  <div class="pill">Done: {{ summary.done }}</div>
  <div class="pill">Pending: {{ summary.pending }}</div>
  <div class="pill">Failed: {{ summary.failed }}</div>
</div>
<form method="get">
  <input type="text" name="q" placeholder="Search bag name" value="{{ q }}">
  <select name="status">
    <option value="">All statuses</option>
    {% for s in statuses %}
    <option value="{{ s }}" {% if status == s %}selected{% endif %}>{{ s }}</option>
    {% endfor %}
  </select>
  <select name="variant">
    <option value="">All variants</option>
    {% for v in variants %}
    <option value="{{ v }}" {% if variant == v %}selected{% endif %}>{{ v }}</option>
    {% endfor %}
  </select>
  <button type="submit">Filter</button>
</form>
<div class="grid">
{% for row in rows %}
  <div class="card">
    <div><strong>{{ row.name }}</strong></div>
    <div class="meta">{{ row.product_id }} / {{ row.variant }}</div>
    <div class="meta status">Status: {{ row.status }}</div>
    {% if row.error %}<div class="meta">Error: {{ row.error }}</div>{% endif %}
    <div class="thumb">
      {% if row.final_exists %}
        <a href="{{ url_for('serve_image', kind='final', product_id=row.product_id, variant=row.variant) }}">
          <img src="{{ url_for('serve_image', kind='final', product_id=row.product_id, variant=row.variant) }}">
        </a>
      {% else %}
        <div class="empty">No final image yet</div>
      {% endif %}
    </div>
    <div class="actions">
      {% if row.final_exists %}<a href="{{ url_for('download_image', kind='final', product_id=row.product_id, variant=row.variant) }}">download final</a>{% endif %}
      <a href="{{ row.url }}" target="_blank">product</a>
    </div>
  </div>
{% endfor %}
</div>
"""


def read_manifest() -> list[dict]:
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["base_exists"] = Path(row["base_image_path"]).exists()
        row["final_exists"] = Path(row["final_image_path"]).exists()
    return rows


def find_row(product_id: str, variant: str) -> dict:
    for row in read_manifest():
        if row["product_id"] == product_id and row["variant"] == variant:
            return row
    raise FileNotFoundError("Row not found")


@APP.route("/")
def index():
    rows = read_manifest()
    q = request.args.get("q", "").lower().strip()
    status = request.args.get("status", "").strip()
    variant = request.args.get("variant", "").strip()
    if q:
        rows = [row for row in rows if q in row["name"].lower()]
    if status:
        rows = [row for row in rows if row["status"] == status]
    if variant:
        rows = [row for row in rows if row["variant"] == variant]
    all_rows = read_manifest()
    summary = {
        "total": len(all_rows),
        "done": sum(row["status"] == "done" for row in all_rows),
        "pending": sum(row["status"] == "pending" for row in all_rows),
        "failed": sum(row["status"] == "failed" for row in all_rows),
    }
    return render_template_string(
        HTML,
        rows=rows,
        q=q,
        status=status,
        variant=variant,
        statuses=sorted({row["status"] for row in read_manifest()}),
        variants=["lifestyle", "editorial"],
        summary=summary,
    )


@APP.route("/image/<kind>/<product_id>/<variant>")
def serve_image(kind: str, product_id: str, variant: str):
    row = find_row(product_id, variant)
    path = Path(row["base_image_path"] if kind == "base" else row["final_image_path"])
    return send_file(path)


@APP.route("/download/<kind>/<product_id>/<variant>")
def download_image(kind: str, product_id: str, variant: str):
    row = find_row(product_id, variant)
    path = Path(row["base_image_path"] if kind == "base" else row["final_image_path"])
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    APP.run(debug=True, port=5001)
