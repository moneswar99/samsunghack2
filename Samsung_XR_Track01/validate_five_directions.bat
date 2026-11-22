@echo off
setlocal
set "BLENDER_EXE=C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"
if not exist "%BLENDER_EXE%" set "BLENDER_EXE=blender"

echo ========================================================
echo Running Five-Direction Gaze Validation Suite
echo ========================================================
"%BLENDER_EXE%" --factory-startup --background scene.blend --python scripts/validate_five_directions.py
pause
