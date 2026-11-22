@echo off
setlocal
cd /d "%~dp0"

echo ========================================================================
echo       Samsung XR Hackathon Track 01 - Push to GitHub
echo       Repository: https://github.com/dsssrikar/Samsung_XR_Hackathon.git
echo ========================================================================
echo.
echo Pushing all project files to main branch...
echo.

git remote set-url origin https://github.com/dsssrikar/Samsung_XR_Hackathon.git
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================================
    echo SUCCESS! All files are now live on GitHub:
    echo https://github.com/dsssrikar/Samsung_XR_Hackathon
    echo ========================================================================
) else (
    echo.
    echo ========================================================================
    echo If a browser window opened, click "Authorize git-ecosystem" to sign in.
    echo ========================================================================
)

echo.
pause
