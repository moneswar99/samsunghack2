"""
Samsung XR Hackathon 2026 - Track 01
Synthetic Eye Movement & Virtual Camera Rendering
Eye Movement Automation API: wrapper/eyes.py

Reusable Eyes controller class interfacing with Blender API (bpy).
Features:
- True 3D eyeball rotation around physical centers (NOT 2D translation)
- Realistic binocular convergence on a 35 cm fixation plane
- Clamped normalized gaze inputs h, v in [-1.0, 1.0]
- Zero-drift deterministic reset()
- Fixed calibrated camera rendering (1024x1024 PNG)
- Accurate projected 2D pupil centers and 3D world rotations

COORDINATE SYSTEM:
  - Eye midpoint at world origin (0, 0, 0)
  - Forward direction: -Y axis (camera at Y=-0.40m)
  - Left eye at X=+0.032m, Right eye at X=-0.032m
  - Up direction: +Z axis

ROTATION APPROACH:
  - Use Euler XYZ rotations on the pose bones directly
  - Pitch (up/down) = rotation around X axis
  - Yaw (left/right) = rotation around Z axis
  - This avoids pose-space vs armature-space matrix conversion issues
"""

import os
import math
import typing

try:
    import bpy
    import mathutils
    from mathutils import Vector, Matrix, Quaternion, Euler
    from bpy_extras.object_utils import world_to_camera_view
    BPY_AVAILABLE = True
except ImportError:
    BPY_AVAILABLE = False


class Eyes:
    """
    Controller for realistic 3D eye movement and virtual camera rendering in Blender.
    
    Usage:
        eyes = Eyes(scene_path="path/to/scene.blend")
        eyes.move(h=0.5, v=0.3)   # Look right and up
        eyes.render("output.png")
        eyes.reset()               # Return to center
    """

    def __init__(self, scene_path: typing.Optional[str] = None):
        """
        Initialize the Eyes controller.
        
        Args:
            scene_path: Path to the .blend file. If provided, loads it.
        """
        if not BPY_AVAILABLE:
            raise RuntimeError(
                "Blender Python API (bpy) is not available. "
                "Run via: blender --background scene.blend --python script.py"
            )

        # Load the blend file if provided
        if scene_path and os.path.exists(scene_path):
            bpy.ops.wm.open_mainfile(filepath=scene_path)
            print(f"[Eyes] Loaded scene: {scene_path}")

        self.scene = bpy.context.scene

        # Locate required objects
        self.armature = bpy.data.objects.get("EyeRig")
        self.eyeball_l = bpy.data.objects.get("Eyeball_L")
        self.eyeball_r = bpy.data.objects.get("Eyeball_R")
        self.camera = bpy.data.objects.get("GazeCamera")

        if not self.armature:
            raise ValueError("Scene missing required object 'EyeRig'")
        if not self.eyeball_l:
            raise ValueError("Scene missing required object 'Eyeball_L'")
        if not self.eyeball_r:
            raise ValueError("Scene missing required object 'Eyeball_R'")
        if not self.camera:
            raise ValueError("Scene missing required object 'GazeCamera'")

        # Verify pose bones exist
        pose_bones = self.armature.pose.bones
        if "Eye_L" not in pose_bones or "Eye_R" not in pose_bones:
            raise ValueError("Armature 'EyeRig' must have bones 'Eye_L' and 'Eye_R'")

        self.bone_l = pose_bones["Eye_L"]
        self.bone_r = pose_bones["Eye_R"]

        # Set rotation mode to Euler XYZ for predictable direct control
        self.bone_l.rotation_mode = 'XYZ'
        self.bone_r.rotation_mode = 'XYZ'

        # CRITICAL: Clear any animation data that would override our rotations
        # Animation keyframes in the scene.blend can lock the pose bones
        if self.armature.animation_data:
            self.armature.animation_data_clear()
            print("[Eyes] Cleared animation data - programmatic control enabled")

        # Physical parameters (all in meters)
        # Interpupillary distance = 64mm (0.064m), so each eye is 32mm from center
        self.center_l = Vector((+0.032, 0.0, 0.0))   # Left eye center
        self.center_r = Vector((-0.032, 0.0, 0.0))   # Right eye center
        self.eye_midpoint = Vector((0.0, 0.0, 0.0))

        # Samsung XR Track 01 Specifications
        self.fixation_distance = 0.35   # 35 cm fixation plane
        self.camera_distance = 0.40     # 40 cm camera distance

        # Human eye voluntary movement range (comfortable range)
        self.max_yaw_deg = 25.0    # Horizontal: ±25 degrees
        self.max_pitch_deg = 20.0  # Vertical: ±20 degrees

        # Find anterior pupil vertex (the one at -Y extreme = front of eyeball)
        self.pupil_idx_l = self._find_pupil_vertex(self.eyeball_l)
        self.pupil_idx_r = self._find_pupil_vertex(self.eyeball_r)

        # State tracking
        self.current_h = 0.0
        self.current_v = 0.0

        # Reset to center gaze on initialization
        self.reset()
        print("[Eyes] Initialized. Eyes centered at fixation target (0, -0.35, 0)")

    def _find_pupil_vertex(self, eye_obj) -> int:
        """
        Find the vertex index closest to the anterior pole (front of eyeball).
        The eyeball's local -Y direction = forward = toward camera.
        """
        # Check if previously computed and stored
        stored_idx = eye_obj.get("pupil_vert_idx", None)
        if stored_idx is not None:
            return int(stored_idx)

        # Find vertex closest to anterior pole (0, -radius, 0) in local space
        # Radius = 0.012m (12mm eyeball radius)
        radius = 0.012
        anterior_pole = Vector((0.0, -radius, 0.0))

        best_idx = 0
        min_dist = float("inf")
        for v in eye_obj.data.vertices:
            dist = (v.co - anterior_pole).length
            if dist < min_dist:
                min_dist = dist
                best_idx = v.index

        eye_obj["pupil_vert_idx"] = best_idx
        print(f"[Eyes] Pupil vertex for {eye_obj.name}: index {best_idx}")
        return best_idx

    def move(self, h: float, v: float):
        """
        Rotate both eyeballs to look at a 3D fixation target.
        
        Uses true 3D eyeball rotation (NOT 2D pupil translation).
        Both eyes converge binocularly toward the fixation point.
        
        Args:
            h (float): Horizontal gaze input [-1.0, +1.0]
                       +1.0 = look right (subject's right, screen left)
                       -1.0 = look left (subject's left, screen right)
            v (float): Vertical gaze input [-1.0, +1.0]
                       +1.0 = look up
                       -1.0 = look down
        """
        # Type validation
        try:
            h = float(h)
            v = float(v)
        except (ValueError, TypeError) as e:
            raise ValueError(f"h and v must be numbers. Got h={h}, v={v}") from e

        # Clamp to valid range
        h = max(-1.0, min(1.0, h))
        v = max(-1.0, min(1.0, v))

        self.current_h = h
        self.current_v = v

        # Calculate the 3D fixation target position
        # h and v map to angles within our comfortable gaze range
        yaw_deg = h * self.max_yaw_deg    # Horizontal angle
        pitch_deg = v * self.max_pitch_deg  # Vertical angle

        # Convert to target position on the fixation plane (Z=-0.35m)
        # tan(angle) gives the displacement at unit distance
        d = self.fixation_distance  # 0.35 m
        target_x = d * math.tan(math.radians(yaw_deg))
        target_z = d * math.tan(math.radians(pitch_deg))
        target_y = -d  # -0.35m (forward = -Y direction)

        fixation_target = Vector((target_x, target_y, target_z))
        self.current_fixation_target = fixation_target

        # Apply eye rotations using Euler angles on pose bones
        # This is the most reliable approach for Blender's armature system
        self._rotate_eye_to_target(self.bone_l, self.center_l, fixation_target)
        self._rotate_eye_to_target(self.bone_r, self.center_r, fixation_target)

        # Force depsgraph to update so vertex positions are recalculated
        bpy.context.view_layer.update()

        print(f"[Eyes] move(h={h:+.3f}, v={v:+.3f}) → target=({target_x:+.4f}, {target_y:+.4f}, {target_z:+.4f})")

    def _rotate_eye_to_target(self, pose_bone, eye_center: Vector, target: Vector):
        """
        Compute the Euler XYZ rotation needed for the eye bone to look at target.
        
        The bone's rest pose points along -Y (forward).
        We calculate:
          - pitch (X rotation): up/down angle 
          - yaw (Z rotation): left/right angle
        
        Args:
            pose_bone: The Blender pose bone to rotate
            eye_center: World position of the eye center (pivot point)
            target: World position of the fixation target
        """
        # Direction vector from eye center to target (in world space)
        gaze_dir = (target - eye_center).normalized()

        # --- Convert world gaze direction to bone local Euler angles ---
        # Bone rest pose: Y axis = forward (-Y world = forward gaze)
        # We need to find the rotation FROM the rest direction (0, -1, 0) TO gaze_dir

        # Yaw (Z-axis rotation) = left/right
        # = angle between forward vector projected onto XY plane
        yaw_rad = math.atan2(gaze_dir.x, -gaze_dir.y)

        # Pitch (X-axis rotation) = up/down
        # = angle between forward vector and horizontal plane
        pitch_rad = math.asin(max(-1.0, min(1.0, gaze_dir.z)))

        # Apply directly to pose bone Euler rotation
        # Bone rest pose is along -Y, so:
        # pitch (X rot) moves up/down
        # yaw (Z rot) moves left/right
        pose_bone.rotation_euler[0] = -pitch_rad   # Negative: +v means look up = negative X rot
        pose_bone.rotation_euler[1] = 0.0           # Roll: keep zero (Listing's law)
        pose_bone.rotation_euler[2] = -yaw_rad      # Negative: +h means right = negative Z rot

    def reset(self):
        """
        Reset both eyes to center gaze (looking straight forward at fixation target).
        Uses move(0, 0) for exact, error-free reset.
        """
        self.bone_l.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')
        self.bone_r.rotation_euler = Euler((0.0, 0.0, 0.0), 'XYZ')
        self.current_h = 0.0
        self.current_v = 0.0
        self.current_fixation_target = Vector((0.0, -self.fixation_distance, 0.0))
        bpy.context.view_layer.update()
        print("[Eyes] reset() → both eyes centered")

    def render(self, filepath: typing.Optional[str] = None) -> str:
        """
        Render the current gaze pose from the fixed virtual camera.
        
        Args:
            filepath: Output PNG path. Defaults to renders/render_output.png
            
        Returns:
            Absolute path of the rendered PNG.
        """
        if filepath is None:
            filepath = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "renders",
                "render_output.png"
            )

        # Ensure output directory exists
        out_dir = os.path.dirname(filepath)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        # Set render parameters
        self.scene.camera = self.camera
        self.scene.render.resolution_x = 1024
        self.scene.render.resolution_y = 1024
        self.scene.render.image_settings.file_format = 'PNG'
        self.scene.render.image_settings.color_mode = 'RGB'
        self.scene.render.filepath = filepath

        # Update scene before rendering
        bpy.context.view_layer.update()

        # Render
        bpy.ops.render.render(write_still=True)
        print(f"[Eyes] Rendered → {filepath}")
        return filepath

    def get_pupil_center_2d(self, side: str) -> typing.Tuple[float, float]:
        """
        Get the actual 2D pixel coordinate of the pupil center in the rendered image.
        
        Uses Blender's world_to_camera_view() for accurate projection.
        Coordinate convention: origin at top-left, X right, Y down (standard image coords).
        
        Args:
            side: 'L' for left eye, 'R' for right eye
            
        Returns:
            (px, py): Pixel coordinates in [0, 1024] range
        """
        side = side.upper()
        if side == 'L':
            obj = self.eyeball_l
            idx = self.pupil_idx_l
        elif side == 'R':
            obj = self.eyeball_r
            idx = self.pupil_idx_r
        else:
            raise ValueError(f"side must be 'L' or 'R', got '{side}'")

        # Get the evaluated (post-modifier, post-armature) mesh
        depsgraph = bpy.context.view_layer.depsgraph
        eval_obj = obj.evaluated_get(depsgraph)
        eval_mesh = eval_obj.data

        # Get 3D world position of the pupil vertex
        pupil_world = obj.matrix_world @ eval_mesh.vertices[idx].co

        # Project to camera viewport (normalized device coordinates)
        coords_ndc = world_to_camera_view(self.scene, self.camera, pupil_world)

        # Convert NDC [0,1] to pixel coordinates [0, 1024]
        res_x = self.scene.render.resolution_x
        res_y = self.scene.render.resolution_y
        px = coords_ndc.x * res_x
        py = (1.0 - coords_ndc.y) * res_y   # Flip Y: Blender Y=0 is bottom, image Y=0 is top

        return (round(px, 3), round(py, 3))

    def get_eye_rotation_euler(self, side: str) -> typing.List[float]:
        """
        Get the actual 3D world rotation of the eye bone as Euler angles in degrees.
        
        Args:
            side: 'L' or 'R'
            
        Returns:
            [rx, ry, rz] in degrees
        """
        side = side.upper()
        bone = self.bone_l if side == 'L' else self.bone_r

        # Get the bone's pose matrix in armature space and convert to world via armature matrix
        bone_world_mat = self.armature.matrix_world @ bone.matrix
        euler = bone_world_mat.to_euler('XYZ')

        return [
            round(math.degrees(euler.x), 4),
            round(math.degrees(euler.y), 4),
            round(math.degrees(euler.z), 4)
        ]

    def get_camera_calibration(self) -> typing.Dict[str, typing.Any]:
        """
        Return the camera's intrinsic matrix K and extrinsic matrix.
        
        K = [[fx,  0, cx],
             [ 0, fy, cy],
             [ 0,  0,  1]]
        
        Returns:
            Dict with intrinsic_matrix, extrinsic_matrix, focal_length_mm, etc.
        """
        cam_data = self.camera.data
        res_x = self.scene.render.resolution_x
        res_y = self.scene.render.resolution_y
        sensor_w = cam_data.sensor_width
        sensor_h = cam_data.sensor_height
        focal_mm = cam_data.lens

        # Focal length in pixels
        fx = focal_mm * (res_x / sensor_w)
        fy = focal_mm * (res_y / sensor_h)
        cx = res_x / 2.0
        cy = res_y / 2.0

        intrinsic_matrix = [
            [round(fx, 4), 0.0, round(cx, 4)],
            [0.0, round(fy, 4), round(cy, 4)],
            [0.0, 0.0, 1.0]
        ]

        # Extrinsic = world-to-camera = inverse of camera's world matrix
        w2c = self.camera.matrix_world.inverted()
        extrinsic_matrix = [[round(val, 6) for val in row] for row in w2c]

        return {
            "intrinsic_matrix": intrinsic_matrix,
            "extrinsic_matrix": extrinsic_matrix,
            "focal_length_mm": focal_mm,
            "sensor_size_mm": [sensor_w, sensor_h],
            "resolution": [res_x, res_y],
            "camera_position": [round(v, 4) for v in self.camera.matrix_world.translation]
        }

    def get_state(self) -> typing.Dict:
        """
        Return current gaze state for debugging.
        """
        pupil_l = self.get_pupil_center_2d('L')
        pupil_r = self.get_pupil_center_2d('R')
        rot_l = self.get_eye_rotation_euler('L')
        rot_r = self.get_eye_rotation_euler('R')
        return {
            "h": self.current_h,
            "v": self.current_v,
            "bone_euler_L": [round(math.degrees(a), 3) for a in self.bone_l.rotation_euler],
            "bone_euler_R": [round(math.degrees(a), 3) for a in self.bone_r.rotation_euler],
            "pupil_2d_L": pupil_l,
            "pupil_2d_R": pupil_r,
            "world_euler_L": rot_l,
            "world_euler_R": rot_r,
        }
