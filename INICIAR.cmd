@echo off
cd /d "%~dp0"
set LOCAL_SQLITE=1
if not exist .venv\Scripts\python.exe (
  python -m venv .venv
  if errorlevel 1 goto error
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py migrate
if errorlevel 1 goto error
.venv\Scripts\python.exe manage.py check
if errorlevel 1 goto error
echo Iniciando servidor en modo LOCAL seguro (db.sqlite3 + private_media).
echo Abre http://127.0.0.1:8000/ en el navegador.
.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
goto end
:error
echo No se pudo iniciar. Revisa el error anterior.
:end
pause
