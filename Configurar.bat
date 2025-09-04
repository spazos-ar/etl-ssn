@echo off
REM Script para configurar el proyecto ETL SSN y activar el entorno virtual
REM Uso: Configurar.bat

echo.
echo ================================================
echo   CONFIGURACION INICIAL - ETL SSN System
echo ================================================
echo.

python setup.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Error en la configuracion. Revise los mensajes anteriores.
    exit /b %ERRORLEVEL%
)

echo.
echo ================================================
echo   CONFIGURACION COMPLETADA EXITOSAMENTE
echo ================================================
echo.
echo Proximos pasos:
echo.
echo 1 🏃 Activar entorno virtual:
echo      .venv\Scripts\activate
echo.
echo 2 🏃 Configurar ambiente de trabajo:
echo      SetAmbiente.bat prod   (para produccion)
echo      SetAmbiente.bat test   (para pruebas)
echo.
echo 3 🏃 Procesar datos:
echo      ProcesarMes.bat        (datos mensuales)
echo      ProcesarSem.bat        (datos semanales)
echo.
echo NOTA: Por defecto se configura el ambiente de PRODUCCION
echo      Use SetAmbiente.bat para cambiar entre ambientes
echo.
echo ================================================
