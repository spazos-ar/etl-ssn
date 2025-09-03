@echo off
echo.
echo ================================================
echo   CONFIGURADOR DE AMBIENTE SSN - ETL System
echo ================================================

if "%1"=="" (
    echo Error: Debe especificar el ambiente
    echo.
    echo Uso: SetAmbiente.bat [prod^|test]
    echo.
    exit /b 1
)

echo Configurando ambiente: %1
echo.

python upload\set_env.py %1

echo.
echo ================================================
