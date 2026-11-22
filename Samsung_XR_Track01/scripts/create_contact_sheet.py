"""
Contact Sheet Generator for Samsung XR Hackathon Track 01
Creates a high-resolution 5 x 2 contact sheet from the 10 rendered frames
with frame numbers, theta values, and gaze direction labels.
"""

import os
import json
from PIL import Image, ImageDraw, ImageFont

def create_contact_sheet():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    renders_dir = os.path.join(project_root, "renders")
    metadata_path = os.path.join(project_root, "metadata.json")
    output_path = os.path.join(project_root, "contact_sheet.png")

    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Missing {metadata_path}. Run generate_ten_renders.py first.")

    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Grid specifications
    cols = 5
    rows = 2
    thumb_w = 420
    thumb_h = 420
    card_header_h = 60
    pad = 20
    title_h = 100

    sheet_w = pad + cols * (thumb_w + pad)
    sheet_h = title_h + pad + rows * (thumb_h + card_header_h + pad)

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(18, 22, 28))
    draw = ImageDraw.Draw(sheet)

    # Try loading default or TTF font
    font_large = ImageFont.load_default()
    font_title = font_large
    font_body = font_large

    # Gaze direction labels
    dir_names = [
        "Up (k=0)",
        "Up-Right (k=1)",
        "Right-Up (k=2)",
        "Right-Down (k=3)",
        "Down-Right (k=4)",
        "Down (k=5)",
        "Down-Left (k=6)",
        "Left-Down (k=7)",
        "Left-Up (k=8)",
        "Up-Left (k=9)"
    ]

    # Draw Title Header
    title_text = "SAMSUNG R&D XR HACKATHON 2026 - TRACK 01"
    sub_title = "Synthetic Eye Movement & Calibrated Virtual Camera Rendering (10-Sample Clockwise Sequence)"
    draw.text((pad, 25), title_text, fill=(240, 245, 255), font=font_title)
    draw.text((pad, 55), sub_title, fill=(130, 160, 200), font=font_body)
    draw.line([(pad, 85), (sheet_w - pad, 85)], fill=(60, 75, 95), width=2)

    for record in metadata:
        k = record["frame"]
        col = k % cols
        row = k // cols

        x0 = pad + col * (thumb_w + pad)
        y0 = title_h + pad + row * (thumb_h + card_header_h + pad)

        # Draw card container
        card_rect = [x0 - 2, y0 - 2, x0 + thumb_w + 2, y0 + thumb_h + card_header_h + 2]
        draw.rectangle(card_rect, fill=(26, 32, 42), outline=(50, 65, 85), width=2)

        # Load and resize render
        img_path = os.path.join(renders_dir, f"frame_{k:02d}.png")
        if os.path.exists(img_path):
            with Image.open(img_path) as im:
                thumb = im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
                sheet.paste(thumb, (x0, y0))
        else:
            draw.rectangle([x0, y0, x0 + thumb_w, y0 + thumb_h], fill=(40, 45, 55))
            draw.text((x0 + 20, y0 + 100), f"Missing frame_{k:02d}.png", fill=(255, 80, 80))

        # Draw card footer banner with metrics
        banner_y = y0 + thumb_h
        draw.rectangle([x0, banner_y, x0 + thumb_w, banner_y + card_header_h], fill=(32, 40, 52))

        theta = record["theta"]
        h = record["input"]["h"]
        v = record["input"]["v"]
        gaze_str = dir_names[k] if k < len(dir_names) else ""

        line1 = f"Frame {k:02d}: {gaze_str}"
        line2 = f"theta={theta:.2f} rad | h={h:+.2f}, v={v:+.2f}"
        pupil_str = f"L:({record['pupil_center_2D_L'][0]:.0f},{record['pupil_center_2D_L'][1]:.0f}) R:({record['pupil_center_2D_R'][0]:.0f},{record['pupil_center_2D_R'][1]:.0f})"

        draw.text((x0 + 10, banner_y + 8), line1, fill=(255, 215, 0), font=font_body)
        draw.text((x0 + 10, banner_y + 24), line2, fill=(200, 220, 240), font=font_body)
        draw.text((x0 + 10, banner_y + 40), pupil_str, fill=(140, 180, 210), font=font_body)

    sheet.save(output_path, "PNG")
    print(f"Contact sheet successfully created: {output_path} ({sheet_w}x{sheet_h})")

if __name__ == "__main__":
    create_contact_sheet()
