@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM Mostrar ayuda si no hay argumentos
if "%~1"=="" (
    echo Uso:
    echo   ProcesarMes.bat datos_mensuales.xlsx         - Extraer datos
    echo   ProcesarMes.bat datos_mensuales.xlsx full    - Extraer y enviar con confirmacion
    echo   ProcesarMes.bat upload                       - Solo enviar JSONs existentes
    echo   ProcesarMes.bat query YYYY-MM                - Consultar estado de un mes
    echo   ProcesarMes.bat fix YYYY-MM                  - Corregir datos de un mes
    exit /b 1
)

REM Configurar rutas
set "EXTRACT_CONFIG=.\extract\config-mensual.json"
set "UPLOAD_CONFIG=.\upload\config-mensual.json"
set "PROCESSED_DIR=.\data\processed\monthly"
set "DATA_DIR=.\data"

REM Crear carpeta processed\monthly si no existe
if not exist "!PROCESSED_DIR!" mkdir "!PROCESSED_DIR!"

REM Procesar comando query
if "%~1"=="query" (
    if "%~2"=="" (
        echo Error: Debe especificar el mes en formato YYYY-MM
        echo Ejemplo: ProcesarMes.bat query 2025-05
        exit /b 1
    )
    python .\upload\ssn-mensual.py --query-month %2
    exit /b !ERRORLEVEL!
)

REM Procesar comando fix
if "%~1"=="fix" (
    if "%~2"=="" (
        echo Error: Debe especificar el mes en formato YYYY-MM
        echo Ejemplo: ProcesarMes.bat fix 2025-05
        exit /b 1
    )
    python .\upload\ssn-mensual.py --fix-month %2
    exit /b !ERRORLEVEL!
)

REM Manejar caso de solo envio
if "%~1"=="upload" (
    for %%f in ("!DATA_DIR!\Mes-*.json") do (
        echo Procesando %%~nxf...
        python .\upload\ssn-mensual.py --confirm-month "%%f"
        if !ERRORLEVEL! neq 0 (
            echo Error al procesar %%~nxf
            exit /b !ERRORLEVEL!
        )
    )
    echo Todos los archivos fueron procesados exitosamente
    exit /b 0
)

REM Procesar archivo Excel
set "EXCEL_FILE=%~1"
if not exist "!EXCEL_FILE!" (
    set "EXCEL_FILE=!DATA_DIR!\%~1"
)

if exist "!EXCEL_FILE!" (
    echo Extrayendo datos de !EXCEL_FILE!...
    python .\extract\xls-mensual.py --config "!EXTRACT_CONFIG!" --xls-path "!EXCEL_FILE!"
    if !ERRORLEVEL! neq 0 (
        echo Error al extraer datos
        exit /b !ERRORLEVEL!
    )
    
    REM Si se especifica 'full', enviar y confirmar
    if /i "%~2"=="full" (
        echo Enviando datos a SSN...
        for %%f in ("!DATA_DIR!\Mes-*.json") do (
            echo Procesando %%~nxf...
            python .\upload\ssn-mensual.py --confirm-month "%%f"
            if !ERRORLEVEL! neq 0 (
                echo Error al procesar %%~nxf
                exit /b !ERRORLEVEL!
            )
        )
        echo Procesamiento completo
    ) else (
        echo Extraccion completa. Use 'ProcesarMes.bat upload' para enviar los datos
    )
) else (
    echo Error: No se encuentra el archivo %1
    exit /b 1
)
