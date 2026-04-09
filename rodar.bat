@echo off
cd /d "%~dp0"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
python -B -m streamlit run EMS_UI.py --server.fileWatcherType poll
pause
