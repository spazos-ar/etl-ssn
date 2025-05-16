@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Mostrar ayuda si no hay argumentos
if "%~1"=="" (
    echo Uso:
    echo   Procesar.bat datos_semanales.xlsx        - Extraer datos
    echo   Procesar.bat datos_semanales.xlsx full   - Extraer y enviar
    echo   Procesar.bat upload                      - Solo enviar JSONs existentes
    exit /b 1
)

REM Configurar rutas
set "EXTRACT_CONFIG=.\extract\config.json"
set "UPLOAD_CONFIG=.\upload\config.json"
set "PROCESSED_DIR=.\data\processed"
set "DATA_DIR=.\data"

REM Crear carpeta processed si no existe
if not exist "!PROCESSED_DIR!" mkdir "!PROCESSED_DIR!"

REM Configurar modo
set "MODO=extract"
if /i "%~1"=="upload" (
    set "MODO=upload"
    if not exist "!UPLOAD_CONFIG!" (
        echo Error: No se encuentra el archivo de configuracion !UPLOAD_CONFIG!
        exit /b 1
    )
    goto :upload
)

if /i "%~2"=="full" set "MODO=full"

REM Verificar configuraciones para modos extract y full
if not exist "!EXTRACT_CONFIG!" (
    echo Error: No se encuentra el archivo de configuracion !EXTRACT_CONFIG!
    exit /b 1
)

REM Determinar ruta del Excel eliminando .\data\ si existe en el parámetro
set "EXCEL_NAME=%~1"
set "EXCEL_NAME=!EXCEL_NAME:.\data\=!"
set "EXCEL_FILE=!DATA_DIR!\!EXCEL_NAME!"

if not exist "!EXCEL_FILE!" (
    echo Error: No se encuentra el archivo Excel !EXCEL_FILE!
    exit /b 1
)

echo Modo: !MODO!

REM Extraer datos
echo Extrayendo datos de !EXCEL_FILE!...
python extract\xls-semanal.py --config "!EXTRACT_CONFIG!" --xls-path "!EXCEL_FILE!"
if !ERRORLEVEL! neq 0 (
    echo Error en extraccion
    exit /b !ERRORLEVEL!
)

if /i "!MODO!"=="extract" (
    echo Extraccion completada
    exit /b 0
)

:upload
echo Buscando archivos JSON en !DATA_DIR!...
set "FOUND=0"
for %%f in ("!DATA_DIR!\Semana*.json") do (
    set /a "FOUND+=1"
    echo Procesando %%~nxf
    python .\upload\ssn-semanal.py --config "!UPLOAD_CONFIG!" "%%f"
    if !ERRORLEVEL! neq 0 (
        echo Error al procesar %%~nxf
        exit /b !ERRORLEVEL!
    )
    move "%%f" "!PROCESSED_DIR!\%%~nxf" >nul 2>&1
    if !ERRORLEVEL! neq 0 (
        echo Advertencia: No se pudo mover %%~nxf a !PROCESSED_DIR!
    )
)

if !FOUND!==0 (
    echo No se encontraron archivos JSON para procesar en !DATA_DIR!
    dir "!DATA_DIR!\Semana*.json" 2>nul
    exit /b 1
)

echo Proceso completado exitosamente
exit /b 0
