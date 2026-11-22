"""
Samsung XR Hackathon 2026 - Track 01
Generate Ten Clockwise Gaze Renders and Ground-Truth Metadata

Formula:
  theta_k = 2 * pi * k / 10
  h = sin(theta_k)      (horizontal: right=+1, left=-1)
  v = cos(theta_k)      (vertical: up=+1, down=-1)
  for k = 0, 1, ..., 9

Frame 0 starts at top (v=1, h=0 → looking straight up)
Clockwise sequence: up → upper-right → right → lower-right → down → ...
"""

import os
import sys
import math
import json

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from wrapper.eyes import Eyes


def generate_renders_and_metadata():
    print("=" * 72)
    print("   SAMSUNG XR HACKATHON 2026: TEN CLOCKWISE GAZE RENDERS")
    print("=" * 72)

    scene_path = os.path.join(project_root, "scene.blend")
    renders_dir = os.path.join(project_root, "renders")
    metadata_path = os.path.join(project_root, "metadata.json")
    os.makedirs(renders_dir, exist_ok=True)

    # Verify scene exists
    if not os.path.exists(scene_path):
        print(f"ERROR: scene.blend not found at {scene_path}")
        print("Please run build_scene.py first!")
        sys.exit(1)

    # Initialize eye controller
    eyes = Eyes(scene_path=scene_path)

    # Get camera calibration (constant across all frames)
    camera_info = eyes.get_camera_calibration()
    camera_matrix = camera_info["intrinsic_matrix"]

    print(f"\nCamera position: {camera_info['camera_position']}")
    print(f"Intrinsic matrix: fx={camera_matrix[0][0]:.1f}, fy={camera_matrix[1][1]:.1f}")
    print(f"Principal point: cx={camera_matrix[0][2]:.1f}, cy={camera_matrix[1][2]:.1f}")
    print("-" * 72)

    # --- VERIFICATION STEP: Check pupil positions before rendering ---
    print("\n[ VERIFICATION: Checking eye rotation per frame ]")
    print(f"{'Frame':<6} {'theta':>8} {'h':>8} {'v':>8} {'Eye_L euler (deg)':>30} {'Pupil_L 2D':>20}")
    print("-" * 80)

    for k in range(10):
        theta_k = 2.0 * math.pi * k / 10
        h = math.sin(theta_k)
        v = math.cos(theta_k)
        eyes.move(h, v)
        state = eyes.get_state()
        euler_l = state["bone_euler_L"]
        pupil_l = state["pupil_2d_L"]
        print(f"  {k:02d}   {theta_k:8.4f} {h:+8.4f} {v:+8.4f}   "
              f"X={euler_l[0]:+6.2f}° Z={euler_l[2]:+6.2f}°    "
              f"({pupil_l[0]:6.1f}, {pupil_l[1]:6.1f})")

    eyes.reset()
    print("-" * 72)
    print("\n[ If all Pupil_L 2D coordinates are DIFFERENT → eye rotation is working correctly ]")
    print("[ If all coordinates are identical → animation data may still be overriding pose ]\n")

    # --- MAIN RENDERING LOOP ---
    print("\n[ RENDERING 10 FRAMES ]")
    metadata_records = []

    for k in range(10):
        theta_k = 2.0 * math.pi * k / 10
        h = math.sin(theta_k)
        v = math.cos(theta_k)

        frame_filename = f"frame_{k:02d}.png"
        frame_filepath = os.path.join(renders_dir, frame_filename)

        # Apply 3D gaze rotation
        eyes.move(h, v)

        # Verify rotation was actually applied
        state = eyes.get_state()
        euler_l = state["bone_euler_L"]

        print(f"\nFrame {k:02d}: theta={theta_k:.4f}rad, h={h:+.4f}, v={v:+.4f}")
        print(f"  Bone_L euler: X={euler_l[0]:+.2f}° Z={euler_l[2]:+.2f}°")
        print(f"  Pupil_L 2D: {state['pupil_2d_L']}")

        # Render PNG
        print(f"  Rendering {frame_filename}...")
        eyes.render(frame_filepath)

        # Get accurate ground-truth measurements
        pupil_l = eyes.get_pupil_center_2d('L')
        pupil_r = eyes.get_pupil_center_2d('R')
        rot_l = eyes.get_eye_rotation_euler('L')
        rot_r = eyes.get_eye_rotation_euler('R')

        print(f"  → Pupil L: {pupil_l}  |  Pupil R: {pupil_r}")

        record = {
            "frame": k,
            "theta": round(theta_k, 4),
            "input": {
                "h": round(h, 4),
                "v": round(v, 4)
            },
            "eye_rotation_L": rot_l,
            "eye_rotation_R": rot_r,
            "pupil_center_2D_L": list(pupil_l),
            "pupil_center_2D_R": list(pupil_r),
            "camera_matrix": camera_matrix
        }
        metadata_records.append(record)

    # Save metadata.json
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_records, f, indent=2)

    print("\n" + "=" * 72)
    print(f"DONE: metadata.json saved to {metadata_path}")
    print(f"DONE: 10 PNG renders saved to {renders_dir}/")
    print("=" * 72)

    # --- FINAL VALIDATION: Confirm unique pupil positions ---
    print("\n[ UNIQUENESS CHECK: All 10 frames should have different pupil positions ]")
    left_pupils = [r["pupil_center_2D_L"] for r in metadata_records]
    unique_pupils = len(set(str(p) for p in left_pupils))
    print(f"  Unique left pupil positions: {unique_pupils} / 10")
    if unique_pupils == 10:
        print("  ✓ PASS: All 10 frames show different eye rotations")
    elif unique_pupils > 1:
        print(f"  ~ PARTIAL: {unique_pupils} unique positions (expected 10)")
    else:
        print("  ✗ FAIL: All frames show same pupil position!")
        print("         Check: animation_data_clear() called in Eyes.__init__?")

    eyes.reset()
    return metadata_records


if __name__ == "__main__":
    generate_renders_and_metadata()
