@echo off
cd /d "%~dp0"
if not exist .venv-pruebas\Scripts\python.exe (
  python -m venv .venv-pruebas
  if errorlevel 1 goto error
)
.venv-pruebas\Scripts\python.exe -m pip install -r requirements-dev.txt
if errorlevel 1 goto error
.venv-pruebas\Scripts\python.exe verificar_proyecto.py
if errorlevel 1 goto error
echo Pruebas finalizadas correctamente.
pause
exit /b 0
:error
echo Hay errores. Revisa la salida y el informe en resultados_pruebas.
pause
exit /b 1
