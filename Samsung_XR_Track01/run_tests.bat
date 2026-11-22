@echo off
setlocal
set "BLENDER_EXE=C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"
if not exist "%BLENDER_EXE%" set "BLENDER_EXE=blender"

echo ========================================================
echo Running Full 9-Point Verification Test Suite
echo ========================================================
"%BLENDER_EXE%" --factory-startup --background scene.blend --python tests/test_eye_movement.py
pause
