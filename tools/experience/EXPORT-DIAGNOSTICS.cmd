@echo off
setlocal
"%~dp0experience-runtime\pythonw.exe" -B "%~dp0experience-runtime\normal_lifecycle.py" "%~dp0." --export
