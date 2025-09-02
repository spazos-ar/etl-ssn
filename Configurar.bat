@echo off
REM Script para configurar el proyecto ETL SSN y activar el entorno virtual
REM Uso: ConfigurarProyecto.bat

python setup.py
if %ERRORLEVEL% neq 0 (
    echo Error en la configuración. Revisá los mensajes anteriores.
    exit /b %ERRORLEVEL%
)

REM Activar entorno virtual
if exist ".venv\Scripts\activate" call .venv\Scripts\activate

echo Configuración completada y entorno virtual activado.
echo Ahora podés ejecutar los comandos del sistema ETL SSN.
