"""
Test new head mesh geometry with open eyelid apertures and raycast verification
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Create Head with open eye sockets
mesh = bpy.data.meshes.new("Human_Head_Mesh")
obj = bpy.data.objects.new("Human_Head", mesh)
bpy.context.collection.objects.link(obj)

bm = bmesh.new()

lat_steps = 36
lon_steps = 48
head_rx = 0.095
head_ry = 0.082
head_rz = 0.125
center_y = 0.070
center_z = 0.005

verts = []
for i in range(lat_steps + 1):
    v = i / lat_steps
    phi = (v - 0.5) * math.pi
    cos_phi = math.cos(phi)
    sin_phi = math.sin(phi)
    
    row = []
    for j in range(lon_steps):
        u = j / lon_steps
        theta = u * 2 * math.pi
        
        x = head_rx * cos_phi * math.sin(theta)
        y = center_y - head_ry * cos_phi * math.cos(theta)
        z = center_z + head_rz * sin_phi
        
        # Facial contours for front face (theta between 0 and pi, y < center_y)
        if math.cos(theta) > 0:
            # Nose
            if abs(x) < 0.020 and -0.045 <= z <= 0.015:
                t_nose = math.exp(-((x / 0.011)**2 + ((z + 0.010) / 0.022)**2))
                y -= 0.024 * t_nose
            
            # Chin
            if z < -0.06:
                t_chin = min(1.0, (-0.06 - z) / 0.06)
                x *= (1.0 - 0.40 * t_chin)
                if z < -0.08:
                    y -= 0.012 * math.sin(min(math.pi, (z + 0.08) / 0.04 * math.pi))
        
        vert = bm.verts.new((x, y, z))
        row.append(vert)
    verts.append(row)

# Create quad faces, skipping the eye socket openings
eye_w = 0.014
eye_h = 0.008

for i in range(lat_steps):
    for j in range(lon_steps):
        v1 = verts[i][j]
        v2 = verts[i][(j + 1) % lon_steps]
        v3 = verts[i + 1][(j + 1) % lon_steps]
        v4 = verts[i + 1][j]
        
        # Center of face
        fc_x = (v1.co.x + v2.co.x + v3.co.x + v4.co.x) / 4.0
        fc_y = (v1.co.y + v2.co.y + v3.co.y + v4.co.y) / 4.0
        fc_z = (v1.co.z + v2.co.z + v3.co.z + v4.co.z) / 4.0
        
        # Check if face is in eye aperture (front face, y < 0.02)
        in_aperture = False
        if fc_y < 0.02:
            for sign in [-1.0, 1.0]:
                cx = sign * 0.032
                cz = 0.000
                if ((fc_x - cx) / eye_w)**2 + ((fc_z - cz) / eye_h)**2 < 1.0:
                    in_aperture = True
                    break
        
        if not in_aperture:
            if i == 0:
                bm.faces.new((v1, v2, v3))
            elif i == lat_steps - 1:
                bm.faces.new((v1, v2, v4))
            else:
                bm.faces.new((v1, v2, v3, v4))

bm.to_mesh(mesh)
bm.free()

# 2. Add Eyeball_L and Eyeball_R
for side, sign in [('L', +1.0), ('R', -1.0)]:
    cx = sign * 0.032
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.012, location=(cx, 0, 0))
    eye_obj = bpy.context.active_object
    eye_obj.name = f"Eyeball_{side}"

# 3. Add Camera
cam_data = bpy.data.cameras.new("GazeCamera")
cam_obj = bpy.data.objects.new("GazeCamera", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_obj.location = Vector((0.0, -0.40, 0.0))
cam_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
bpy.context.scene.camera = cam_obj

bpy.context.view_layer.update()

# 4. Raycast from camera to Left and Right pupils
depsgraph = bpy.context.view_layer.depsgraph
cam_pos = cam_obj.matrix_world.translation

for side, sign in [('L', +1.0), ('R', -1.0)]:
    pupil_pos = Vector((sign * 0.032, -0.012, 0.0))
    ray_dir = (pupil_pos - cam_pos).normalized()
    ray_dist = (pupil_pos - cam_pos).length
    
    result, hit_pos, normal, index, hit_obj, matrix = bpy.context.scene.ray_cast(
        depsgraph, cam_pos, ray_dir, distance=ray_dist + 0.01
    )
    print(f"Raycast to Eye_{side}:")
    print(f"  Hit object: {hit_obj.name if result else 'None'}")
    print(f"  Hit location: {hit_pos if result else 'None'}")
    if result and hit_obj.name == f"Eyeball_{side}":
        print(f"  >>> SUCCESS: Eye_{side} is DIRECTLY VISIBLE to camera! <<<")
    else:
        print(f"  >>> FAILED: Blocked by {hit_obj.name if result else 'None'} <<<")
