# Guía de Instalación

Esta guía te va a ayudar a configurar todo lo necesario para ejecutar el sistema ETL SSN en Windows 10/11.

## Prerequisitos

### 1. Instalar Git

Git es necesario para clonar el repositorio. Para instalarlo:

1. Descargá Git para Windows desde [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Ejecutá el instalador descargado
3. Durante la instalación:
   - Dejá las opciones por defecto
   - En "Adjusting your PATH environment", seleccioná "Git from the command line and also from 3rd-party software"
   - En "Choosing HTTPS transport backend", seleccioná "Use the native Windows Secure Channel library"
4. Completá la instalación

Para verificar la instalación, abre PowerShell y ejecuta:
```powershell
git --version
```

### 2. Instalar Python

El proyecto requiere Python 3.8 o superior:

1. Descargá Python desde [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Asegurate de descargar la versión de 64 bits para Windows
2. Ejecutá el instalador
3. **¡IMPORTANTE!** Marcá la opción "Add Python to PATH" antes de comenzar la instalación
4. Seleccioná "Install Now" para una instalación estándar

Para verificar la instalación, abre PowerShell y ejecuta:
```powershell
python --version
pip --version
```

## Instalación del Proyecto

### 1. Clonar el Repositorio

1. Abre PowerShell o CMD (ventana de comando)

2. Crea y navega al directorio recomendado para proyectos (si no existe, los comandos lo crearán):
```powershell
# Crear las carpetas si no existen
New-Item -ItemType Directory -Force -Path "$HOME\source\repos"
```
```
# Navegar a la carpeta
cd $HOME\source\repos
```

> **Nota**: Se recomienda usar la estructura `source\repos` en tu carpeta de usuario para mantener organizados todos tus proyectos, siguiendo las buenas prácticas de desarrollo en Windows.

3. Clona el repositorio:
```powershell
git clone https://github.com/spazos-ar/etl-ssn.git
```
```
cd etl-ssn
```

### 2. Crear Entorno Virtual (Recomendado)

Es una buena práctica usar un entorno virtual para aislar las dependencias:

```powershell
# Crear el entorno virtual
python -m venv .venv
```
```
# Activar el entorno virtual
.\.venv\Scripts\Activate
```
```
# Si ves un error de scripts, corré PowerShell como administrador y ejecutá:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Instalar Dependencias

Con el entorno virtual activado, instala las dependencias:

```powershell
pip install -r requirements.txt
```

### 4. Configurar Credenciales y Archivos de Configuración

1. Crea una copia del archivo de ejemplo de configuración:
```powershell
Copy-Item .env.example .env
```

2. Edita el archivo `.env` con tu editor preferido (por ejemplo, Notepad):
```powershell
notepad .env
```

3. Completa las siguientes variables con tus credenciales:
```
SSN_USER=usuario
SSN_PASSWORD=contraseña
SSN_COMPANY=codigo_compania
```

4. Revisá los archivos de configuración para ambos flujos:
   - Extracción semanal: `extract/config-semanal.json`
   - Extracción mensual: `extract/config-mensual.json`
   - Carga semanal: `upload/config-semanal.json`
   - Carga mensual: `upload/config-mensual.json`

## Verificar la Instalación

Para verificar que todo esté correctamente instalado:

1. Asegúrate de que el entorno virtual esté activado (verás `(.venv)` al inicio del prompt)

2. Prueba el script de extracción semanal:
```powershell
python .\extract\xls-semanal.py --xls-path .\data\datos_semanales.xlsx
```

3. Prueba el script de extracción mensual:
```powershell
python .\extract\xls-mensual.py --xls-path .\data\datos_mensuales.xlsx
```

4. Si no hay errores, probá una consulta al sistema SSN (flujo semanal):
```powershell
.\ProcesarSem.bat query 2025-15
```

5. Para el flujo mensual, podés ejecutar:
```powershell
.\ProcesarMes.bat upload
```

## Estructura de Carpetas y Archivos

- `data/`: Carpeta para archivos de entrada y salida
  - `datos_semanales.xlsx`: Archivo de entrada semanal
  - `datos_mensuales.xlsx`: Archivo de entrada mensual
  - `processed/weekly/`: Archivos JSON procesados semanalmente
  - `processed/monthly/`: Archivos JSON procesados mensualmente
- `extract/`: Scripts y configuraciones de extracción
  - `xls-semanal.py`, `xls-mensual.py`, `config-semanal.json`, `config-mensual.json`
- `upload/`: Scripts y configuraciones de carga
  - `ssn-semanal.py`, `ssn-mensual.py`, `config-semanal.json`, `config-mensual.json`

## Actualización de versión

Para actualizar el sistema a la última versión disponible en el repositorio:

1. Abrí una ventana de PowerShell o CMD:
   - Presioná `Windows + R`
   - Escribí `powershell` y presioná Enter

2. Navegá hasta la carpeta del proyecto:
```powershell
cd $HOME\source\repos\etl-ssn
```

3. Ejecutá el comando para actualizar:
```powershell
git pull origin main
```

Este comando va a:
- Descargar los últimos cambios del repositorio remoto
- Actualizar tus archivos locales a la última versión
- Mantener tus archivos de configuración y datos sin modificar

> **Nota**: Si tenés cambios locales que no querés perder, primero tenés que hacer commit de esos cambios o guardarlos temporalmente con `git stash`.

## Solución de Problemas

### Error: "python no se reconoce como un comando..."
- Verificá que Python esté en el PATH de Windows
- Reiniciá PowerShell después de instalar Python

### Error al activar el entorno virtual
- Ejecutá `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Asegurate de estar en el directorio correcto al activar el entorno

### Error al instalar dependencias
- Verificá que estés usando pip desde el entorno virtual
- Actualizá pip: `python -m pip install --upgrade pip`

### Errores de conexión con la SSN
- Verificá tus credenciales en el archivo `.env`
- Asegurate de tener conexión a Internet
- Verificá que los endpoints en `upload/config.json` sean correctos

## Ayuda Adicional

Si encuentras algún problema durante la instalación:
1. Revisa la [documentación oficial](URL_DEL_REPO)
2. Crea un issue en el repositorio con los detalles del error
3. Contacta al equipo de soporte de tu compañía
