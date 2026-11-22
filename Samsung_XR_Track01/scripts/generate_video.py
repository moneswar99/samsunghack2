"""
Video Generation Script for Samsung XR Hackathon Track 01
Generates:
1. H.264 MP4 video rendered via Blender's internal FFmpeg encoder
2. Animated WebP video with metrics overlay
3. Animated GIF video
"""

import os
import sys
import math
from PIL import Image, ImageDraw, ImageFont

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
video_dir = os.path.join(project_root, "video")
renders_dir = os.path.join(project_root, "renders")
os.makedirs(video_dir, exist_ok=True)

def generate_animated_files():
    print("Generating animated WebP and GIF videos from rendered frames...")
    frames = []
    num_frames = 10

    dir_names = [
        "Up (Top)", "Up-Right", "Right-Up", "Right-Down", "Down-Right",
        "Down (Bottom)", "Down-Left", "Left-Down", "Left-Up", "Up-Left"
    ]

    for k in range(num_frames):
        img_path = os.path.join(renders_dir, f"frame_{k:02d}.png")
        if not os.path.exists(img_path):
            continue
        im = Image.open(img_path).convert("RGBA")
        
        # Add visual metric overlay on the frame
        draw = ImageDraw.Draw(im)
        font = ImageFont.load_default()
        
        theta = 2.0 * math.pi * k / num_frames
        h_val = math.sin(theta)
        v_val = math.cos(theta)
        
        # Bottom status bar
        bar_h = 70
        draw.rectangle([0, 1024 - bar_h, 1024, 1024], fill=(15, 20, 28, 220))
        
        line1 = f"SAMSUNG XR HACKATHON 2026 | FRAME {k:02d} / 09 : {dir_names[k]}"
        line2 = f"theta = {theta:.3f} rad ({(theta*180/math.pi):.1f} deg) | h = {h_val:+.3f}, v = {v_val:+.3f} | Fixation: 35cm | Camera: 40cm"
        
        draw.text((24, 1024 - 55), line1, fill=(255, 215, 0), font=font)
        draw.text((24, 1024 - 32), line2, fill=(180, 220, 255), font=font)
        
        # Small corner watermark
        draw.rectangle([16, 16, 260, 48], fill=(20, 30, 45, 200), outline=(50, 70, 100))
        draw.text((26, 24), "Track 01: 3D Eye Movement", fill=(6, 182, 212), font=font)
        
        frames.append(im.convert("RGB"))

    if frames:
        # Save high-res WebP animation (24-bit color, 2.5 fps = 400ms duration per frame)
        webp_path = os.path.join(video_dir, "demo_gaze_sequence.webp")
        frames[0].save(
            webp_path,
            save_all=True,
            append_images=frames[1:],
            duration=400,
            loop=0,
            quality=95
        )
        print(f"Saved animated WebP video: {webp_path}")

        # Save GIF animation
        gif_path = os.path.join(video_dir, "demo_gaze_sequence.gif")
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=400,
            loop=0
        )
        print(f"Saved animated GIF video: {gif_path}")

if __name__ == "__main__":
    generate_animated_files()
