"""
Five-Direction Validation Suite for Samsung XR Track 01
Validates:
1. Left gaze  (h = -1.0, v =  0.0)
2. Right gaze (h = +1.0, v =  0.0)
3. Up gaze    (h =  0.0, v = +1.0)
4. Down gaze  (h =  0.0, v = -1.0)
5. Reset      (h =  0.0, v =  0.0)

Measures actual projected 2D pupil pixel displacement.
Verifies directional correctness and zero-drift reset.
"""

import sys
import os

# Add project root to sys.path so wrapper can be imported
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from wrapper.eyes import Eyes

def run_validation():
    print("=" * 72)
    print("   SAMSUNG XR HACKATHON 2026: FIVE-DIRECTION GAZE VALIDATION")
    print("=" * 72)

    scene_path = os.path.join(project_root, "scene.blend")
    eyes = Eyes(scene_path=scene_path)

    # Establish baseline center fixation
    eyes.reset()
    init_l = eyes.get_pupil_center_2d('L')
    init_r = eyes.get_pupil_center_2d('R')

    print(f"Baseline Rest Pupil Coordinates (Top-Left Origin):")
    print(f"  Left Eye  (Eye_L): X={init_l[0]:.2f} px, Y={init_l[1]:.2f} px")
    print(f"  Right Eye (Eye_R): X={init_r[0]:.2f} px, Y={init_r[1]:.2f} px")
    print("-" * 72)

    tests = [
        {
            "name": "1. LEFT GAZE",
            "input": (-1.0, 0.0),
            "expected_desc": "Pupils displace to the left in camera projection (delta_X < 0)",
            "check": lambda dl_x, dl_y, dr_x, dr_y: dl_x < -5.0 and dr_x < -5.0 and abs(dl_y) < 1.0 and abs(dr_y) < 1.0
        },
        {
            "name": "2. RIGHT GAZE",
            "input": (+1.0, 0.0),
            "expected_desc": "Pupils displace to the right in camera projection (delta_X > 0)",
            "check": lambda dl_x, dl_y, dr_x, dr_y: dl_x > 5.0 and dr_x > 5.0 and abs(dl_y) < 1.0 and abs(dr_y) < 1.0
        },
        {
            "name": "3. UP GAZE",
            "input": (0.0, +1.0),
            "expected_desc": "Pupils displace upward in camera projection (delta_Y < 0)",
            "check": lambda dl_x, dl_y, dr_x, dr_y: dl_y < -5.0 and dr_y < -5.0 and abs(dl_x) < 1.0 and abs(dr_x) < 1.0
        },
        {
            "name": "4. DOWN GAZE",
            "input": (0.0, -1.0),
            "expected_desc": "Pupils displace downward in camera projection (delta_Y > 0)",
            "check": lambda dl_x, dl_y, dr_x, dr_y: dl_y > 5.0 and dr_y > 5.0 and abs(dl_x) < 1.0 and abs(dr_x) < 1.0
        },
        {
            "name": "5. RESET TO CENTER",
            "input": (0.0, 0.0),
            "expected_desc": "Pupils return exactly to baseline (abs(delta) < 0.01 px)",
            "check": lambda dl_x, dl_y, dr_x, dr_y: abs(dl_x) < 0.01 and abs(dr_x) < 0.01 and abs(dl_y) < 0.01 and abs(dr_y) < 0.01
        }
    ]

    results = []
    all_passed = True

    for t in tests:
        h, v = t["input"]
        if t["name"].startswith("5"):
            # Explicit reset test
            eyes.reset()
        else:
            eyes.move(h, v)

        curr_l = eyes.get_pupil_center_2d('L')
        curr_r = eyes.get_pupil_center_2d('R')

        dl_x = curr_l[0] - init_l[0]
        dl_y = curr_l[1] - init_l[1]
        dr_x = curr_r[0] - init_r[0]
        dr_y = curr_r[1] - init_r[1]

        passed = t["check"](dl_x, dl_y, dr_x, dr_y)
        if not passed:
            all_passed = False

        status = "PASS" if passed else "FAIL"

        print(f"\nTEST: {t['name']} (h={h:+.1f}, v={v:+.1f})")
        print(f"  Description : {t['expected_desc']}")
        print(f"  Left Eye    : Pos=({curr_l[0]:.2f}, {curr_l[1]:.2f}) | Displacement: dX={dl_x:+.2f} px, dY={dl_y:+.2f} px")
        print(f"  Right Eye   : Pos=({curr_r[0]:.2f}, {curr_r[1]:.2f}) | Displacement: dX={dr_x:+.2f} px, dY={dr_y:+.2f} px")
        print(f"  Result      : [{status}]")

        results.append({
            "test": t["name"],
            "input": {"h": h, "v": v},
            "status": status,
            "pupil_L": curr_l,
            "pupil_R": curr_r,
            "displacement_L": [round(dl_x, 3), round(dl_y, 3)],
            "displacement_R": [round(dr_x, 3), round(dr_y, 3)]
        })

    print("\n" + "=" * 72)
    print(f"OVERALL FIVE-DIRECTION VALIDATION: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    print("=" * 72)

    return all_passed

if __name__ == "__main__":
    success = run_validation()
    if not success:
        sys.exit(1)
