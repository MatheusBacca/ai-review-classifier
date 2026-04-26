@echo off
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

if exist "%ROOT%.venv\Scripts\python.exe" (
  "%ROOT%.venv\Scripts\python.exe" -m alembic upgrade head
) else (
  python -m alembic upgrade head
)
exit /b %ERRORLEVEL%
