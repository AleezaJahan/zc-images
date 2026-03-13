"""
Generate lifestyle and editorial model photos for Zero Collective bags.

Two-step workflow per bag and per variant:
1. Generate a styled scene with a generic placeholder bag that matches the
   target bag's scale/carry geometry.
2. Edit that scene by replacing only the placeholder with the exact bag
   product image while preserving the scene.
"""

import csv
import io
import os
import glob
import urllib.request

from google import genai
from google.genai import types
from PIL import Image, ImageOps

API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL = "gemini-3-pro-image-preview"

CSV_PATH = "zero_collective_products.csv"
OUTPUT_DIR = "generated"
LIFESTYLE_REF_DIR = "lifestyle_ref"
EDITORIAL_REF_DIR = "editorial_ref"
NUM_BAGS = 5


def get_image_paths(ref_dir: str) -> list[str]:
    """Return supported image paths from a reference directory."""
    return sorted(
        glob.glob(os.path.join(ref_dir, "*.png"))
        + glob.glob(os.path.join(ref_dir, "*.jpg"))
        + glob.glob(os.path.join(ref_dir, "*.jpeg"))
        + glob.glob(os.path.join(ref_dir, "*.webp"))
    )


def load_image(path: str) -> Image.Image:
    """Load and resize one reference image."""
    img = Image.open(path).convert("RGB")
    img.thumbnail((1024, 1024), Image.LANCZOS)
    return img


def load_references(ref_dir: str) -> list[Image.Image]:
    """Load all reference images from a directory."""
    return [load_image(path) for path in get_image_paths(ref_dir)]


def download_bag_image(url: str):
    """Download the bag product image from its CDN URL."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.thumbnail((1024, 1024), Image.LANCZOS)
        return img
    except Exception as exc:
        print(f"  Warning: could not download bag image: {exc}")
        return None


def pil_to_part(img: Image.Image) -> types.Part:
    """Convert a PIL image to a Gemini API Part."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png")


def to_square(img: Image.Image) -> Image.Image:
    """Force image to square as a safeguard."""
    side = min(img.size)
    return ImageOps.fit(
        img,
        (side, side),
        method=Image.LANCZOS,
        centering=(0.5, 0.45),
    )


def save_as_square(img: Image.Image, out_path: str):
    """Save a square-cropped version of the image."""
    to_square(img).save(out_path)


def slugify_name(name: str) -> str:
    """Build a stable filename slug from a bag name."""
    return name.lower().replace(" ", "_")[:60]


def extract_first_image(response):
    """Get the first image part from a Gemini response."""
    for part in response.candidates[0].content.parts:
        if part.inline_data and part.inline_data.mime_type.startswith("image/"):
            return Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
    return None


def build_size_guidance(dimensions: str, ideal_for: str) -> str:
    """Convert catalog size metadata into stronger human-readable scale guidance."""
    dim_upper = (dimensions or "").upper()
    if "X-SMALL" in dim_upper:
        size_label = "mini / extra-small"
        scale_line = (
            "The bag should read as genuinely mini on the body, small in the hand, "
            "and not like a medium everyday bag."
        )
    elif "SMALL" in dim_upper:
        size_label = "small / compact"
        scale_line = (
            "The bag should read as compact and small on the body, clearly smaller "
            "than a medium everyday shoulder bag."
        )
    elif "MEDIUM" in dim_upper:
        size_label = "medium / everyday"
        scale_line = (
            "The bag should read as a true everyday medium size, noticeably larger "
            "than a mini bag but not oversized."
        )
    elif "LARGE" in dim_upper:
        size_label = "large / oversized"
        scale_line = (
            "The bag should read as large on the body, with substantial volume and "
            "presence, not compact or mini."
        )
    else:
        size_label = "match catalog dimensions"
        scale_line = "The bag scale should match the catalog dimensions naturally on-body."

    capacity_line = (
        f"It should look realistically capable of holding: {ideal_for}."
        if ideal_for
        else "Its capacity should look realistic for its stated size."
    )
    return f"{size_label}. {scale_line} {capacity_line}"


def build_carry_guidance(name: str, features: str, handle_drop: str) -> str:
    """Infer likely carry position from catalog cues."""
    text = f"{name} {features}".upper()
    handle_text = (handle_drop or "").strip()

    if "TOP HANDLE" in text or "LADY DIOR" in text or "VANITY" in text:
        return (
            "Carry guidance: this bag should read primarily as a hand-carried or top-handle "
            "bag, not a low crossbody."
        )
    if "WALLET" in text or "CHAIN WALLET" in text:
        return (
            "Carry guidance: this bag should read as a very small chain shoulder or evening "
            "bag, worn close to the body."
        )
    if "TOTE" in text or "CABAS" in text or "SHOPPING" in text or "BASKET" in text:
        return (
            "Carry guidance: this bag should read as a roomy tote carried by hand or on the "
            "shoulder, with visible volume."
        )
    if "HOBO" in text or "BAGUETTE" in text:
        return (
            "Carry guidance: this bag should sit naturally under the arm or close on the "
            "shoulder, not far down on the torso."
        )
    if "SADDLE" in text:
        return (
            "Carry guidance: this bag should read as a short-strap shoulder or hand-carried "
            "statement bag, sitting fairly close to the body."
        )

    if '"' in handle_text:
        try:
            first_num = float(handle_text.split('"')[0].replace("-", "").strip())
        except Exception:
            first_num = None
        if first_num is not None:
            if first_num <= 6:
                return (
                    "Carry guidance: the strap/drop is short, so the bag should be hand-carried "
                    "or sit high and close to the body."
                )
            if first_num <= 12:
                return (
                    "Carry guidance: the bag should sit high on the shoulder or under the arm, "
                    "not low like a crossbody."
                )
            if first_num <= 18:
                return (
                    "Carry guidance: the bag should read as a regular shoulder bag with a "
                    "natural shoulder drop."
                )
            return (
                "Carry guidance: the strap/drop is long enough that the bag can read as a long "
                "shoulder or crossbody-style carry."
            )

    return (
        "Carry guidance: hold or wear the bag in a way that looks natural for its shape and "
        "strap design, with believable placement on the body."
    )


def infer_bag_geometry(name: str, features: str) -> str:
    """Infer a simple placeholder geometry for the scene-generation step."""
    text = f"{name} {features}".upper()
    if "TOP HANDLE" in text or "LADY DIOR" in text or "VANITY" in text:
        return "structured top-handle bag"
    if "TOTE" in text or "CABAS" in text or "SHOPPING" in text or "BASKET" in text:
        return "structured tote bag"
    if "HOBO" in text:
        return "soft hobo shoulder bag"
    if "BAGUETTE" in text:
        return "compact underarm baguette bag"
    if "SADDLE" in text:
        return "curved saddle shoulder bag"
    if "WALLET" in text:
        return "small wallet-on-chain bag"
    if "BUCKET" in text or "BALLOON" in text:
        return "bucket bag"
    if "FLAP" in text:
        return "structured flap bag"
    return "luxury handbag"


def extract_styling_hint(colour: str, design_notes: str) -> tuple[str, str]:
    """Extract an outfit hint, handling misaligned rows."""
    notes_source = design_notes
    clean_colour = colour
    if (not notes_source or len(notes_source) < 50) and colour and len(colour) > 80:
        notes_source = colour
        clean_colour = ""

    styling_hint = ""
    if notes_source:
        sentences = [s.strip() for s in notes_source.split(".") if s.strip()]
        for sentence in reversed(sentences):
            if any(kw in sentence.lower() for kw in ["wear", "style", "pair"]):
                styling_hint = sentence + "."
                break
    return clean_colour, styling_hint


def build_scene_prompt(bag: dict, variant: str) -> str:
    """Step 1: create a scene with a geometry-matched placeholder bag."""
    name = bag.get("name", "luxury bag")
    colour = bag.get("colour", "")
    material = bag.get("made_of", "")
    features = bag.get("features", "")
    dimensions = bag.get("dimensions", "")
    handle_drop = bag.get("handle_drop", "")
    ideal_for = bag.get("ideal_for", "")
    design_notes = bag.get("design_notes", "")

    colour, styling_hint = extract_styling_hint(colour, design_notes)
    size_line = build_size_guidance(dimensions, ideal_for)
    carry_line = build_carry_guidance(name, features, handle_drop)
    geometry = infer_bag_geometry(name, features)

    if variant == "lifestyle":
        style_block = (
            "The lifestyle references are crucial and should dominate the look of the image. "
            "Use the lifestyle references as the style guide. Match their candid, "
            "real-life smartphone-photo feel. The image should look like a stylish "
            "iPhone snapshot, not a professional campaign shoot. Use natural ambient "
            "light, full-scene sharpness, visible background detail, and realistic "
            "phone-camera rendering. No portrait mode, no cinematic bokeh, no shallow "
            "depth of field, no glossy studio look."
        )
        opening = "Generate a square lifestyle fashion photo."
    else:
        style_block = (
            "The editorial references are crucial and should dominate the look of the image. "
            "Use the editorial references as the style guide. Match a similar polished "
            "editorial vibe, framing, lighting, and environment quality. The image should "
            "look like a polished fashion editorial or campaign still. Keep the scene crisp, "
            "readable, and not blurry."
        )
        opening = "Generate a square editorial fashion photo."

    outfit_line = (
        f"Outfit direction: {styling_hint}"
        if styling_hint
        else "Outfit should suit the bag and not overpower it."
    )

    return f"""{opening}

Use the attached style references as the main guide for the image.
The references are crucial. They should dominate the scene style, environment, framing, lighting, camera treatment, and focus behavior.
If there is any conflict between a generic model prior and the references, follow the references.

Create a new image in that visual world with a simple placeholder bag that can be replaced later.
The placeholder bag only needs to roughly match:
- bag type: {geometry}
- size: {dimensions if dimensions else 'match target size naturally'}
- scale guidance: {size_line}
- {carry_line}

Keep the placeholder bag simple, clean, unbranded, and easy to replace later.

{style_block}
{outfit_line}
Bag context for styling only: {colour if colour else 'natural luxury colour palette'}, {material if material else 'luxury material'}, {features if features else 'luxury handbag details'}.

Create a new image with a different model identity from the references. Do not copy the exact face, outfit, or pose.
Composition guidance:
- the scene should feel very close to the style references
- keep the placeholder bag visible and readable
- avoid extreme perspective distortion

No text or watermark. Square 1:1. Keep it natural and believable.
"""


def build_edit_prompt(bag: dict) -> str:
    """Step 2: replace placeholder with exact bag while preserving the scene."""
    name = bag.get("name", "luxury bag")
    colour = bag.get("colour", "")
    material = bag.get("made_of", "")
    features = bag.get("features", "")
    dimensions = bag.get("dimensions", "")
    handle_drop = bag.get("handle_drop", "")
    ideal_for = bag.get("ideal_for", "")
    design_notes = bag.get("design_notes", "")

    colour, _ = extract_styling_hint(colour, design_notes)
    size_line = build_size_guidance(dimensions, ideal_for)
    carry_line = build_carry_guidance(name, features, handle_drop)

    return f"""Edit the attached base scene image.

Keep everything else the same:
- preserve the model identity
- preserve the environment
- preserve the lighting
- preserve the framing and camera angle
- preserve the outfit
- preserve the pose
- preserve the focus behavior and overall photographic treatment

Replace only the placeholder bag with the attached product object called Bag_A.

Preserve Bag_A exactly:
- same silhouette and proportions
- same structure and shape
- same quilting or stitching pattern
- same hardware placement and finish
- same strap design and handle shape
- same closure details
- same colour and material look
- keep Bag_A structurally intact and product-accurate
- do not soften, collapse, reshape, or simplify Bag_A
- do not invent extra pockets, folds, straps, quilting, or hardware
- do not change the bag opening, flap shape, body depth, or handle geometry

Bag_A details:
- name: {name}
- size: {dimensions if dimensions else 'match product image naturally'}
- scale guidance: {size_line}
- {carry_line}
- features: {features if features else 'match product image'}
- colour/material context: {colour if colour else 'match product image'}, {material if material else 'match product image'}

Composition guidance:
- place Bag_A where the placeholder bag was
- preserve the same overall scale and carry position
- keep Bag_A clearly visible and mostly unobstructed
- show Bag_A from a clear front or three-quarter angle
- avoid extreme perspective distortion on Bag_A

No text or watermark. Final output square 1:1.
"""


def build_output_paths(bag: dict, bag_index: int, variant: str) -> dict[str, str]:
    """Return output paths for base and final images."""
    name = bag.get("name", f"bag_{bag_index}")
    slug = slugify_name(name)
    out_dir = os.path.join(OUTPUT_DIR, variant)
    base_dir = os.path.join(OUTPUT_DIR, f"{variant}_base")
    return {
        "final_dir": out_dir,
        "base_dir": base_dir,
        "final_path": os.path.join(out_dir, f"{bag_index}_{slug}.png"),
        "base_path": os.path.join(base_dir, f"{bag_index}_{slug}.png"),
    }


def generate_variant(client, bag: dict, bag_index: int, variant: str, ref_dir: str):
    """Generate either a lifestyle or editorial image for one bag via 2 steps."""
    ref_paths = get_image_paths(ref_dir)
    paths = build_output_paths(bag, bag_index, variant)
    out_dir = paths["final_dir"]
    base_dir = paths["base_dir"]
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(base_dir, exist_ok=True)

    if not ref_paths:
        print(f"  [{variant}] -> Error: no reference images found in {ref_dir}")
        return {"ok": False, "error": f"no reference images found in {ref_dir}", **paths}

    name = bag.get("name", f"bag_{bag_index}")
    out_path = paths["final_path"]
    base_path = paths["base_path"]

    refs = load_references(ref_dir)
    print(f"  [{variant}] using {len(refs)} refs from {ref_dir}")
    for path in ref_paths:
        print(f"    - {path}")

    bag_img = download_bag_image(bag.get("image_url", ""))

    # Step 1: create base scene with placeholder bag
    scene_prompt = build_scene_prompt(bag, variant)
    scene_parts = []
    for idx, ref in enumerate(refs, 1):
        scene_parts.append(
            types.Part.from_text(
                text=(
                    f"{variant.upper()} STYLE REFERENCE {idx} — use this for style only: "
                    "environment, lighting, framing, camera treatment, and focus behavior. "
                    "Match the photographic treatment of this reference. Do not copy the exact "
                    "face, outfit, or pose."
                )
            )
        )
        scene_parts.append(pil_to_part(ref))
    scene_parts.append(types.Part.from_text(text=scene_prompt))

    scene_img_count = sum(1 for part in scene_parts if hasattr(part, "inline_data") and part.inline_data)
    print(f"  [{variant}] step 1 sending {scene_img_count} images ({len(refs)} style refs)")

    try:
        scene_response = client.models.generate_content(
            model=MODEL,
            contents=types.Content(parts=scene_parts),
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                temperature=0.3,
            ),
        )
    except Exception as exc:
        print(f"  [{variant}] step 1 -> Error: {exc}")
        return {"ok": False, "error": str(exc), **paths}

    base_img = extract_first_image(scene_response)
    if base_img is None:
        print(f"  [{variant}] step 1 -> No image returned")
        return {"ok": False, "error": "step 1 returned no image", **paths}

    base_img = to_square(base_img)
    base_img.save(base_path)
    print(f"  [{variant}] step 1 -> Saved base scene to {base_path}")

    # Step 2: replace placeholder with exact bag
    if not bag_img:
        print(f"  [{variant}] step 2 -> Skipped, bag product image unavailable")
        return {"ok": False, "error": "bag product image unavailable", **paths}

    edit_prompt = build_edit_prompt(bag)
    edit_parts = [
        types.Part.from_text(
            text=(
                "BASE SCENE IMAGE — preserve this scene, model, outfit, pose, lighting, "
                "composition, and photographic treatment."
            )
        ),
        pil_to_part(base_img),
        types.Part.from_text(
            text=(
                "PRODUCT OBJECT REFERENCE — this image is Bag_A. Replace the placeholder bag "
                "with Bag_A while preserving the rest of the scene."
            )
        ),
        pil_to_part(bag_img),
        types.Part.from_text(text=edit_prompt),
    ]

    print(f"  [{variant}] step 2 sending 2 images (base scene + bag object)")

    try:
        edit_response = client.models.generate_content(
            model=MODEL,
            contents=types.Content(parts=edit_parts),
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                temperature=0.15,
            ),
        )
    except Exception as exc:
        print(f"  [{variant}] step 2 -> Error: {exc}")
        return {"ok": False, "error": str(exc), **paths}

    final_img = extract_first_image(edit_response)
    if final_img is None:
        print(f"  [{variant}] step 2 -> No image returned")
        return {"ok": False, "error": "step 2 returned no image", **paths}

    save_as_square(final_img, out_path)
    print(f"  [{variant}] step 2 -> Saved final to {out_path}")
    return {"ok": True, "error": "", **paths}


def main():
    if not API_KEY:
        raise SystemExit("Missing GEMINI_API_KEY environment variable.")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    client = genai.Client(api_key=API_KEY)

    with open(CSV_PATH, encoding="utf-8") as f:
        bags = list(csv.DictReader(f))[:NUM_BAGS]

    print(f"Generating 2-step lifestyle + editorial images for {len(bags)} bags\n")

    for i, bag in enumerate(bags, 1):
        name = bag.get("name", f"bag_{i}")
        print(f"[{i}/{len(bags)}] {name}")
        generate_variant(client, bag, i, "lifestyle", LIFESTYLE_REF_DIR)
        generate_variant(client, bag, i, "editorial", EDITORIAL_REF_DIR)
        print()

    print(
        f"\nDone! Check '{OUTPUT_DIR}/lifestyle', '{OUTPUT_DIR}/editorial', "
        f"'{OUTPUT_DIR}/lifestyle_base', and '{OUTPUT_DIR}/editorial_base'."
    )


if __name__ == "__main__":
    main()
