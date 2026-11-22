"""
Build Scene Script for Samsung XR Hackathon Track 01
Fixes:
- Anatomically aligned head geometry with open eyelid apertures
- Direct, unobstructed optical line-of-sight from virtual camera to Eyeball_L and Eyeball_R
- Realistic hazel iris, limbal ring, pupil, and glossy cornea with softbox catchlights
- 10-position animation keyframes embedded in scene.blend for live playback (Spacebar)
- Viewport opens directly in Camera View with Material Shading
"""

import os
import bpy
import bmesh
import math
import mathutils
from mathutils import Vector, Matrix, Quaternion

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def create_head_mesh():
    mesh = bpy.data.meshes.new("Human_Head_Mesh")
    obj = bpy.data.objects.new("Human_Head", mesh)
    bpy.context.collection.objects.link(obj)
    
    bm = bmesh.new()
    
    lat_steps = 36
    lon_steps = 48
    head_rx = 0.095  # width radius (9.5 cm)
    head_ry = 0.082  # depth radius (8.2 cm)
    head_rz = 0.125  # height radius (12.5 cm)
    center_y = 0.070 # skull center placed so facial surface aligns with eyeball plane at y ~ 0
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
            
            # Sculpt facial features for front face (cos(theta) > 0, y < center_y)
            if math.cos(theta) > 0:
                # Nose bridge, dorsum and tip
                if abs(x) < 0.020 and -0.045 <= z <= 0.015:
                    t_nose = math.exp(-((x / 0.011)**2 + ((z + 0.010) / 0.022)**2))
                    y -= 0.024 * t_nose
                
                # Chin tapering and projection
                if z < -0.06:
                    t_chin = min(1.0, (-0.06 - z) / 0.06)
                    x *= (1.0 - 0.40 * t_chin)
                    if z < -0.08:
                        y -= 0.012 * math.sin(min(math.pi, (z + 0.08) / 0.04 * math.pi))
                
                # Cheeks smoothing
                if -0.04 <= z <= 0.01 and abs(x) > 0.025:
                    y -= 0.004
            
            vert = bm.verts.new((x, y, z))
            row.append(vert)
        verts.append(row)
    
    # Create quad faces with OPEN eye socket apertures
    # Eyelid opening dimensions (meters)
    eye_w = 0.015  # 15mm half-width
    eye_h = 0.009  # 9mm half-height
    
    for i in range(lat_steps):
        for j in range(lon_steps):
            v1 = verts[i][j]
            v2 = verts[i][(j + 1) % lon_steps]
            v3 = verts[i + 1][(j + 1) % lon_steps]
            v4 = verts[i + 1][j]
            
            fc_x = (v1.co.x + v2.co.x + v3.co.x + v4.co.x) / 4.0
            fc_y = (v1.co.y + v2.co.y + v3.co.y + v4.co.y) / 4.0
            fc_z = (v1.co.z + v2.co.z + v3.co.z + v4.co.z) / 4.0
            
            # Check if this face is in the eye socket opening
            in_aperture = False
            if fc_y < 0.025:
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
    
    # UV mapping aligned to studio photograph
    uv_layer = bm.loops.layers.uv.verify()
    for face in bm.faces:
        for loop in face.loops:
            v_co = loop.vert.co
            u = 0.50 - (v_co.x / 0.165)
            w = 0.48 + (v_co.z / 0.180)
            u = max(0.001, min(0.999, u))
            w = max(0.001, min(0.999, w))
            loop[uv_layer].uv = (u, w)
    
    bm.to_mesh(mesh)
    bm.free()
    
    for poly in mesh.polygons:
        poly.use_smooth = True
    
    subsurf = obj.modifiers.new("Subsurf", type='SUBSURF')
    subsurf.levels = 2
    subsurf.render_levels = 2
    
    # Skin material
    mat = bpy.data.materials.new(name="Skin_Material")
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_out = nodes.new(type="ShaderNodeOutputMaterial")
    node_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    
    face_tex_path = os.path.join(project_root, "textures", "face_studio_texture.png")
    if os.path.exists(face_tex_path):
        img = bpy.data.images.load(face_tex_path)
        node_tex = nodes.new(type="ShaderNodeTexImage")
        node_tex.image = img
        links.new(node_tex.outputs["Color"], node_bsdf.inputs["Base Color"])
    else:
        node_bsdf.inputs["Base Color"].default_value = (0.85, 0.65, 0.55, 1.0)
    
    node_bsdf.inputs["Roughness"].default_value = 0.38
    if "Subsurface Weight" in node_bsdf.inputs:
        node_bsdf.inputs["Subsurface Weight"].default_value = 0.20
        node_bsdf.inputs["Subsurface Radius"].default_value = (0.03, 0.015, 0.008)
    elif "Subsurface" in node_bsdf.inputs:
        node_bsdf.inputs["Subsurface"].default_value = 0.20
    
    links.new(node_bsdf.outputs["BSDF"], node_out.inputs["Surface"])
    mesh.materials.append(mat)
    
    return obj

def create_eyeball(name, center_x, arm_obj, bone_name):
    radius = 0.012
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=64,
        ring_count=32,
        radius=radius,
        location=(center_x, 0.0, 0.0)
    )
    obj = bpy.context.active_object
    obj.name = name
    
    for poly in obj.data.polygons:
        poly.use_smooth = True
        
    vg = obj.vertex_groups.new(name=bone_name)
    vg.add([v.index for v in obj.data.vertices], 1.0, 'REPLACE')
    
    mod = obj.modifiers.new("Armature", type='ARMATURE')
    mod.object = arm_obj
    
    pupil_vert_idx = None
    min_dist = 999.0
    for v in obj.data.vertices:
        d = (v.co - Vector((0.0, -radius, 0.0))).length
        if d < min_dist:
            min_dist = d
            pupil_vert_idx = v.index
    obj["pupil_vert_idx"] = pupil_vert_idx
    
    # High-Definition Hazel Iris and Glossy Cornea Shader
    mat = bpy.data.materials.new(name=f"Eye_Material_{name}")
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    node_out = nodes.new(type="ShaderNodeOutputMaterial")
    node_bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    
    node_tex_coord = nodes.new(type="ShaderNodeTexCoord")
    node_sep = nodes.new(type="ShaderNodeSeparateXYZ")
    links.new(node_tex_coord.outputs["Object"], node_sep.inputs["Vector"])
    
    # Calculate radial distance in XZ plane: sqrt(x^2 + z^2)
    node_x2 = nodes.new(type="ShaderNodeMath")
    node_x2.operation = 'MULTIPLY'
    links.new(node_sep.outputs["X"], node_x2.inputs[0])
    links.new(node_sep.outputs["X"], node_x2.inputs[1])
    
    node_z2 = nodes.new(type="ShaderNodeMath")
    node_z2.operation = 'MULTIPLY'
    links.new(node_sep.outputs["Z"], node_z2.inputs[0])
    links.new(node_sep.outputs["Z"], node_z2.inputs[1])
    
    node_add = nodes.new(type="ShaderNodeMath")
    node_add.operation = 'ADD'
    links.new(node_x2.outputs["Value"], node_add.inputs[0])
    links.new(node_z2.outputs["Value"], node_add.inputs[1])
    
    node_sqrt = nodes.new(type="ShaderNodeMath")
    node_sqrt.operation = 'SQRT'
    links.new(node_add.outputs["Value"], node_sqrt.inputs[0])
    
    # Normalize by radius (0.012)
    node_norm = nodes.new(type="ShaderNodeMath")
    node_norm.operation = 'DIVIDE'
    links.new(node_sqrt.outputs["Value"], node_norm.inputs[0])
    node_norm.inputs[1].default_value = radius
    
    # Realistic Hazel Iris Color Ramp
    node_ramp = nodes.new(type="ShaderNodeValToRGB")
    ramp = node_ramp.color_ramp
    ramp.color_mode = 'RGB'
    ramp.interpolation = 'LINEAR'
    
    ramp.elements[0].position = 0.0
    ramp.elements[0].color = (0.003, 0.003, 0.003, 1.0) # Pupil black
    
    e1 = ramp.elements.new(0.18)
    e1.color = (0.003, 0.003, 0.003, 1.0) # Pupil boundary
    
    e2 = ramp.elements.new(0.19)
    e2.color = (0.35, 0.22, 0.08, 1.0) # Hazel amber inner ring
    
    e3 = ramp.elements.new(0.32)
    e3.color = (0.28, 0.30, 0.14, 1.0) # Hazel green/amber mid-iris
    
    e4 = ramp.elements.new(0.43)
    e4.color = (0.16, 0.18, 0.09, 1.0) # Limbal ring start
    
    e5 = ramp.elements.new(0.48)
    e5.color = (0.02, 0.03, 0.02, 1.0) # Dark limbal ring edge
    
    e6 = ramp.elements.new(0.52)
    e6.color = (0.95, 0.93, 0.91, 1.0) # Sclera white
    
    ramp.elements[1].position = 1.0
    ramp.elements[1].color = (0.90, 0.88, 0.86, 1.0) # Sclera posterior
    
    links.new(node_norm.outputs["Value"], node_ramp.inputs["Fac"])
    links.new(node_ramp.outputs["Color"], node_bsdf.inputs["Base Color"])
    
    # Glossy cornea surface for sharp studio catchlights
    node_bsdf.inputs["Roughness"].default_value = 0.015
    node_bsdf.inputs["IOR"].default_value = 1.376
    
    links.new(node_bsdf.outputs["BSDF"], node_out.inputs["Surface"])
    obj.data.materials.append(mat)
    
    return obj

def create_rig():
    arm_data = bpy.data.armatures.new("EyeRig_Data")
    arm_obj = bpy.data.objects.new("EyeRig", arm_data)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    bone_head = arm_data.edit_bones.new("Head")
    bone_head.head = Vector((0.0, 0.0, -0.15))
    bone_head.tail = Vector((0.0, 0.0, 0.15))
    
    bone_l = arm_data.edit_bones.new("Eye_L")
    bone_l.head = Vector((+0.032, 0.0, 0.0))
    bone_l.tail = Vector((+0.032, -0.05, 0.0))
    bone_l.parent = bone_head
    
    bone_r = arm_data.edit_bones.new("Eye_R")
    bone_r.head = Vector((-0.032, 0.0, 0.0))
    bone_r.tail = Vector((-0.032, -0.05, 0.0))
    bone_r.parent = bone_head
    
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

def setup_camera_and_lighting():
    # Camera fixed at distance 40 cm (0.40 m) from eye midpoint (0, 0, 0)
    cam_data = bpy.data.cameras.new("GazeCamera")
    cam_data.lens = 50.0
    cam_data.sensor_width = 36.0
    cam_data.sensor_height = 36.0
    cam_data.clip_start = 0.05
    cam_data.clip_end = 10.0
    
    cam_obj = bpy.data.objects.new("GazeCamera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    
    cam_obj.location = Vector((0.0, -0.40, 0.0))
    cam_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    bpy.context.scene.camera = cam_obj
    
    scene = bpy.context.scene
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    
    # 3-Point Studio Softbox Lighting
    key_light_data = bpy.data.lights.new(name="Key_Light", type='AREA')
    key_light_data.energy = 60.0
    key_light_data.size = 0.35
    key_light_data.color = (1.0, 0.98, 0.96)
    key_light_obj = bpy.data.objects.new("Key_Light", key_light_data)
    key_light_obj.location = Vector((0.25, -0.55, 0.25))
    key_light_obj.rotation_euler = (math.radians(45), math.radians(15), math.radians(25))
    bpy.context.collection.objects.link(key_light_obj)
    
    fill_light_data = bpy.data.lights.new(name="Fill_Light", type='AREA')
    fill_light_data.energy = 42.0
    fill_light_data.size = 0.40
    fill_light_data.color = (0.96, 0.98, 1.0)
    fill_light_obj = bpy.data.objects.new("Fill_Light", fill_light_data)
    fill_light_obj.location = Vector((-0.25, -0.50, 0.20))
    fill_light_obj.rotation_euler = (math.radians(45), math.radians(-15), math.radians(-25))
    bpy.context.collection.objects.link(fill_light_obj)
    
    rim_light_data = bpy.data.lights.new(name="Rim_Light", type='SPOT')
    rim_light_data.energy = 45.0
    rim_light_data.spot_size = math.radians(65)
    rim_light_obj = bpy.data.objects.new("Rim_Light", rim_light_data)
    rim_light_obj.location = Vector((0.0, 0.35, 0.40))
    rim_light_obj.rotation_euler = (math.radians(-45), 0.0, 0.0)
    bpy.context.collection.objects.link(rim_light_obj)
    
    world = bpy.data.worlds.new("Studio_World")
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs["Color"].default_value = (0.92, 0.93, 0.95, 1.0)
        bg_node.inputs["Strength"].default_value = 0.8
    bpy.context.scene.world = world

def add_animation_keyframes(arm_obj):
    """
    Keyframe the 10 clockwise gaze movements across frames 1 to 100
    so that pressing Spacebar in Blender plays the eye movement animation in the camera view!
    """
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 100
    scene.render.fps = 24

    bone_l = arm_obj.pose.bones["Eye_L"]
    bone_r = arm_obj.pose.bones["Eye_R"]
    bone_l.rotation_mode = 'XYZ'
    bone_r.rotation_mode = 'XYZ'

    num_samples = 10
    frames_per_sample = 10

    max_yaw = math.radians(25.0)
    max_pitch = math.radians(20.0)

    for k in range(num_samples):
        theta = 2.0 * math.pi * k / num_samples
        h = math.sin(theta)
        v = math.cos(theta)

        # Fixation target at 35cm
        tx = 0.35 * math.tan(h * max_yaw)
        tz = 0.35 * math.tan(v * max_pitch)
        target = Vector((tx, -0.35, tz))

        # Aim bones
        for bone, cx in [(bone_l, +0.032), (bone_r, -0.032)]:
            eye_center = Vector((cx, 0.0, 0.0))
            gaze_dir = (target - eye_center).normalized()
            
            y_axis = gaze_dir
            world_up = Vector((0.0, 0.0, 1.0))
            z_axis = (world_up - (world_up.dot(y_axis)) * y_axis).normalized()
            x_axis = y_axis.cross(z_axis).normalized()
            
            rot_mat = Matrix([
                [x_axis.x, y_axis.x, z_axis.x, 0.0],
                [x_axis.y, y_axis.y, z_axis.y, 0.0],
                [x_axis.z, y_axis.z, z_axis.z, 0.0],
                [0.0,      0.0,      0.0,      1.0]
            ])
            rot_mat.translation = eye_center
            bone.matrix = rot_mat

            frame_num = k * frames_per_sample + 1
            bone.keyframe_insert(data_path="rotation_euler", frame=frame_num)

    # Loop back to frame 1 at frame 101
    scene.frame_set(1)

def configure_viewport_shading():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
                        space.region_3d.view_perspective = 'CAMERA'

def main():
    print("Building Photorealistic Samsung XR Track 01 scene with visible eye movement...")
    clear_scene()
    
    arm_obj = create_rig()
    head_obj = create_head_mesh()
    eye_l = create_eyeball("Eyeball_L", +0.032, arm_obj, "Eye_L")
    eye_r = create_eyeball("Eyeball_R", -0.032, arm_obj, "Eye_R")
    
    setup_camera_and_lighting()
    add_animation_keyframes(arm_obj)
    configure_viewport_shading()
    
    blend_path = os.path.join(project_root, "scene.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Scene successfully created with visible eye movements: {blend_path}")

if __name__ == "__main__":
    main()
