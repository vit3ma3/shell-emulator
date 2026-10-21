@echo off
REM Запуск эмулятора: run.bat --vfs examples\vfs\nested [--script scripts\stage2.sh]
cd /d "%~dp0"
python -m src.main %*
