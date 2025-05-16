# ETL SSN

Sistema de extracción y carga de datos para la Superintendencia de Seguros de la Nación (SSN). Este proyecto automatiza el proceso de carga de información semanal requerida por la SSN, facilitando el cumplimiento de las obligaciones regulatorias de las compañías aseguradoras.

## Descripción

El sistema consta de dos componentes principales:

1. **Extracción de datos**: Procesa los archivos Excel semanales ubicados en la carpeta `data/` y los prepara según el formato requerido por la SSN.
2. **Carga de datos**: Realiza la carga automática de la información procesada al sistema de la SSN utilizando las credenciales configuradas.

### Estructura del proyecto

- `data/`: Directorio para los archivos de datos semanales
  - `datos_semanales.xlsx`: Archivo de entrada con los datos a procesar
  - `processed/`: Carpeta donde se almacenan los archivos procesados
- `extract/`: Módulo de extracción y procesamiento de datos
  - `xls-semanal.py`: Script para el procesamiento de archivos Excel
  - `config.json`: Configuración del proceso de extracción
- `upload/`: Módulo de carga de datos
  - `ssn-semanal.py`: Script para la carga automática al sistema SSN
  - `config.json`: Configuración del proceso de carga

## Configuración inicial

1. Instala las dependencias del proyecto:
```powershell
pip install -r requirements.txt
```

2. Configura las credenciales:
   - Copia el archivo `.env.example` y renómbralo a `.env`
   - Edita el archivo `.env` y completa tus credenciales:
     ```
     SSN_USER=tu_usuario
     SSN_PASSWORD=tu_contraseña
     SSN_COMPANY=tu_codigo_compania
     ```

## Uso

### Proceso de carga semanal

1. Coloca el archivo Excel con los datos semanales en la carpeta `data/` con el nombre `datos_semanales.xlsx`

2. El script `Procesar.bat` tiene las siguientes opciones de uso:

```powershell
# Solo extraer datos del Excel
.\Procesar.bat datos_semanales.xlsx

# Extraer datos y enviarlos a la SSN
.\Procesar.bat datos_semanales.xlsx full

# Solo enviar JSONs existentes en data/
.\Procesar.bat upload
```

El script realizará automáticamente según la opción elegida:
- Validación del formato de los datos de entrada
- Procesamiento del Excel según los requerimientos de la SSN
- Generación de archivos JSON en la carpeta `data/`
- Carga de la información al sistema SSN utilizando las credenciales configuradas
- Movimiento de los archivos procesados a la carpeta `data/processed/`

### Uso de scripts Python individuales

Si necesitas ejecutar los scripts de Python de manera individual, puedes hacerlo de la siguiente manera:

#### Script Python de extracción (`extract/xls-semanal.py`)

Este script procesa los archivos Excel y genera los JSONs necesarios para la carga:

```powershell
# Procesar un archivo Excel específico
python extract/xls-semanal.py data/datos_semanales.xlsx

# Especificar una carpeta de salida diferente (por defecto es data/)
python extract/xls-semanal.py data/datos_semanales.xlsx --output carpeta_salida/
```

#### Script Python de carga (`upload/ssn-semanal.py`)

Este script maneja la carga de los JSONs al sistema de la SSN:

```powershell
# Cargar todos los JSONs de la carpeta data/
python upload/ssn-semanal.py

# Cargar JSONs desde una carpeta específica
python upload/ssn-semanal.py --input carpeta_entrada/

# Modo debug (muestra más información durante la ejecución)
python upload/ssn-semanal.py --debug
```

Ambos scripts utilizan la configuración de sus respectivos archivos `config.json` y las credenciales del archivo `.env`.

### Archivos de configuración

- `extract/config.json`: Permite configurar los parámetros de extracción y procesamiento
- `upload/config.json`: Configura los parámetros de conexión y carga al sistema SSN

### Documentación adicional

En la carpeta `docs/` encontrarás:
- Especificaciones técnicas del formato requerido por la SSN
- Ejemplos de archivos de datos para pruebas

## Soporte

Para reportar problemas o solicitar mejoras, por favor crear un issue en el repositorio.
