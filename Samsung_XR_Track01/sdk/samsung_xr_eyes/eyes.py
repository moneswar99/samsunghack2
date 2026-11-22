"""
Samsung XR Hackathon 2026 - Track 01
Synthetic Eye Movement & Virtual Camera Rendering
Eye Movement Automation API: wrapper/eyes.py

Reusable Eyes controller class interfacing with Blender API (bpy).
Features:
- Programmatic 3D eyeball rotation around physical centers
- Realistic binocular convergence on a 35 cm fixation plane
- Clamped normalized gaze inputs h, v in [-1.0, 1.0]
- Zero-drift deterministic reset()
- Fixed calibrated camera rendering (1024x1024 PNG)
- Accurate projected 2D pupil centers and 3D world rotations
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
    """

    def __init__(self, scene_path: typing.Optional[str] = None):
        """
        Initialize the Eyes controller.
        If scene_path is provided and bpy is active, loads the specified .blend file.
        """
        if not BPY_AVAILABLE:
            raise RuntimeError(
                "Blender Python API (bpy) is not available in the current Python environment. "
                "Run this module via Blender's Python: blender -b scene.blend --python <script>.py"
            )

        if scene_path and os.path.exists(scene_path):
            bpy.ops.wm.open_mainfile(filepath=scene_path)

        self.scene = bpy.context.scene

        # Locate key objects in the scene
        self.armature = self._find_object("EyeRig")
        self.eyeball_l = self._find_object("Eyeball_L")
        self.eyeball_r = self._find_object("Eyeball_R")
        self.camera = self._find_object("GazeCamera")

        if not self.armature:
            raise ValueError("Scene missing required Armature object 'EyeRig'")
        if not self.camera:
            raise ValueError("Scene missing required Camera object 'GazeCamera'")

        # Ensure pose bones exist
        if "Eye_L" not in self.armature.pose.bones or "Eye_R" not in self.armature.pose.bones:
            raise ValueError("Armature 'EyeRig' must contain 'Eye_L' and 'Eye_R' pose bones")

        self.bone_l = self.armature.pose.bones["Eye_L"]
        self.bone_r = self.armature.pose.bones["Eye_R"]

        # Eyeball centers in world coordinates (meters)
        # Interpupillary distance (IPD) = 64 mm (0.064 m)
        self.center_l = Vector((+0.032, 0.0, 0.0))
        self.center_r = Vector((-0.032, 0.0, 0.0))
        self.eye_midpoint = Vector((0.0, 0.0, 0.0))

        # Specifications (Track 01):
        # Fixation target: 35 cm forward along -Y axis
        # Camera distance: 40 cm forward along -Y axis
        self.fixation_distance = 0.35  # meters (35 cm)
        self.camera_distance = 0.40    # meters (40 cm)

        # Maximum human voluntary ocular motor range (without head rotation)
        # Horizontal (yaw): +/- 25 degrees (~0.4363 rad)
        # Vertical (pitch): +/- 20 degrees (~0.3491 rad)
        self.max_yaw_rad = math.radians(25.0)
        self.max_pitch_rad = math.radians(20.0)

        # Baseline resting gaze vector (pointing forward along -Y)
        self.rest_dir = Vector((0.0, -1.0, 0.0))

        # Anterior pupil vertex indices for exact geometric tracking
        self.pupil_idx_l = self.eyeball_l.get("pupil_vert_idx", None)
        self.pupil_idx_r = self.eyeball_r.get("pupil_vert_idx", None)

        if self.pupil_idx_l is None:
            self.pupil_idx_l = self._find_anterior_pole_vert(self.eyeball_l)
        if self.pupil_idx_r is None:
            self.pupil_idx_r = self._find_anterior_pole_vert(self.eyeball_r)

        # Current state
        self.current_h = 0.0
        self.current_v = 0.0

        # Enforce initial reset to calibrated 35cm fixation
        self.reset()

    def _find_object(self, name: str):
        return bpy.data.objects.get(name, None)

    def _find_anterior_pole_vert(self, eye_obj) -> int:
        """Find the index of the vertex closest to the anterior pole (0, -0.012, 0)."""
        radius = 0.012
        target_pole = Vector((0.0, -radius, 0.0))
        best_idx = 0
        min_dist = float("inf")
        for v in eye_obj.data.vertices:
            dist = (v.co - target_pole).length
            if dist < min_dist:
                min_dist = dist
                best_idx = v.index
        eye_obj["pupil_vert_idx"] = best_idx
        return best_idx

    def move(self, h: float, v: float):
        """
        Rotate both eyeballs programmatically around their physical centers.
        
        Args:
            h (float): Normalized horizontal gaze input [-1.0, +1.0].
                       h > 0: gaze shifts right (subject's +X).
                       h < 0: gaze shifts left (subject's -X).
            v (float): Normalized vertical gaze input [-1.0, +1.0].
                       v > 0: gaze shifts up (+Z).
                       v < 0: gaze shifts down (-Z).
        
        Preserves realistic binocular convergence toward the 35 cm fixation target plane.
        """
        # Type and validity checking
        try:
            h = float(h)
            v = float(v)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Gaze inputs h and v must be numeric. Received h={h}, v={v}") from e

        # Clamp inputs to supported [-1.0, +1.0] range
        h_clamped = max(-1.0, min(1.0, h))
        v_clamped = max(-1.0, min(1.0, v))

        self.current_h = h_clamped
        self.current_v = v_clamped

        # Calculate fixation target in 3D world space
        # Fixation plane is at Y = -fixation_distance (-0.35 m)
        d = self.fixation_distance
        target_x = d * math.tan(h_clamped * self.max_yaw_rad)
        target_z = d * math.tan(v_clamped * self.max_pitch_rad)
        target_y = -d

        fixation_target = Vector((target_x, target_y, target_z))
        self.current_fixation_target = fixation_target

        # Update rotation for Left and Right eyes
        self._aim_eye(self.bone_l, self.center_l, fixation_target)
        self._aim_eye(self.bone_r, self.center_r, fixation_target)

        # Synchronize Blender's dependency graph
        bpy.context.view_layer.update()

    def _aim_eye(self, pose_bone, eye_center: Vector, target: Vector):
        """
        Compute and apply the exact 3D orientation for an eye bone
        so that it points directly at the target from its physical center.
        """
        # Direction vector from eyeball center to fixation target
        gaze_dir = (target - eye_center).normalized()

        # Bone orientation in armature space (rig is at world origin):
        # Y axis points along gaze direction
        y_axis = gaze_dir

        # Listing's law / Donders' law constraint:
        # Keep eye vertical Z axis perpendicular to gaze_dir, aligned with world +Z
        world_up = Vector((0.0, 0.0, 1.0))
        z_axis = (world_up - (world_up.dot(y_axis)) * y_axis).normalized()
        x_axis = y_axis.cross(z_axis).normalized()

        # Build 4x4 orientation matrix with pivot at eye_center
        rot_mat = Matrix([
            [x_axis.x, y_axis.x, z_axis.x, 0.0],
            [x_axis.y, y_axis.y, z_axis.y, 0.0],
            [x_axis.z, y_axis.z, z_axis.z, 0.0],
            [0.0,      0.0,      0.0,      1.0]
        ])
        rot_mat.translation = eye_center

        pose_bone.matrix = rot_mat

    def reset(self):
        """
        Reset both eyes to the baseline converged center fixation target (h=0, v=0).
        Restores initial rotations exactly with zero accumulated error.
        """
        self.move(0.0, 0.0)

    def render(self, filepath: typing.Optional[str] = None) -> str:
        """
        Render the current scene from the fixed virtual camera to a 1024x1024 PNG file.
        
        Args:
            filepath (str, optional): Target output path. If None, saves to default renders/frame.png.
        
        Returns:
            str: Absolute path of the rendered PNG file.
        """
        if filepath is None:
            filepath = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "renders",
                "render_output.png"
            )

        # Ensure parent directory exists
        out_dir = os.path.dirname(filepath)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        # Verify fixed camera parameters
        self.scene.camera = self.camera
        self.scene.render.resolution_x = 1024
        self.scene.render.resolution_y = 1024
        self.scene.render.image_settings.file_format = 'PNG'
        self.scene.render.image_settings.color_mode = 'RGB'
        self.scene.render.filepath = filepath

        # Render frame
        bpy.ops.render.render(write_still=True)
        return filepath

    def get_pupil_center_2d(self, side: str) -> typing.Tuple[float, float]:
        """
        Calculate actual projected 2D pupil center in pixel coordinates.
        Uses universal Computer Vision convention (origin at Top-Left: X right [0, 1024], Y down [0, 1024]).
        """
        side_upper = side.upper()
        if side_upper == 'L':
            obj = self.eyeball_l
            idx = self.pupil_idx_l
        elif side_upper == 'R':
            obj = self.eyeball_r
            idx = self.pupil_idx_r
        else:
            raise ValueError(f"Unknown eye side '{side}'. Must be 'L' or 'R'")

        depsgraph = bpy.context.view_layer.depsgraph
        eval_obj = obj.evaluated_get(depsgraph)
        eval_mesh = eval_obj.data

        # 3D world coordinate of the pupil landmark vertex
        pupil_world = obj.matrix_world @ eval_mesh.vertices[idx].co

        # Project 3D point to camera viewport
        coords_ndc = world_to_camera_view(self.scene, self.camera, pupil_world)

        res_x = self.scene.render.resolution_x
        res_y = self.scene.render.resolution_y

        # Convert normalized device coordinates [0, 1] to pixel coordinates (top-left origin)
        px = coords_ndc.x * res_x
        py = (1.0 - coords_ndc.y) * res_y

        return (round(px, 3), round(py, 3))

    def get_eye_rotation_euler(self, side: str) -> typing.List[float]:
        """
        Return actual 3D world rotation of the eye bone in Euler angles (degrees).
        """
        side_upper = side.upper()
        bone = self.bone_l if side_upper == 'L' else self.bone_r
        euler = bone.matrix.to_euler('XYZ')
        return [
            round(math.degrees(euler.x), 4),
            round(math.degrees(euler.y), 4),
            round(math.degrees(euler.z), 4)
        ]

    def get_camera_calibration(self) -> typing.Dict[str, typing.Any]:
        """
        Return the exact 3x3 camera intrinsic matrix K and 4x4 camera extrinsic matrix.
        """
        cam_data = self.camera.data
        res_x = self.scene.render.resolution_x
        res_y = self.scene.render.resolution_y
        sensor_w = cam_data.sensor_width
        sensor_h = cam_data.sensor_height
        focal_mm = cam_data.lens

        # Focal lengths in pixels
        fx = focal_mm * (res_x / sensor_w)
        fy = focal_mm * (res_y / sensor_h)

        # Principal point (optical center)
        cx = res_x / 2.0
        cy = res_y / 2.0

        intrinsic_matrix = [
            [round(fx, 4), 0.0,          round(cx, 4)],
            [0.0,          round(fy, 4), round(cy, 4)],
            [0.0,          0.0,          1.0]
        ]

        # Extrinsic matrix: world-to-camera transformation matrix [R | t]
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
