"""
Assemble animation_demo.gif and animation_demo.webp from rendered anim_frames/
Runs in system Python (not Blender) - Pillow must be installed.
"""
import os, math
from PIL import Image, ImageDraw, ImageFont

project_root = r"c:\Users\mones\OneDrive\Desktop\samsang\Samsung_XR_Track01"
frames_dir   = os.path.join(project_root, "video", "anim_frames")
video_dir    = os.path.join(project_root, "video")

# ── Rebuild the same sequence used during rendering ──────────────────────────
def build_sequence():
    seq = []
    part1 = [
        (0.00,  0.00, "CENTER",     6),
        (0.00,  0.00, "CENTER",     4),
        (-1.00, 0.00, "LEFT",       8),
        (0.00,  0.00, "CENTER",     4),
        (1.00,  0.00, "RIGHT",      8),
        (0.00,  0.00, "CENTER",     4),
        (0.00,  1.00, "UP",         8),
        (0.00,  0.00, "CENTER",     4),
        (0.00, -1.00, "DOWN",       8),
        (0.00,  0.00, "CENTER",     6),
    ]
    seq.extend([(h, v, f"[1/3] {l}", hold) for h,v,l,hold in part1])

    for k in range(11):
        ki = k % 10
        theta = 2*math.pi*ki/10
        h, v = math.sin(theta), math.cos(theta)
        dirs = ["UP","UP-RIGHT","RIGHT","DN-RIGHT","DOWN","DN-LEFT","LEFT","UP-LEFT","UP-LEFT2","UP-RIGHT2"]
        seq.append((h, v, f"[2/3] CLOCK k={ki} {dirs[ki]}", 10 if ki==0 else 7))
    seq.append((0,0,"[2/3] CENTER", 8))

    for i in range(61):
        theta = 2*math.pi*(i/60)
        h, v = math.sin(theta), math.cos(theta)
        seq.append((h, v, f"[3/3] SMOOTH θ={math.degrees(theta):.0f}°", 1))
    return seq

sequence = build_sequence()

# Map each pose_XXXX.png → (h, v, label) ─────────────────────────────────────
pose_files = sorted([f for f in os.listdir(frames_dir) if f.startswith("pose_") and f.endswith(".png")])
print(f"Found {len(pose_files)} rendered pose frames")

# ── Annotation helper ─────────────────────────────────────────────────────────
try:
    font_big = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
    font_sm  = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   16)
    font_xs  = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   13)
except:
    font_big = font_sm = font_xs = ImageFont.load_default()

PART_COLORS = {"[1/3]": (255,180,0), "[2/3]": (0,210,100), "[3/3]": (100,170,255)}

def annotate(img, h, v, label, frame_num, total, scale):
    draw = ImageDraw.Draw(img, "RGBA")
    W, H = img.size

    # determine part
    part_key = next((k for k in PART_COLORS if k in label), "[1/3]")
    bar_col  = PART_COLORS[part_key]
    part_names = {"[1/3]":"PART 1 · 5-Direction Demo",
                  "[2/3]":"PART 2 · Clockwise Sweep",
                  "[3/3]":"PART 3 · Smooth Circle"}

    # top bar
    draw.rectangle([(0,0),(W,3)], fill=bar_col)
    draw.rectangle([(0,3),(W,52)], fill=(0,0,0,180))

    clean = label.replace("[1/3] ","").replace("[2/3] ","").replace("[3/3] ","")
    draw.text((10, 6),  part_names[part_key], font=font_sm, fill=bar_col)
    draw.text((W//2-80, 6),  clean,           font=font_big, fill=(255,255,255))
    draw.text((W-105,  8),  f"{frame_num+1:03d}/{total:03d}", font=font_xs, fill=(190,190,190))

    # bottom bar
    draw.rectangle([(0, H-44),(W,H)], fill=(0,0,0,160))
    draw.text((10, H-36), f"h = {h:+.3f}    v = {v:+.3f}", font=font_sm, fill=(255,255,255))

    # gaze compass
    cx, cy = W//2, H-22
    r = 15
    draw.ellipse([(cx-r,cy-r),(cx+r,cy+r)], outline=(130,130,130,200), width=1)
    draw.line([(cx-r,cy),(cx+r,cy)], fill=(70,70,70,180), width=1)
    draw.line([(cx,cy-r),(cx,cy+r)], fill=(70,70,70,180), width=1)
    dx = int(cx + h*r*0.85)
    dy = int(cy - v*r*0.85)
    draw.ellipse([(dx-4,dy-4),(dx+4,dy+4)], fill=bar_col+(255,))

    return img

# ── Build expanded frame list (handle holds) ──────────────────────────────────
# pose_files[i] corresponds to sequence[i] (one render per pose)
expanded = []  # (pil_image_path, h, v, label)
for pose_idx, (h, v, lbl, hold) in enumerate(sequence):
    if pose_idx >= len(pose_files):
        break
    path = os.path.join(frames_dir, pose_files[pose_idx])
    for _ in range(hold):
        expanded.append((path, h, v, lbl))

total = len(expanded)
print(f"Total video frames: {total}")

SCALE = 512   # output size

# ── Annotate + collect frames ─────────────────────────────────────────────────
print("Annotating frames...")
gif_frames = []
for i, (path, h, v, lbl) in enumerate(expanded):
    img = Image.open(path).convert("RGBA")
    img = img.resize((SCALE, SCALE), Image.LANCZOS)
    img = annotate(img, h, v, lbl, i, total, SCALE)
    gif_frames.append(img.convert("RGB"))
    if i % 30 == 0:
        print(f"  {i+1}/{total}...")

print(f"Annotated {len(gif_frames)} frames")

# ── Save GIF ──────────────────────────────────────────────────────────────────
gif_path = os.path.join(video_dir, "animation_demo.gif")
print(f"\nSaving GIF → {gif_path} ...")
gif_frames[0].save(
    gif_path, format="GIF", save_all=True,
    append_images=gif_frames[1:],
    duration=100,   # 10 fps
    loop=0, optimize=True
)
sz = os.path.getsize(gif_path)/1024/1024
print(f"  ✓ GIF saved: {sz:.1f} MB")

# ── Save WebP ─────────────────────────────────────────────────────────────────
webp_path = os.path.join(video_dir, "animation_demo.webp")
print(f"Saving WebP → {webp_path} ...")
gif_frames[0].save(
    webp_path, format="WEBP", save_all=True,
    append_images=gif_frames[1:],
    duration=85,    # 12 fps
    loop=0, quality=72, method=4
)
sz2 = os.path.getsize(webp_path)/1024/1024
print(f"  ✓ WebP saved: {sz2:.1f} MB")

# ── 5-direction preview GIF ───────────────────────────────────────────────────
n_part1 = sum(hold for _,_,lbl,hold in sequence if "[1/3]" in lbl)
preview_frames = gif_frames[:n_part1]
prev_path = os.path.join(video_dir, "preview_5directions.gif")
print(f"Saving preview GIF → {prev_path} ({len(preview_frames)} frames)...")
preview_frames[0].save(
    prev_path, format="GIF", save_all=True,
    append_images=preview_frames[1:],
    duration=140,   # 7 fps (slower = easier to read labels)
    loop=0, optimize=True
)
sz3 = os.path.getsize(prev_path)/1024/1024
print(f"  ✓ Preview saved: {sz3:.1f} MB")

print("\n" + "="*60)
print("ALL VIDEOS READY:")
print(f"  animation_demo.gif      → {gif_path}")
print(f"  animation_demo.webp     → {webp_path}")
print(f"  preview_5directions.gif → {prev_path}")
print("="*60)
print("\nOpen the video folder:")
print(f"  {video_dir}")
