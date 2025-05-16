# ETL SSN

Sistema de extracción y carga de datos para la Superintendencia de Seguros de la Nación (SSN). Este proyecto automatiza el proceso de carga de información semanal requerido por la SSN, facilitando el cumplimiento de las obligaciones regulatorias de las compañías de seguros.

## Descripción

El sistema tiene dos componentes principales:

1. **Extracción de datos**: Procesa los archivos Excel semanales ubicados en la carpeta `data/` y los prepara según el formato requerido por la SSN.
2. **Carga de datos**: Sube automáticamente la información procesada al sistema de la SSN usando las credenciales configuradas.

### Estructura del proyecto

- `data/`: Directorio para los archivos de datos semanales
  - `datos_semanales.xlsx`: Archivo de entrada con los datos a procesar
  - `processed/`: Carpeta donde quedan guardados los archivos ya procesados
- `extract/`: Módulo de extracción y procesamiento de datos
  - `xls-semanal.py`: Script para procesar los archivos Excel
  - `config.json`: Configuración del proceso de extracción
- `upload/`: Módulo de carga de datos
  - `ssn-semanal.py`: Script para la carga automática al sistema SSN
  - `config.json`: Configuración del proceso de carga

## Instalación

Para una guía detallada de instalación en Windows 10/11, incluyendo la instalación de Git, Python y la configuración del entorno, consultá [docs/INSTALACION.md](docs/INSTALACION.md).

## Configuración inicial

Una vez instalados los prerequisitos:

1. Instalá las dependencias del proyecto:
```powershell
pip install -r requirements.txt
```

2. Configurá las credenciales:
   - Copiá el archivo `.env.example` y cambiále el nombre a `.env`
   - Editá el archivo `.env` y completá tus credenciales:
     ```
     SSN_USER=tu_usuario
     SSN_PASSWORD=tu_contraseña
     SSN_COMPANY=tu_codigo_compania
     ```

## Uso

### Proceso de carga semanal

1. Poné el archivo Excel con los datos semanales en la carpeta `data/` con el nombre `datos_semanales.xlsx`

2. El script `Procesar.bat` tiene estas opciones de uso:

```powershell
# Extraer datos del Excel
.\Procesar.bat datos_semanales.xlsx

# Extraer datos y enviarlos automáticamente a la SSN con confirmación
.\Procesar.bat datos_semanales.xlsx full

# Enviar y confirmar los JSONs que ya están en data/
.\Procesar.bat upload

# Consultar el estado de una semana específica
.\Procesar.bat query 2025-15

# Pedir rectificativa de una semana específica
.\Procesar.bat fix 2025-15
```

El script va a hacer automáticamente según la opción que elijas:
- Validar el formato de los datos de entrada
- Procesar el Excel según lo que pide la SSN
- Generar los archivos JSON en la carpeta `data/`
- Cargar la información al sistema SSN usando tus credenciales
- Mover los archivos procesados a la carpeta `data/processed/`

### Uso de scripts Python por separado

Si necesitás ejecutar los scripts de Python por separado, podés hacerlo así:

#### Script de extracción (`extract/xls-semanal.py`)

Este script procesa los archivos Excel y genera los JSONs necesarios para la carga:

```powershell
# Procesar un archivo Excel (ruta requerida)
python extract/xls-semanal.py --xls-path data/datos_semanales.xlsx

# Especificar un archivo de configuración alternativo
python extract/xls-semanal.py --config otra-config.json --xls-path data/datos_semanales.xlsx
```

Los argumentos disponibles son:
- `--xls-path`: Ruta al archivo Excel a procesar (requerido)
- `--config`: Ruta al archivo de configuración (opcional, por defecto usa `extract/config.json`)

#### Script de carga (`upload/ssn-semanal.py`)

Este script se encarga de subir y gestionar los datos en el sistema de la SSN:

```powershell
# Cargar un archivo JSON de datos - sin confirmacion
python upload/ssn-semanal.py data/Semana15.json

# Cargar y confirmar un archivo JSON de datos
python upload/ssn-semanal.py --confirm-week data/Semana15.json

# Consultar el estado de una semana específica
python upload/ssn-semanal.py --query-week 2025-15

# Pedir Rectificativa de una semana específica
python upload/ssn-semanal.py --fix-week 2025-15

# Especificar un archivo de configuración alternativo
python upload/ssn-semanal.py --config otra-config.json data/Semana15.json
```

Los argumentos disponibles son:
- `--config`: Ruta al archivo de configuración (opcional, por defecto usa `upload/config.json`)
- `--confirm-week`: Confirma la entrega semanal y mueve el archivo a processed/
- `--fix-week YYYY-WW`: Pide rectificativa de una semana específica
- `--query-week YYYY-WW`: Consulta el estado de una semana específica

Los dos scripts usan la configuración de sus respectivos archivos `config.json` y las credenciales del archivo `.env`. Las credenciales requeridas son:
- `SSN_USER`: Usuario para autenticación
- `SSN_PASSWORD`: Contraseña del usuario
- `SSN_COMPANY`: Código de la compañía

### Archivos de configuración

- `extract/config.json`: Te permite configurar los parámetros de extracción y procesamiento
- `upload/config.json`: Configurá los parámetros de conexión y carga al sistema SSN

### Documentación adicional

En la carpeta `docs/` vas a encontrar:
- Especificaciones técnicas del formato requerido por la SSN
- Ejemplos de archivos de datos para hacer pruebas
- Guía de instalación detallada para Windows 10/11

## Soporte

Si encontrás algún problema o querés sugerir mejoras, creá un issue en el repositorio.
