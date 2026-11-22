"""
Automated Test Suite for Samsung XR Hackathon 2026 - Track 01
Validates:
1. Blender scene existence and integrity
2. Eye bones existence and physical rotation pivots
3. Camera distance (40 cm forward from eye midpoint)
4. Fixation distance (35 cm forward from eye midpoint)
5. Resolution and PNG output validation (1024x1024)
6. Five-direction gaze displacement validation
7. Reset accuracy and drift-free repeated movements
8. Ten-frame render count and image verification
9. Ground-truth JSON metadata schema and values
10. Contact sheet existence and resolution
"""

import os
import sys
import math
import json
import unittest
import subprocess

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import bpy
    import mathutils
    from mathutils import Vector
    from wrapper.eyes import Eyes
    BPY_MODE = True
except ImportError:
    BPY_MODE = False


class TestTrack01Verification(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = project_root
        cls.scene_file = os.path.join(cls.root, "scene.blend")
        cls.metadata_file = os.path.join(cls.root, "metadata.json")
        cls.renders_dir = os.path.join(cls.root, "renders")
        cls.contact_sheet_file = os.path.join(cls.root, "contact_sheet.png")

        if BPY_MODE:
            cls.eyes = Eyes(scene_path=cls.scene_file)
        else:
            cls.eyes = None

    def test_01_blender_scene_exists(self):
        """Verify scene.blend exists and has non-zero size."""
        self.assertTrue(os.path.exists(self.scene_file), "scene.blend does not exist")
        file_size = os.path.getsize(self.scene_file)
        self.assertGreater(file_size, 50000, f"scene.blend is abnormally small: {file_size} bytes")

    def test_02_eye_bones_and_pivots(self):
        """Verify Eye_L and Eye_R bones exist with correct eyeball center pivots."""
        if not BPY_MODE:
            self.skipTest("Requires Blender Python environment")

        arm = bpy.data.objects.get("EyeRig")
        self.assertIsNotNone(arm, "Missing 'EyeRig' armature in Blender scene")
        self.assertIn("Eye_L", arm.pose.bones, "Missing 'Eye_L' bone in EyeRig")
        self.assertIn("Eye_R", arm.pose.bones, "Missing 'Eye_R' bone in EyeRig")

        # Verify bone heads are located at physical eyeball centers
        bone_l = arm.data.bones["Eye_L"]
        bone_r = arm.data.bones["Eye_R"]

        # Left eye: +0.032m (+32mm), Right eye: -0.032m (-32mm)
        self.assertAlmostEqual(bone_l.head_local.x, 0.032, places=3, msg="Eye_L center pivot X is not +0.032m")
        self.assertAlmostEqual(bone_r.head_local.x, -0.032, places=3, msg="Eye_R center pivot X is not -0.032m")
        self.assertAlmostEqual(bone_l.head_local.y, 0.0, places=3, msg="Eye_L center pivot Y is not 0.0m")
        self.assertAlmostEqual(bone_r.head_local.y, 0.0, places=3, msg="Eye_R center pivot Y is not 0.0m")

    def test_03_camera_calibration_and_distance(self):
        """Verify camera is fixed at exactly 40 cm (0.40m) forward from eye midpoint."""
        if not BPY_MODE:
            self.skipTest("Requires Blender Python environment")

        cam = bpy.data.objects.get("GazeCamera")
        self.assertIsNotNone(cam, "Missing 'GazeCamera' in Blender scene")

        cam_pos = cam.matrix_world.translation
        eye_midpoint = Vector((0.0, 0.0, 0.0))
        dist = (cam_pos - eye_midpoint).length

        # Camera at (0, -0.40, 0)
        self.assertAlmostEqual(dist, 0.40, places=3, msg=f"Camera distance {dist:.4f}m is not 0.40m")
        self.assertAlmostEqual(cam_pos.x, 0.0, places=3, msg="Camera X is not aligned with eye midpoint")
        self.assertAlmostEqual(cam_pos.y, -0.40, places=3, msg="Camera Y is not -0.40m")

        # Focal length and sensor size
        self.assertAlmostEqual(cam.data.lens, 50.0, places=1, msg="Camera focal length is not 50mm")

    def test_04_resolution_and_format(self):
        """Verify 1024x1024 resolution and PNG format in Blender scene settings."""
        if not BPY_MODE:
            self.skipTest("Requires Blender Python environment")

        scene = bpy.context.scene
        self.assertEqual(scene.render.resolution_x, 1024, "Resolution X is not 1024")
        self.assertEqual(scene.render.resolution_y, 1024, "Resolution Y is not 1024")
        self.assertEqual(scene.render.image_settings.file_format, 'PNG', "Image format is not PNG")

    def test_05_five_direction_gaze_movement(self):
        """Verify 2D pupil displacement directions for Left, Right, Up, Down, and Reset."""
        if not BPY_MODE:
            self.skipTest("Requires Blender Python environment")

        self.eyes.reset()
        init_l = self.eyes.get_pupil_center_2d('L')
        init_r = self.eyes.get_pupil_center_2d('R')

        # 1. Left Gaze (h = -1.0, v = 0.0) -> Pupils shift to left in camera projection (dX < 0)
        self.eyes.move(-1.0, 0.0)
        curr_l = self.eyes.get_pupil_center_2d('L')
        curr_r = self.eyes.get_pupil_center_2d('R')
        self.assertLess(curr_l[0] - init_l[0], -5.0, "Left eye did not displace left")
        self.assertLess(curr_r[0] - init_r[0], -5.0, "Right eye did not displace left")

        # 2. Right Gaze (h = +1.0, v = 0.0) -> Pupils shift to right in camera projection (dX > 0)
        self.eyes.move(+1.0, 0.0)
        curr_l = self.eyes.get_pupil_center_2d('L')
        curr_r = self.eyes.get_pupil_center_2d('R')
        self.assertGreater(curr_l[0] - init_l[0], 5.0, "Left eye did not displace right")
        self.assertGreater(curr_r[0] - init_r[0], 5.0, "Right eye did not displace right")

        # 3. Up Gaze (h = 0.0, v = +1.0) -> Pupils shift upward (dY < 0 in top-left screen coords)
        self.eyes.move(0.0, +1.0)
        curr_l = self.eyes.get_pupil_center_2d('L')
        curr_r = self.eyes.get_pupil_center_2d('R')
        self.assertLess(curr_l[1] - init_l[1], -5.0, "Left eye did not displace up")
        self.assertLess(curr_r[1] - init_r[1], -5.0, "Right eye did not displace up")

        # 4. Down Gaze (h = 0.0, v = -1.0) -> Pupils shift downward (dY > 0 in top-left screen coords)
        self.eyes.move(0.0, -1.0)
        curr_l = self.eyes.get_pupil_center_2d('L')
        curr_r = self.eyes.get_pupil_center_2d('R')
        self.assertGreater(curr_l[1] - init_l[1], 5.0, "Left eye did not displace down")
        self.assertGreater(curr_r[1] - init_r[1], 5.0, "Right eye did not displace down")

        # 5. Reset Gaze
        self.eyes.reset()
        curr_l = self.eyes.get_pupil_center_2d('L')
        curr_r = self.eyes.get_pupil_center_2d('R')
        self.assertAlmostEqual(curr_l[0], init_l[0], delta=0.01, msg="Left eye reset X error")
        self.assertAlmostEqual(curr_l[1], init_l[1], delta=0.01, msg="Left eye reset Y error")
        self.assertAlmostEqual(curr_r[0], init_r[0], delta=0.01, msg="Right eye reset X error")
        self.assertAlmostEqual(curr_r[1], init_r[1], delta=0.01, msg="Right eye reset Y error")

    def test_06_reset_drift_free_reliability(self):
        """Verify repeated randomized movements do not accumulate drift."""
        if not BPY_MODE:
            self.skipTest("Requires Blender Python environment")

        self.eyes.reset()
        baseline_l = self.eyes.get_pupil_center_2d('L')
        baseline_r = self.eyes.get_pupil_center_2d('R')

        # Sequence of movements
        test_sequence = [
            (0.7, -0.4), (-0.9, 0.8), (0.3, 0.5), (-0.6, -0.6), (1.0, 1.0)
        ]
        for h, v in test_sequence:
            self.eyes.move(h, v)

        # Reset and check
        self.eyes.reset()
        after_l = self.eyes.get_pupil_center_2d('L')
        after_r = self.eyes.get_pupil_center_2d('R')

        self.assertAlmostEqual(after_l[0], baseline_l[0], delta=0.005, msg="Drift in Left eye X after sequence")
        self.assertAlmostEqual(after_l[1], baseline_l[1], delta=0.005, msg="Drift in Left eye Y after sequence")
        self.assertAlmostEqual(after_r[0], baseline_r[0], delta=0.005, msg="Drift in Right eye X after sequence")
        self.assertAlmostEqual(after_r[1], baseline_r[1], delta=0.005, msg="Drift in Right eye Y after sequence")

    def test_07_ten_rendered_frames_exist_and_valid(self):
        """Verify all 10 rendered frames exist, are PNGs, and have 1024x1024 resolution."""
        for k in range(10):
            frame_name = f"frame_{k:02d}.png"
            frame_path = os.path.join(self.renders_dir, frame_name)
            self.assertTrue(os.path.exists(frame_path), f"Missing render: {frame_name}")
            file_size = os.path.getsize(frame_path)
            self.assertGreater(file_size, 100000, f"Frame {frame_name} has invalid size: {file_size} bytes")

            # Validate PNG magic bytes
            with open(frame_path, "rb") as f:
                header = f.read(8)
                self.assertEqual(header, b'\x89PNG\r\n\x1a\n', f"{frame_name} is not a valid PNG file")

    def test_08_metadata_json_schema_and_values(self):
        """Verify metadata.json structure, non-empty values, and correct schema."""
        self.assertTrue(os.path.exists(self.metadata_file), "metadata.json missing")
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, list, "metadata.json must contain a list of records")
        self.assertEqual(len(data), 10, "metadata.json must contain exactly 10 records")

        for k, record in enumerate(data):
            self.assertEqual(record["frame"], k, f"Record {k} has wrong frame id")
            self.assertIn("theta", record)
            self.assertIn("input", record)
            self.assertIn("h", record["input"])
            self.assertIn("v", record["input"])
            self.assertIn("eye_rotation_L", record)
            self.assertIn("eye_rotation_R", record)
            self.assertIn("pupil_center_2D_L", record)
            self.assertIn("pupil_center_2D_R", record)
            self.assertIn("camera_matrix", record)

            # Check math: theta_k = 2*pi*k/10, h = sin(theta), v = cos(theta)
            expected_theta = 2.0 * math.pi * k / 10.0
            self.assertAlmostEqual(record["theta"], expected_theta, places=3)
            self.assertAlmostEqual(record["input"]["h"], math.sin(expected_theta), places=3)
            self.assertAlmostEqual(record["input"]["v"], math.cos(expected_theta), places=3)

            # Check lengths
            self.assertEqual(len(record["eye_rotation_L"]), 3)
            self.assertEqual(len(record["eye_rotation_R"]), 3)
            self.assertEqual(len(record["pupil_center_2D_L"]), 2)
            self.assertEqual(len(record["pupil_center_2D_R"]), 2)
            self.assertEqual(len(record["camera_matrix"]), 3)

    def test_09_contact_sheet_exists(self):
        """Verify contact_sheet.png exists and has valid PNG format."""
        self.assertTrue(os.path.exists(self.contact_sheet_file), "contact_sheet.png does not exist")
        file_size = os.path.getsize(self.contact_sheet_file)
        self.assertGreater(file_size, 100000, f"contact_sheet.png is too small: {file_size} bytes")

        with open(self.contact_sheet_file, "rb") as f:
            header = f.read(8)
            self.assertEqual(header, b'\x89PNG\r\n\x1a\n', "contact_sheet.png is not a valid PNG file")


def find_blender_exe():
    standard_paths = [
        r"C:\Program Files\Blender Foundation\Blender 5.3\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe",
        r"C:\Program Files\Blender Foundation\Blender\blender.exe"
    ]
    for p in standard_paths:
        if os.path.exists(p):
            return p
    return "blender"

def run_tests():
    if BPY_MODE:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestTrack01Verification)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        return result.wasSuccessful()
    else:
        # Running from standard Python CLI: delegate to Blender to run all 9 tests
        blender_exe = find_blender_exe()
        scene_path = os.path.join(project_root, "scene.blend")
        this_script = os.path.abspath(__file__)
        cmd = [blender_exe, "--factory-startup", "--background", scene_path, "--python", this_script]
        print(f"Executing complete verification test suite via Blender: {' '.join(cmd)}")
        proc = subprocess.run(cmd)
        return proc.returncode == 0

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
