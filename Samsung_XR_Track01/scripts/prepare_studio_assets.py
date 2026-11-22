"""
Prepare Studio Photo Face and Iris Assets for Photorealistic 3D Scene
"""
import os
import math
from PIL import Image, ImageFilter, ImageDraw, ImageChops

def prepare_assets():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_path = os.path.join(project_root, "textures", "studio_face.jpg")
    textures_dir = os.path.join(project_root, "textures")
    os.makedirs(textures_dir, exist_ok=True)

    img = Image.open(src_path).convert("RGBA")
    w, h = img.size

    # 1. Rotate to align eye line horizontally
    # Right eye (viewer left): (273, 305)
    # Left eye (viewer right): (730, 320)
    dx = 730 - 273 # 457
    dy = 320 - 305 # 15
    angle_deg = math.degrees(math.atan2(dy, dx)) # ~1.88 degrees
    print(f"Aligning eye line: rotating {-angle_deg:.2f} degrees")

    img_rot = img.rotate(-angle_deg, resample=Image.Resampling.BICUBIC, center=((273 + 730)/2, (305 + 320)/2))

    # Recalculate aligned eye centers
    # After rotation around midpoint (501.5, 312.5):
    mid_x, mid_y = 501.5, 312.5
    half_dist = dx / 2.0 # 228.5
    eye_r_x = mid_x - half_dist # 273.0
    eye_l_x = mid_x + half_dist # 730.0
    eye_y = mid_y # 312.5

    # 2. Extract High-Res Iris Texture from Viewer Right Eye (clean hazel iris)
    iris_r = 52
    iris_crop = img_rot.crop((int(eye_l_x - iris_r), int(eye_y - iris_r), int(eye_l_x + iris_r), int(eye_y + iris_r)))
    # Resize to 512x512
    iris_512 = iris_crop.resize((512, 512), Image.Resampling.LANCZOS)
    
    # Create circular mask with soft edge for iris
    iris_mask = Image.new("L", (512, 512), 0)
    iris_draw = ImageDraw.Draw(iris_mask)
    iris_draw.ellipse([8, 8, 504, 504], fill=255)
    iris_mask = iris_mask.filter(ImageFilter.GaussianBlur(radius=6))
    
    # Create complete eyeball texture: white sclera with microvascular tint + circular iris in center
    eyeball_tex = Image.new("RGBA", (1024, 1024), (242, 238, 235, 255))
    eye_draw = ImageDraw.Draw(eyeball_tex)
    
    # Subtle sclera radial shading
    for r in range(500, 300, -5):
        alpha = int((500 - r) / 200.0 * 25)
        eye_draw.ellipse([512 - r, 512 - r, 512 + r, 512 + r], outline=(230, 205, 200, alpha), width=3)
        
    # Paste iris in center
    eyeball_tex.paste(iris_512, (512 - 256, 512 - 256), iris_mask)
    
    iris_tex_path = os.path.join(textures_dir, "eyeball_photorealistic.png")
    eyeball_tex.save(iris_tex_path, "PNG")
    print(f"Saved photorealistic eyeball texture: {iris_tex_path}")

    # 3. Prepare Face Texture Map (2048 x 2048)
    # We want eye midpoint at (1024, 980)
    # Eye distance in 3D is 0.064m
    # In camera view (40cm distance, 50mm lens, 36mm sensor):
    # Projected eye distance in 1024x1024 render is:
    # 0.064 * 1422.22 / 0.40 = 227.5 pixels!
    # In our reference photo, eye distance is 457 pixels.
    # So scale = 227.55 / 457.0 = 0.4979
    # Let's scale and center on a 2048x2048 canvas for maximum crisp detail!
    canvas_size = 2048
    scale = (canvas_size * 0.50) / dx # so eye distance is 0.50 * canvas_size
    
    scaled_w = int(w * scale)
    scaled_h = int(h * scale)
    scaled_img = img_rot.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
    
    face_canvas = Image.new("RGBA", (canvas_size, canvas_size), color=(228, 196, 180, 255))
    
    # Aligned eye centers on canvas:
    canvas_mid_x = canvas_size // 2 # 1024
    canvas_mid_y = int(canvas_size * 0.48) # 983
    
    paste_x = canvas_mid_x - int(mid_x * scale)
    paste_y = canvas_mid_y - int(mid_y * scale)
    
    face_canvas.paste(scaled_img, (paste_x, paste_y))
    
    # Mask out the eyeballs so the 3D spherical eyeballs sit behind the real eyelids
    # Left eye socket opening (viewer right)
    scaled_eye_l_x = paste_x + int(eye_l_x * scale)
    scaled_eye_l_y = paste_y + int(eye_y * scale)
    scaled_eye_r_x = paste_x + int(eye_r_x * scale)
    scaled_eye_r_y = paste_y + int(eye_y * scale)
    
    hole_rx = int(iris_r * scale * 1.05)
    hole_ry = int(iris_r * scale * 0.85)
    
    socket_mask = Image.new("L", (canvas_size, canvas_size), 255)
    mask_draw = ImageDraw.Draw(socket_mask)
    
    mask_draw.ellipse([scaled_eye_l_x - hole_rx, scaled_eye_l_y - hole_ry, scaled_eye_l_x + hole_rx, scaled_eye_l_y + hole_ry], fill=0)
    mask_draw.ellipse([scaled_eye_r_x - hole_rx, scaled_eye_r_y - hole_ry, scaled_eye_r_x + hole_rx, scaled_eye_r_y + hole_ry], fill=0)
    socket_mask = socket_mask.filter(ImageFilter.GaussianBlur(radius=5))
    
    # Save face diffuse texture
    face_tex_path = os.path.join(textures_dir, "face_studio_texture.png")
    face_canvas.save(face_tex_path, "PNG")
    print(f"Saved photorealistic face texture: {face_tex_path} ({canvas_size}x{canvas_size})")

if __name__ == "__main__":
    prepare_assets()
