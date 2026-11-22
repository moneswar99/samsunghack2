"""
Create Complete Samsung XR Track 01 Submission ZIP Bundle
"""
import os
import zipfile

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out_zip = os.path.join(os.path.dirname(project_root), "Samsung_XR_Track01_Submission_Bundle.zip")

include_dirs = ["wrapper", "renders", "tests", "scripts", "dashboard", "presentation", "video", "sdk", "textures"]
include_files = ["scene.blend", "metadata.json", "contact_sheet.png", "README.md", "AI_DISCLOSURE.md", "requirements.txt", "run_dashboard.bat", "run_tests.bat", "validate_five_directions.bat", "generate_ten_renders.bat", "create_contact_sheet.bat"]

print(f"Creating submission zip: {out_zip} ...")
with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
    # Add top-level files
    for fname in include_files:
        fpath = os.path.join(project_root, fname)
        if os.path.exists(fpath):
            arcname = f"Samsung_XR_Track01/{fname}"
            zf.write(fpath, arcname)
            print(f"  Added file: {arcname} ({os.path.getsize(fpath)} bytes)")

    # Add directories
    for dname in include_dirs:
        dpath = os.path.join(project_root, dname)
        if not os.path.exists(dpath):
            continue
        for root, dirs, files in os.walk(dpath):
            if "__pycache__" in root or "anim_frames" in root:
                continue
            for file in files:
                fpath = os.path.join(root, file)
                rel_path = os.path.relpath(fpath, project_root)
                arcname = f"Samsung_XR_Track01/{rel_path}"
                zf.write(fpath, arcname)

print("=" * 72)
print(f"SUCCESS: Submission bundle created at {out_zip} ({os.path.getsize(out_zip)} bytes)")
print("=" * 72)
