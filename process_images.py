#!/usr/bin/env python3
"""
Automatisk billedebehandlingsscript for HUM-lokalet:
- Læser billeder fra img/raw/
- Optimerer til JPG, maks 1200px bredde, 80% kvalitet til img/uploads/
- Renser al EXIF/kamera/GPS metadata fuldstændigt via exiftool
- Kan opdatere content/data.json med billedtekst
"""

import os
import sys
import glob
import subprocess
import json
from PIL import Image

RAW_DIR = "img/raw"
UPLOADS_DIR = "img/uploads"
DATA_FILE = "content/data.json"

def process_image(src_path, caption=None):
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    basename = os.path.splitext(os.path.basename(src_path))[0]
    out_name = f"{basename}.jpg"
    out_path = os.path.join(UPLOADS_DIR, out_name)

    # 1. Åbn billede og optimér
    with Image.open(src_path) as im:
        im = im.convert('RGB')
        width, height = im.size
        if width > 1200:
            new_height = int(height * (1200 / width))
            im = im.resize((1200, new_height), Image.Resampling.LANCZOS)
        im.save(out_path, format="JPEG", quality=80, optimize=True)

    # 2. Strip alt metadata med exiftool
    subprocess.run(["exiftool", "-all=", "-overwrite_original", out_path], check=True)
    print(f"Behandlet og renset: {out_path}")

    # 3. Tilføj til content/data.json hvis ønsket
    if caption:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        img_rel_url = f"./{out_path}"
        # Undgå dubletter
        exists = any(item.get("image") == img_rel_url for item in data.get("gallery", []))
        if not exists:
            data.setdefault("gallery", []).append({
                "image": img_rel_url,
                "caption": caption
            })
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Tilføjet til galleri i data.json med billedtekst: '{caption}'")

if __name__ == '__main__':
    images = glob.glob(os.path.join(RAW_DIR, "*.*"))
    valid_images = [f for f in images if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp'))]
    if not valid_images:
        print(f"Ingen råfotos fundet i {RAW_DIR}.")
        sys.exit(0)
    for img_file in valid_images:
        cap = sys.argv[1] if len(sys.argv) > 1 else "Dokumentation af lokalerammer og foreningsfaciliteter."
        process_image(img_file, cap)
