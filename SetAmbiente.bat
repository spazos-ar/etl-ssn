@echo off
REM Script para cambiar el ambiente de configuración SSN
REM Uso: SetAmbiente.bat prod   o   SetAmbiente.bat test

if "%~1"=="" (
    echo Uso: SetAmbiente.bat [prod^|test]
    exit /b 1
)

REM Activar entorno virtual si existe
if exist ".venv\Scripts\activate" call .venv\Scripts\activate

python upload\set_env.py %1
if %ERRORLEVEL% neq 0 exit /b %ERRORLEVEL%

echo Ambiente actualizado a %1
