"""
Quick debug script: verify eye bone rotations change per frame WITHOUT rendering.
Runs in ~30 seconds vs ~10 minutes for full render.
"""
import os, sys, math

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from wrapper.eyes import Eyes

scene_path = os.path.join(project_root, "scene.blend")
eyes = Eyes(scene_path=scene_path)

print("\n=== EYE ROTATION VERIFICATION (no renders) ===")
print(f"{'k':>3} | {'h':>7} | {'v':>7} | {'Bone_L X':>10} | {'Bone_L Z':>10} | {'Pupil_L':>18} | {'Pupil_R':>18}")
print("-" * 90)

all_ok = True
prev_pupil = None

for k in range(10):
    theta = 2.0 * math.pi * k / 10
    h = math.sin(theta)
    v = math.cos(theta)
    
    eyes.move(h, v)
    
    bx = math.degrees(eyes.bone_l.rotation_euler[0])
    bz = math.degrees(eyes.bone_l.rotation_euler[2])
    pl = eyes.get_pupil_center_2d('L')
    pr = eyes.get_pupil_center_2d('R')
    
    changed = "✓" if prev_pupil is None or pl != prev_pupil else "✗ SAME!"
    if prev_pupil is not None and pl == prev_pupil:
        all_ok = False
    
    print(f"{k:>3} | {h:>+7.3f} | {v:>+7.3f} | {bx:>+10.3f} | {bz:>+10.3f} | {str(pl):>18} | {str(pr):>18}  {changed}")
    prev_pupil = pl

print("-" * 90)
print("RESULT:", "✓ ALL ROTATIONS UNIQUE - Eye movement working!" if all_ok else "✗ ROTATION BUG DETECTED")
eyes.reset()
