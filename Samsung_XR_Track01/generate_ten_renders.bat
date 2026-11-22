@echo off
setlocal
set "BLENDER_EXE=C:\Program Files\Blender Foundation\Blender 5.3\blender.exe"
if not exist "%BLENDER_EXE%" set "BLENDER_EXE=blender"

echo ========================================================
echo Generating Ten Clockwise Gaze Renders and Metadata
echo ========================================================
"%BLENDER_EXE%" --factory-startup --background scene.blend --python scripts/generate_ten_renders.py
pause
