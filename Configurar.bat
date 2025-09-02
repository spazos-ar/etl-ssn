@echo off
REM Script para configurar el proyecto ETL SSN y activar el entorno virtual
REM Uso: ConfigurarProyecto.bat

python setup.py
if %ERRORLEVEL% neq 0 (
    echo Error en la configuración. Revisá los mensajes anteriores.
    exit /b %ERRORLEVEL%
)

REM Activar entorno virtual
REM Para activar el entorno virtual, ejecutá manualmente en la terminal:
echo Configuración completada!
echo Para activar el entorno virtual, ejecutá:
echo .........................................
echo .      .venv\Scripts\activate           .
echo .........................................
echo Activá el entorno virtual antes de ejecutar los comandos del sistema ETL SSN.
