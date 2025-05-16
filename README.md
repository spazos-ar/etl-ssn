# ETL SSN

Sistema de extracción y carga de datos para la Superintendencia de Seguros de la Nación (SSN). Este proyecto automatiza el proceso de carga de información semanal que pide la SSN, facilitando el cumplimiento de las obligaciones regulatorias de las compañías de seguros.

## Descripción

El sistema tiene dos componentes principales:

1. **Extracción de datos**: Procesa los archivos Excel semanales que están en la carpeta `data/` y los prepara según el formato que pide la SSN.
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

## Configuración inicial

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
# Solo extraer datos del Excel
.\Procesar.bat datos_semanales.xlsx

# Extraer datos y mandarlos a la SSN
.\Procesar.bat datos_semanales.xlsx full

# Solo mandar los JSONs que ya están en data/
.\Procesar.bat upload
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
# Procesar un archivo Excel específico
python extract/xls-semanal.py data/datos_semanales.xlsx

# Elegir una carpeta de salida diferente (por defecto es data/)
python extract/xls-semanal.py data/datos_semanales.xlsx --output carpeta_salida/
```

#### Script de carga (`upload/ssn-semanal.py`)

Este script se encarga de subir los JSONs al sistema de la SSN:

```powershell
# Cargar todos los JSONs de la carpeta data/
python upload/ssn-semanal.py

# Cargar JSONs desde otra carpeta
python upload/ssn-semanal.py --input carpeta_entrada/

# Modo debug (muestra más información mientras se ejecuta)
python upload/ssn-semanal.py --debug
```

Los dos scripts usan la configuración de sus respectivos archivos `config.json` y las credenciales del archivo `.env`.

### Archivos de configuración

- `extract/config.json`: Te permite configurar los parámetros de extracción y procesamiento
- `upload/config.json`: Configura los parámetros de conexión y carga al sistema SSN

### Documentación adicional

En la carpeta `docs/` vas a encontrar:
- Especificaciones técnicas del formato que pide la SSN
- Ejemplos de archivos de datos para hacer pruebas

## Soporte

Para reportar problemas o pedir mejoras, creá un issue en el repositorio.
