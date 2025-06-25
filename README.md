# ETL SSN

Sistema de extracción y carga de datos para la Superintendencia de Seguros de la Nación (SSN). Este proyecto automatiza el proceso de carga de información semanal y mensual requerida por la SSN, facilitando el cumplimiento de las obligaciones regulatorias de las compañías de seguros.

## Descripción

El sistema tiene dos componentes principales:

1. **Extracción de datos**: Procesa los archivos Excel semanales o mensuales ubicados en la carpeta `data/` y los prepara según el formato requerido por la SSN.
2. **Carga de datos**: Sube automáticamente la información procesada al sistema de la SSN usando las credenciales configuradas.

### Estructura del proyecto

- `data/`: Directorio para los archivos de datos
  - `datos_semanales.xlsx`: Archivo de entrada semanal
  - `datos_mensuales.xlsx`: Archivo de entrada mensual (opcional)
  - `processed/weekly/`: Carpeta donde quedan guardados los archivos semanales ya procesados
  - `processed/monthly/`: Carpeta donde quedan guardados los archivos mensuales ya procesados
- `extract/`: Módulo de extracción y procesamiento de datos
  - `xls-semanal.py`: Script para procesar los archivos Excel semanales
  - `xls-mensual.py`: Script para procesar los archivos Excel mensuales
  - `config-semanal.json`: Configuración del proceso de extracción semanal
  - `config-mensual.json`: Configuración del proceso de extracción mensual
- `upload/`: Módulo de carga de datos
  - `ssn-semanal.py`: Script para la carga automática semanal al sistema SSN
  - `ssn-mensual.py`: Script para la carga automática mensual al sistema SSN
  - `config-semanal.json`: Configuración del proceso de carga semanal
  - `config-mensual.json`: Configuración del proceso de carga mensual

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

2. El script `ProcesarSem.bat` tiene estas opciones de uso:

```powershell
# Extraer datos del Excel semanal
.\ProcesarSem.bat datos_semanales.xlsx

# Extraer datos y enviarlos automáticamente a la SSN con confirmación
.\ProcesarSem.bat datos_semanales.xlsx full

# Enviar y confirmar los JSONs que ya están en data/processed/weekly
.\ProcesarSem.bat upload

# Consultar el estado de una semana específica
.\ProcesarSem.bat query 2025-15

# Pedir rectificativa de una semana específica
.\ProcesarSem.bat fix 2025-15

# Enviar una semana vacía sin operaciones
.\ProcesarSem.bat empty 2025-15
```

El script va a hacer automáticamente según la opción que elijas:
- Validar el formato de los datos de entrada
- Procesar el Excel según lo que pide la SSN
- Generar los archivos JSON en la carpeta `data/`
- Cargar la información al sistema SSN usando tus credenciales
- Mover los archivos procesados a la carpeta `data/processed/weekly/`

### Proceso de carga mensual

1. Poné el archivo Excel con los datos mensuales en la carpeta `data/` con el nombre `datos_mensuales.xlsx`

2. El script `ProcesarMes.bat` tiene estas opciones de uso:

```powershell
# Extraer datos del Excel mensual
.\ProcesarMes.bat datos_mensuales.xlsx

# Extraer datos y enviarlos automáticamente a la SSN con confirmación
.\ProcesarMes.bat datos_mensuales.xlsx full

# Enviar y confirmar los JSONs que ya están en data/processed/monthly
.\ProcesarMes.bat upload
```

El flujo mensual es similar al semanal, pero utiliza los scripts y configuraciones específicas para el proceso mensual. Los archivos JSON generados tendrán el formato `Mes-YYYY-MM.json` y se almacenarán en `data/processed/monthly/`.

### Diferencias entre procesos semanal y mensual

- **Archivos de entrada**: `datos_semanales.xlsx` (semanal) vs `datos_mensuales.xlsx` (mensual)
- **Scripts de procesamiento**: `xls-semanal.py` y `ssn-semanal.py` (semanal) vs `xls-mensual.py` y `ssn-mensual.py` (mensual)
- **Configuraciones**: `config-semanal.json` vs `config-mensual.json`
- **Carpetas de salida**: `processed/weekly/` vs `processed/monthly/`
- **Formato de archivos JSON**: `SemanaXX.json` (semanal) vs `Mes-YYYY-MM.json` (mensual)

### Uso de scripts Python por separado

Si necesitás ejecutar los scripts de Python por separado, podés hacerlo así:

#### Script de extracción semanal (`extract/xls-semanal.py`)

Este script procesa los archivos Excel semanales y genera los JSONs necesarios para la carga:

```powershell
# Procesar un archivo Excel semanal (ruta requerida)
python extract/xls-semanal.py --xls-path data/datos_semanales.xlsx

# Especificar un archivo de configuración alternativo
python extract/xls-semanal.py --config extract/config-semanal.json --xls-path data/datos_semanales.xlsx
```

#### Script de extracción mensual (`extract/xls-mensual.py`)

Este script procesa los archivos Excel mensuales y genera los JSONs necesarios para la carga:

```powershell
# Procesar un archivo Excel mensual (ruta requerida)
python extract/xls-mensual.py --xls-path data/datos_mensuales.xlsx

# Especificar un archivo de configuración alternativo
python extract/xls-mensual.py --config extract/config-mensual.json --xls-path data/datos_mensuales.xlsx
```

Los argumentos disponibles para ambos scripts son:
- `--xls-path`: Ruta al archivo Excel a procesar (requerido)
- `--config`: Ruta al archivo de configuración (opcional, por defecto usa el correspondiente semanal o mensual)

#### Script de carga semanal (`upload/ssn-semanal.py`)

Este script se encarga de subir y gestionar los datos semanales en el sistema de la SSN:

```powershell
# Cargar un archivo JSON de datos semanal - sin confirmacion
python upload/ssn-semanal.py data/Semana15.json

# Cargar y confirmar un archivo JSON de datos semanal
python upload/ssn-semanal.py --confirm-week data/Semana15.json

# Consultar el estado de una semana específica
python upload/ssn-semanal.py --query-week 2025-15

# Pedir Rectificativa de una semana específica
python upload/ssn-semanal.py --fix-week 2025-15

# Enviar una semana sin operaciones
python upload/ssn-semanal.py --empty-week 2025-15

# Especificar un archivo de configuración alternativo
python upload/ssn-semanal.py --config upload/config-semanal.json data/Semana15.json
```

#### Script de carga mensual (`upload/ssn-mensual.py`)

Este script se encarga de subir y gestionar los datos mensuales en el sistema de la SSN:

```powershell
# Cargar un archivo JSON de datos mensual - sin confirmacion
python upload/ssn-mensual.py data/Mes-2024-05.json

# Cargar y confirmar un archivo JSON de datos mensual
python upload/ssn-mensual.py --confirm-month data/Mes-2024-05.json

# Especificar un archivo de configuración alternativo
python upload/ssn-mensual.py --config upload/config-mensual.json data/Mes-2024-05.json
```

Los argumentos disponibles para ambos scripts de carga son:
- `--config`: Ruta al archivo de configuración (opcional, por defecto usa el correspondiente semanal o mensual)
- `--confirm-week` / `--confirm-month`: Confirma la entrega y mueve el archivo a la carpeta correspondiente
- Otros argumentos específicos según el flujo (ver ayuda de cada script)

Ambos scripts usan la configuración de sus respectivos archivos y las credenciales del archivo `.env`.

### Archivos de configuración

- `extract/config-semanal.json`: Configuración del proceso de extracción semanal
- `extract/config-mensual.json`: Configuración del proceso de extracción mensual
- `upload/config-semanal.json`: Configuración del proceso de carga semanal
- `upload/config-mensual.json`: Configuración del proceso de carga mensual

### Documentación adicional

En la carpeta `docs/` vas a encontrar:
- Especificaciones técnicas del formato requerido por la SSN
- Ejemplos de archivos de datos para hacer pruebas
- Guía de instalación detallada para Windows 10/11

## Soporte

Si encontrás algún problema o querés sugerir mejoras, creá un issue en el repositorio.
