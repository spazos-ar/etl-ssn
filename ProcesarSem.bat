@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Mostrar ayuda si no hay argumentos
if "%~1"=="" (
    echo Uso:
    echo   ProcesarSem.bat datos_semanales.xlsx         - Extraer datos
    echo   ProcesarSem.bat datos_semanales.xlsx full    - Extraer y enviar con confirmacion
    echo   ProcesarSem.bat upload                       - Solo enviar JSONs existentes
    echo   ProcesarSem.bat query YYYY-WW                - Consultar estado de una semana
    echo   ProcesarSem.bat fix YYYY-WW                  - Corregir datos de una semana
    exit /b 1
)

REM Configurar rutas
set "EXTRACT_CONFIG=.\extract\config-semanal.json"
set "UPLOAD_CONFIG=.\upload\config-semanal.json"
set "PROCESSED_DIR=.\data\processed\weekly"
set "DATA_DIR=.\data"

REM Crear carpeta processed\weekly si no existe
if not exist "!PROCESSED_DIR!" mkdir "!PROCESSED_DIR!"

REM Procesar comando query
if "%~1"=="query" (
    if "%~2"=="" (
        echo Error: Debe especificar la semana en formato YYYY-WW
        echo Ejemplo: ProcesarSem.bat query 2025-15
        exit /b 1
    )
    python .\upload\ssn-semanal.py --query-week %2
    exit /b !ERRORLEVEL!
)

REM Procesar comando fix
if "%~1"=="fix" (
    if "%~2"=="" (
        echo Error: Debe especificar la semana en formato YYYY-WW
        echo Ejemplo: ProcesarSem.bat fix 2025-15
        exit /b 1
    )
    python .\upload\ssn-semanal.py --fix-week %2
    exit /b !ERRORLEVEL!
)

REM Manejar caso de solo envio
if "%~1"=="upload" (
    if "%~2"=="" (
        echo Error: Debe especificar la semana en formato YYYY-WW
        echo Ejemplo: ProcesarSem.bat upload 2025-15
        exit /b 1
    )
    set "JSON_FILE=!DATA_DIR!\Semana%~2.json"
    if not exist "!JSON_FILE!" (
        echo Error: No se encuentra el archivo !JSON_FILE!
        exit /b 1
    )
    echo Procesando !JSON_FILE!...
    python .\upload\ssn-semanal.py --confirm-week "!JSON_FILE!"
    if !ERRORLEVEL! neq 0 (
        echo Error al procesar !JSON_FILE!
        exit /b !ERRORLEVEL!
    )
    echo El archivo fue procesado exitosamente
    exit /b 0
}

REM Procesar archivo Excel
set "EXCEL_FILE=%~1"
if not exist "!EXCEL_FILE!" (
    set "EXCEL_FILE=!DATA_DIR!\%~1"
)

if exist "!EXCEL_FILE!" (
    echo Extrayendo datos de !EXCEL_FILE!...
    python .\extract\xls-semanal.py --config "!EXTRACT_CONFIG!" --xls-path "!EXCEL_FILE!"
    if !ERRORLEVEL! neq 0 (
        echo Error al extraer datos
        exit /b !ERRORLEVEL!
    )
    
    REM Si se especifica 'full', enviar y confirmar
    if /i "%~2"=="full" (
        echo Enviando datos a SSN...
        for %%f in ("!DATA_DIR!\Semana*.json") do (
            echo Procesando %%~nxf...
            python .\upload\ssn-semanal.py --confirm-week "%%f"
            if !ERRORLEVEL! neq 0 (
                echo Error al procesar %%~nxf
                exit /b !ERRORLEVEL!
            )
        )
        echo Procesamiento completo
    ) else (
        echo Extraccion completa. Use 'ProcesarSem.bat upload' para enviar los datos
    )
) else (
    echo Error: No se encuentra el archivo %1
    exit /b 1
)
