"""
Pure Python Packager for samsung-xr-eyes SDK
Generates standard .whl (wheel) and .tar.gz (sdist) without external dependencies.
"""
import os
import zipfile
import tarfile

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sdk_dir = os.path.join(project_root, "sdk")
dist_dir = os.path.join(sdk_dir, "dist")
pkg_name = "samsung_xr_eyes"
version = "1.0.0"

os.makedirs(dist_dir, exist_ok=True)

# 1. Build .whl (Standard ZIP archive)
wheel_filename = f"{pkg_name}-{version}-py3-none-any.whl"
wheel_path = os.path.join(dist_dir, wheel_filename)

metadata_content = f"""Metadata-Version: 2.1
Name: samsung-xr-eyes
Version: {version}
Summary: Python SDK for Synthetic Eye Movement, Binocular Convergence and Virtual Camera Ground-Truth Generation
Home-page: https://github.com/samsung-xr-hackathon-2026/track01-gaze
Author: DSS Srikar / Samsung XR Hackathon Track 01
License: Apache-2.0
Requires-Python: >=3.10
Requires-Dist: numpy>=1.24.0
Requires-Dist: Pillow>=10.0.0

# Samsung XR Eyes SDK
Official SDK for Track 01: Synthetic Eye Movement and Virtual Camera.
"""

wheel_content = """Wheel-Version: 1.0
Generator: pure-python-packager
Root-Is-Purelib: true
Tag: py3-none-any
"""

record_entries = []

with zipfile.ZipFile(wheel_path, "w", zipfile.ZIP_DEFLATED) as zf:
    # Package files
    src_pkg = os.path.join(sdk_dir, "samsung_xr_eyes")
    for fname in ["__init__.py", "eyes.py"]:
        fpath = os.path.join(src_pkg, fname)
        arcname = f"{pkg_name}/{fname}"
        zf.write(fpath, arcname)
        record_entries.append(arcname)
    
    # Dist info
    dist_info = f"{pkg_name}-{version}.dist-info"
    zf.writestr(f"{dist_info}/METADATA", metadata_content)
    zf.writestr(f"{dist_info}/WHEEL", wheel_content)
    record_entries.append(f"{dist_info}/METADATA")
    record_entries.append(f"{dist_info}/WHEEL")
    
    record_content = "\n".join([f"{entry},," for entry in record_entries]) + f"\n{dist_info}/RECORD,,\n"
    zf.writestr(f"{dist_info}/RECORD", record_content)

print(f"Successfully built Wheel: {wheel_path}")

# 2. Build .tar.gz (Source Distribution)
sdist_filename = f"{pkg_name}-{version}.tar.gz"
sdist_path = os.path.join(dist_dir, sdist_filename)

with tarfile.open(sdist_path, "w:gz") as tar:
    for fname in ["setup.py", "pyproject.toml", "README.md", "XR_INTEGRATION_SPEC.md"]:
        fpath = os.path.join(sdk_dir, fname)
        if os.path.exists(fpath):
            tar.add(fpath, arcname=f"{pkg_name}-{version}/{fname}")
    
    src_pkg = os.path.join(sdk_dir, "samsung_xr_eyes")
    for fname in ["__init__.py", "eyes.py"]:
        fpath = os.path.join(src_pkg, fname)
        if os.path.exists(fpath):
            tar.add(fpath, arcname=f"{pkg_name}-{version}/{pkg_name}/{fname}")

print(f"Successfully built sdist: {sdist_path}")
