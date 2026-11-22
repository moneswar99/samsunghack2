"""
Inspect visibility of eyeballs through the camera in scene.blend
"""
import bpy
import bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

scene_path = r"c:\Users\mones\OneDrive\Desktop\samsang\Samsung_XR_Track01\scene.blend"
bpy.ops.wm.open_mainfile(filepath=scene_path)

scene = bpy.context.scene
cam = bpy.data.objects["GazeCamera"]
eye_l = bpy.data.objects["Eyeball_L"]
head = bpy.data.objects["Human_Head"]

print("Camera location:", cam.matrix_world.translation)
print("Eyeball_L location:", eye_l.matrix_world.translation)

# Raycast from camera to Left Eye center
# Camera is at (0, -0.40, 0). Left eye center is at (+0.032, 0, 0).
cam_pos = cam.matrix_world.translation
eye_target = Vector((0.032, -0.012, 0.0))
ray_dir = (eye_target - cam_pos).normalized()
ray_dist = (eye_target - cam_pos).length

depsgraph = bpy.context.view_layer.depsgraph
result, location, normal, index, hit_obj, matrix = scene.ray_cast(depsgraph, cam_pos, ray_dir, distance=ray_dist)

print(f"Raycast from camera towards Left Pupil:")
print(f"  Hit something? {result}")
if result:
    print(f"  Hit object: {hit_obj.name}")
    print(f"  Hit location: {location}")
    print(f"  Distance from camera: {(location - cam_pos).length:.4f} m (Pupil is at {ray_dist:.4f} m)")
    if hit_obj.name == "Human_Head":
        print("  WARNING: Human_Head is BLOCKING the eyeball!")
    elif hit_obj.name == "Eyeball_L":
        print("  SUCCESS: Eyeball_L is directly visible to the camera!")
