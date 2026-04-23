@echo off
cd /d "%~dp0"
echo Installing SecuWatch Frontend Dependencies...
echo.
call npm install
echo.
echo Installation complete! Run 'npm run dev' to start the dashboard.
pause
