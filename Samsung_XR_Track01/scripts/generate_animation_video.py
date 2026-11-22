"""
Samsung XR Hackathon 2026 - Track 01
IMPROVED ANIMATION VIDEO GENERATOR

Creates a smooth, labelled animation showing ALL eye movements:
  PART 1: 5-Direction Demo  (CENTER → LEFT → RIGHT → UP → DOWN → CENTER)
  PART 2: Full Clockwise Sweep (10 stops around the circle)
  PART 3: Smooth Circular Loop (interpolated continuous motion)

Output: video/animation_demo.gif  (browser/everywhere compatible)
         video/animation_demo.webp (compact)
         video/frames/  (all individual PNG frames at 1024x1024)

Uses real Blender renders with actual 3D eyeball rotation.
"""

import os
import sys
import math
import json

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from wrapper.eyes import Eyes

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[WARNING] Pillow not found. Install with: pip install Pillow")


# ─────────────────────────────────────────────────────────────
# ANIMATION SEQUENCE DEFINITION
# ─────────────────────────────────────────────────────────────

def build_animation_sequence():
    """
    Build the full list of animation keyframes.
    Each entry: (h, v, label, hold_frames)
    hold_frames = how many video frames to hold this pose for GIF
    """
    sequence = []

    # --- PART 1: 5-Direction Demonstration ---
    # Start at center, dwell, then 5 directions, return to center
    part1 = [
        # (h,     v,     label,              hold)
        (0.00,  0.00,  "CENTER",            6),
        (0.00,  0.00,  "CENTER",            4),   # extra hold at start
        (-1.00,  0.00,  "LEFT",             8),
        (0.00,  0.00,  "CENTER",            4),
        (1.00,  0.00,  "RIGHT",             8),
        (0.00,  0.00,  "CENTER",            4),
        (0.00,  1.00,  "UP",                8),
        (0.00,  0.00,  "CENTER",            4),
        (0.00, -1.00,  "DOWN",              8),
        (0.00,  0.00,  "CENTER",            6),
    ]
    sequence.extend([(h, v, f"[1/3] {lbl}", hold) for h, v, lbl, hold in part1])

    # --- PART 2: 10-Stop Clockwise Circle ---
    for k in range(11):  # 11 to close the loop back to 0
        ki = k % 10
        theta = 2.0 * math.pi * ki / 10
        h = math.sin(theta)
        v = math.cos(theta)
        directions = ["UP", "UP-RIGHT", "RIGHT", "DN-RIGHT", "DOWN",
                      "DN-LEFT", "LEFT", "UP-LEFT", "UP-LEFT2", "UP-RIGHT2"]
        label = f"[2/3] CLOCK k={ki} {directions[ki]}"
        hold = 10 if ki == 0 else 7
        sequence.append((h, v, label, hold))

    # Back to center after clockwise
    sequence.append((0.00, 0.00, "[2/3] CENTER", 8))

    # --- PART 3: Smooth Continuous Circular Loop (interpolated) ---
    NUM_SMOOTH = 60   # 60 frames for one full smooth circle
    for i in range(NUM_SMOOTH + 1):  # +1 to close loop
        frac = i / NUM_SMOOTH
        theta = 2.0 * math.pi * frac
        h = math.sin(theta)
        v = math.cos(theta)
        label = f"[3/3] SMOOTH θ={math.degrees(theta):.0f}°"
        sequence.append((h, v, label, 1))

    return sequence


# ─────────────────────────────────────────────────────────────
# RENDER EACH FRAME
# ─────────────────────────────────────────────────────────────

def render_animation_frames(eyes, sequence, frames_dir):
    """Render all animation frames with Blender."""
    os.makedirs(frames_dir, exist_ok=True)

    rendered_paths = []
    frame_idx = 0
    total_frames = sum(hold for _, _, _, hold in sequence)

    print(f"\nRendering {len(sequence)} poses → {total_frames} total frames\n")

    prev_h, prev_v = None, None

    for pose_idx, (h, v, label, hold) in enumerate(sequence):
        # Skip re-render if pose is identical to previous (for hold frames)
        if h == prev_h and v == prev_v and pose_idx > 0 and hold == 1:
            # Reuse last rendered file
            last_path = rendered_paths[-1]
            for _ in range(hold):
                reuse_path = os.path.join(frames_dir, f"anim_{frame_idx:04d}.png")
                # Create symlink-style copy reference (we'll handle in GIF builder)
                rendered_paths.append(last_path)
                frame_idx += 1
            continue

        # Apply eye rotation
        eyes.move(h, v)
        state = eyes.get_state()
        pupil_l = state["pupil_2d_L"]
        pupil_r = state["pupil_2d_R"]

        # Render this pose to a base file
        base_path = os.path.join(frames_dir, f"pose_{pose_idx:04d}.png")
        eyes.render(base_path)

        print(f"  [{pose_idx+1:3d}/{len(sequence)}] {label:<30} h={h:+.3f} v={v:+.3f} "
              f"→ Pupils L:{pupil_l} R:{pupil_r}")

        # Duplicate for hold frames
        for _ in range(hold):
            rendered_paths.append(base_path)
            frame_idx += 1

        prev_h, prev_v = h, v

    return rendered_paths


# ─────────────────────────────────────────────────────────────
# ANNOTATE FRAMES WITH LABELS (using Pillow)
# ─────────────────────────────────────────────────────────────

def annotate_frame(img_path, label, h, v, frame_num, total_frames, pupil_l, pupil_r):
    """Add overlay text and gaze indicator to a rendered frame."""
    if not PIL_AVAILABLE:
        return img_path

    img = Image.open(img_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    # --- Top bar: dark overlay ---
    bar_h = 60
    overlay = Image.new("RGBA", (W, bar_h), (0, 0, 0, 180))
    img.paste(overlay, (0, 0), overlay)

    # --- Bottom bar ---
    bot_overlay = Image.new("RGBA", (W, 50), (0, 0, 0, 160))
    img.paste(bot_overlay, (0, H - 50), bot_overlay)

    # Try to load a font; fall back to default
    try:
        font_big = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 26)
        font_sm = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
        font_xs = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
    except (IOError, OSError):
        font_big = ImageFont.load_default()
        font_sm = font_big
        font_xs = font_big

    # Title text
    clean_label = label.replace("[1/3] ", "").replace("[2/3] ", "").replace("[3/3] ", "")
    part_label = ""
    if "[1/3]" in label:
        part_label = "PART 1: 5-Direction Demo"
        bar_color = (255, 180, 0)   # Gold
    elif "[2/3]" in label:
        part_label = "PART 2: Clockwise Sweep"
        bar_color = (0, 200, 100)   # Green
    else:
        part_label = "PART 3: Smooth Circle"
        bar_color = (100, 160, 255) # Blue

    # Colored accent bar at top (3px)
    draw.rectangle([(0, 0), (W, 3)], fill=bar_color)

    # Part label (top left)
    draw.text((12, 8), part_label, font=font_sm, fill=bar_color)

    # Pose label (top center)
    draw.text((W // 2 - 100, 8), clean_label, font=font_big, fill=(255, 255, 255))

    # Frame counter (top right)
    draw.text((W - 120, 10), f"Frame {frame_num+1:03d}/{total_frames:03d}", font=font_xs, fill=(200, 200, 200))

    # h/v values (bottom left)
    draw.text((12, H - 42), f"h = {h:+.3f}   v = {v:+.3f}", font=font_sm, fill=(255, 255, 255))

    # Pupil coordinates (bottom right)
    draw.text((W - 300, H - 42),
              f"L:({pupil_l[0]:.0f},{pupil_l[1]:.0f})  R:({pupil_r[0]:.0f},{pupil_r[1]:.0f})",
              font=font_xs, fill=(180, 220, 255))

    # --- Gaze Indicator Compass (bottom center) ---
    cx, cy = W // 2, H - 25
    r = 18
    # Circle
    draw.ellipse([(cx-r, cy-r), (cx+r, cy+r)], outline=(150, 150, 150), width=1)
    # Dot at h/v position
    dot_x = int(cx + h * r * 0.85)
    dot_y = int(cy - v * r * 0.85)   # -v because screen Y is inverted
    draw.ellipse([(dot_x-4, dot_y-4), (dot_x+4, dot_y+4)], fill=bar_color)
    # Crosshairs
    draw.line([(cx-r, cy), (cx+r, cy)], fill=(80, 80, 80), width=1)
    draw.line([(cx, cy-r), (cx, cy+r)], fill=(80, 80, 80), width=1)

    # Pupil crosshair markers ON the face
    for px_coord, py_coord, col in [(pupil_l[0], pupil_l[1], (0, 255, 100)),
                                    (pupil_r[0], pupil_r[1], (0, 200, 255))]:
        px_i = int(px_coord)
        py_i = int(py_coord)
        sz = 8
        draw.line([(px_i-sz, py_i), (px_i+sz, py_i)], fill=col, width=2)
        draw.line([(px_i, py_i-sz), (px_i, py_i+sz)], fill=col, width=2)
        draw.ellipse([(px_i-3, py_i-3), (px_i+3, py_i+3)], outline=col, width=1)

    out_path = img_path.replace(".png", "_annot.png")
    img.save(out_path, "PNG")
    return out_path


# ─────────────────────────────────────────────────────────────
# BUILD GIF / WEBP
# ─────────────────────────────────────────────────────────────

def build_animated_gif(frame_paths_annotated, output_path, fps=10, scale=512):
    """Assemble annotated frames into an animated GIF."""
    if not PIL_AVAILABLE:
        print("[ERROR] Pillow required for GIF creation.")
        return

    print(f"\nBuilding animated GIF ({len(frame_paths_annotated)} frames @ {fps}fps → {scale}px)...")
    duration_ms = int(1000 / fps)

    frames = []
    for path in frame_paths_annotated:
        try:
            img = Image.open(path).convert("RGB")
            img = img.resize((scale, scale), Image.LANCZOS)
            frames.append(img)
        except Exception as e:
            print(f"  [SKIP] {path}: {e}")

    if not frames:
        print("[ERROR] No frames loaded.")
        return

    frames[0].save(
        output_path,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True
    )
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  → Saved: {output_path}  ({len(frames)} frames, {size_mb:.1f} MB)")


def build_animated_webp(frame_paths_annotated, output_path, fps=12, scale=512):
    """Assemble annotated frames into animated WebP (smaller file size)."""
    if not PIL_AVAILABLE:
        return

    print(f"\nBuilding animated WebP ({len(frame_paths_annotated)} frames @ {fps}fps)...")
    duration_ms = int(1000 / fps)

    frames = []
    for path in frame_paths_annotated:
        try:
            img = Image.open(path).convert("RGB")
            img = img.resize((scale, scale), Image.LANCZOS)
            frames.append(img)
        except Exception as e:
            print(f"  [SKIP] {path}: {e}")

    if not frames:
        return

    frames[0].save(
        output_path,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        quality=75,
        method=4
    )
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  → Saved: {output_path}  ({len(frames)} frames, {size_mb:.1f} MB)")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print("=" * 72)
    print("   SAMSUNG XR TRACK 01 - IMPROVED ANIMATION VIDEO GENERATOR")
    print("=" * 72)

    scene_path = os.path.join(project_root, "scene.blend")
    frames_dir = os.path.join(project_root, "video", "anim_frames")
    video_dir = os.path.join(project_root, "video")
    os.makedirs(video_dir, exist_ok=True)
    os.makedirs(frames_dir, exist_ok=True)

    if not os.path.exists(scene_path):
        print(f"ERROR: {scene_path} not found.")
        sys.exit(1)

    # Initialize Eyes controller
    eyes = Eyes(scene_path=scene_path)
    cam_info = eyes.get_camera_calibration()
    print(f"Camera at: {cam_info['camera_position']}")

    # Build animation sequence
    sequence = build_animation_sequence()
    total_frames = sum(hold for _, _, _, hold in sequence)
    print(f"\nAnimation sequence: {len(sequence)} poses → {total_frames} video frames")

    # Render all poses
    rendered_paths = render_animation_frames(eyes, sequence, frames_dir)
    eyes.reset()

    # Annotate frames with labels + gaze indicators
    if PIL_AVAILABLE:
        print(f"\nAnnotating {len(rendered_paths)} frames...")
        annotated_paths = []
        seq_expanded = []
        for h, v, lbl, hold in sequence:
            for _ in range(hold):
                seq_expanded.append((h, v, lbl))

        for i, (base_path, (h, v, lbl)) in enumerate(zip(rendered_paths, seq_expanded)):
            eyes.move(h, v)
            pl = eyes.get_pupil_center_2d('L')
            pr = eyes.get_pupil_center_2d('R')
            eyes.reset()

            ann = annotate_frame(base_path, lbl, h, v, i, len(rendered_paths), pl, pr)
            annotated_paths.append(ann)
            if i % 20 == 0:
                print(f"  Annotated {i+1}/{len(rendered_paths)}...")

        # Build GIF (all three parts)
        gif_path = os.path.join(video_dir, "animation_demo.gif")
        build_animated_gif(annotated_paths, gif_path, fps=8, scale=512)

        # Build WebP
        webp_path = os.path.join(video_dir, "animation_demo.webp")
        build_animated_webp(annotated_paths, webp_path, fps=10, scale=512)

        # Also build a faster "preview" GIF (smaller, just 5-direction part)
        part1_frames = annotated_paths[:sum(hold for _, _, lbl, hold in sequence if "[1/3]" in lbl)]
        if part1_frames:
            preview_path = os.path.join(video_dir, "preview_5dir.gif")
            build_animated_gif(part1_frames, preview_path, fps=6, scale=400)
            print(f"  → Preview GIF: {preview_path}")

        print("\n" + "=" * 72)
        print("ANIMATION VIDEOS CREATED:")
        print(f"  Full demo GIF:  {gif_path}")
        print(f"  Full demo WebP: {webp_path}")
        print("=" * 72)
    else:
        print("\n[WARNING] Pillow not available. Install it to create GIF/WebP:")
        print("  pip install Pillow")
        print(f"\nRendered frames saved to: {frames_dir}")

    return rendered_paths


if __name__ == "__main__":
    main()
