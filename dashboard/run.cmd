@echo off
rem Jalankan dashboard AirGuard: run.cmd  [opsi streamlit...]
rem
rem Streamlit menulis machine-id dan email ke folder home pengguna. Di mesin ini
rem folder profil (C:\Users\Lenovo\.streamlit) tidak bisa ditulis, sehingga sesi
rem browser gagal dibuat dan halaman tampil kosong. Skrip ini mengalihkan home
rem Streamlit ke .venv\home (di dalam proyek) khusus untuk proses ini.
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\streamlit.exe" (
    echo Venv belum ada. Jalankan dulu:
    echo   python -m venv .venv
    echo   .venv\Scripts\python.exe -m pip install -r requirements.txt
    exit /b 1
)

if not exist ".venv\home" mkdir ".venv\home"
set "USERPROFILE=%~dp0.venv\home"
set "PYTHONIOENCODING=utf-8"

".venv\Scripts\streamlit.exe" run app.py %*
