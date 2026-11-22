"""
Prepare User Face Texture for 3D Head Mesh
Extracts the user's facial features (hair, skin, eyebrows, nose, mouth/mustache)
and creates an aligned texture map with open eye sockets for the 3D eyeballs.
"""

import os
from PIL import Image, ImageFilter, ImageDraw

def prepare_texture():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    user_img_path = os.path.join(project_root, "textures", "user_face.jpg")
    out_tex_path = os.path.join(project_root, "textures", "head_texture.png")

    user_img = Image.open(user_img_path).convert("RGBA")
    w_src, h_src = user_img.size

    # Target texture resolution: 1024 x 1024
    tex_size = 1024
    tex = Image.new("RGBA", (tex_size, tex_size), color=(185, 135, 110, 255))
    draw = ImageDraw.Draw(tex)

    # In user_face.jpg:
    # Eye midpoint is at (286.0, 170.5)
    # Eye distance is 64 px
    # In 3D head model:
    # Head spans from X = -0.095m to +0.095m (width 0.190m)
    # Head spans from Z = -0.120m to +0.130m (height 0.250m)
    # Eye distance in 3D is 0.064m
    # We map head width 0.24m to tex_size 1024 px:
    # Scale: 1024 px / 0.24m = 4266.67 px/m
    # 0.064m eye distance = 273 px in the texture!
    # Original eye distance is 64 px, so scale factor = 273.0 / 64.0 = 4.2656
    scale_factor = 4.2656

    new_w = int(w_src * scale_factor)
    new_h = int(h_src * scale_factor)

    scaled_user = user_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Eye midpoint in scaled image:
    scaled_mid_x = int(286.0 * scale_factor)
    scaled_mid_y = int(170.5 * scale_factor)

    # In texture, place eye midpoint at (512, 450)
    target_mid_x = 512
    target_mid_y = 450

    paste_x = target_mid_x - scaled_mid_x
    paste_y = target_mid_y - scaled_mid_y

    # Fill background with average skin & hair tone
    # Top/back hair color
    hair_color = (35, 30, 30, 255)
    skin_color = (185, 135, 110, 255)

    # Background gradient
    for y in range(tex_size):
        if y < 350:
            t = min(1.0, (350 - y) / 200.0)
            c = tuple(int(skin_color[i] * (1 - t) + hair_color[i] * t) for i in range(3)) + (255,)
            draw.line([(0, y), (tex_size, y)], fill=c)
        else:
            draw.line([(0, y), (tex_size, y)], fill=skin_color)

    # Create an elliptical feather mask for seamless face blending
    mask = Image.new("L", (new_w, new_h), 0)
    mask_draw = ImageDraw.Draw(mask)

    # Face ellipse around head
    face_box = [
        scaled_mid_x - int(115 * scale_factor),
        scaled_mid_y - int(125 * scale_factor),
        scaled_mid_x + int(115 * scale_factor),
        scaled_mid_y + int(135 * scale_factor)
    ]
    mask_draw.ellipse(face_box, fill=255)
    # Smooth feathering
    mask = mask.filter(ImageFilter.GaussianBlur(radius=25))

    # Mask out the eyeballs so the 3D articulated eyeballs with dark brown irises show through
    # Left eye socket (subject's left, viewer's right)
    eye_hole_radius_x = int(16 * scale_factor) # ~68 px
    eye_hole_radius_y = int(10 * scale_factor) # ~42 px

    # Viewer right eye
    center_l_x = int(318.0 * scale_factor)
    center_l_y = int(173.0 * scale_factor)
    # Viewer left eye
    center_r_x = int(254.0 * scale_factor)
    center_r_y = int(168.0 * scale_factor)

    eye_mask = Image.new("L", (new_w, new_h), 255)
    eye_mask_draw = ImageDraw.Draw(eye_mask)

    eye_mask_draw.ellipse([
        center_l_x - eye_hole_radius_x, center_l_y - eye_hole_radius_y,
        center_l_x + eye_hole_radius_x, center_l_y + eye_hole_radius_y
    ], fill=0)

    eye_mask_draw.ellipse([
        center_r_x - eye_hole_radius_x, center_r_y - eye_hole_radius_y,
        center_r_x + eye_hole_radius_x, center_r_y + eye_hole_radius_y
    ], fill=0)

    eye_mask = eye_mask.filter(ImageFilter.GaussianBlur(radius=8))

    # Combine masks
    from PIL import ImageChops
    final_mask = ImageChops.multiply(mask, eye_mask)

    # Paste face onto texture
    tex.paste(scaled_user, (paste_x, paste_y), final_mask)

    # Save texture
    tex.save(out_tex_path, "PNG")
    print(f"User face texture successfully generated: {out_tex_path} (1024x1024)")

if __name__ == "__main__":
    prepare_texture()
