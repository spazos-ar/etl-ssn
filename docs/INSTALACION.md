# Guía de Instalación

Esta guía te ayudará a configurar todo lo necesario para ejecutar el sistema ETL SSN en Windows 10/11.

## Prerequisitos

### 1. Instalar Git

Git es necesario para clonar el repositorio. Para instalarlo:

1. Descarga Git para Windows desde [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Ejecuta el instalador descargado
3. Durante la instalación:
   - Mantén las opciones por defecto
   - En "Adjusting your PATH environment", selecciona "Git from the command line and also from 3rd-party software"
   - En "Choosing HTTPS transport backend", selecciona "Use the native Windows Secure Channel library"
4. Completa la instalación

Para verificar la instalación, abre PowerShell y ejecuta:
```powershell
git --version
```

### 2. Instalar Python

El proyecto requiere Python 3.8 o superior:

1. Descarga Python desde [https://www.python.org/downloads/](https://www.python.org/downloads/)
   - Asegúrate de descargar la versión de 64 bits para Windows
2. Ejecuta el instalador
3. **¡IMPORTANTE!** Marca la opción "Add Python to PATH" antes de comenzar la instalación
4. Selecciona "Install Now" para una instalación estándar

Para verificar la instalación, abre PowerShell y ejecuta:
```powershell
python --version
pip --version
```

## Instalación del Proyecto

### 1. Clonar el Repositorio

1. Abre PowerShell

2. Crea y navega al directorio recomendado para proyectos (si no existe, los comandos lo crearán):
```powershell
# Crear las carpetas si no existen
New-Item -ItemType Directory -Force -Path "$HOME\source\repos"

# Navegar a la carpeta
cd $HOME\source\repos
```

> **Nota**: Se recomienda usar la estructura `source\repos` en tu carpeta de usuario para mantener organizados todos tus proyectos, siguiendo las buenas prácticas de desarrollo en Windows.

3. Clona el repositorio:
```powershell
git clone https://github.com/spazos-ar/etl-ssn.git
cd etl-ssn
```

### 2. Crear Entorno Virtual (Recomendado)

Es una buena práctica usar un entorno virtual para aislar las dependencias:

```powershell
# Crear el entorno virtual
python -m venv .venv

# Activar el entorno virtual
.\.venv\Scripts\Activate

# Si ves un error de ejecución de scripts, ejecuta esto como administrador:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Instalar Dependencias

Con el entorno virtual activado, instala las dependencias:

```powershell
pip install -r requirements.txt
```

### 4. Configurar Credenciales

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
SSN_USER=tu_usuario
SSN_PASSWORD=tu_contraseña
SSN_COMPANY=tu_codigo_compania
```

## Verificar la Instalación

Para verificar que todo esté correctamente instalado:

1. Asegúrate de que el entorno virtual esté activado (verás `(.venv)` al inicio del prompt)

2. Prueba el script de extracción:
```powershell
python .\extract\xls-semanal.py --xls-path .\docs\datos_prueba_SEMANAL.xlsx
```

3. Si no hay errores, prueba una consulta al sistema SSN:
```powershell
.\Procesar.bat query 2025-15
```

## Solución de Problemas

### Error: "python no se reconoce como un comando..."
- Verifica que Python esté en el PATH de Windows
- Reinicia PowerShell después de instalar Python

### Error al activar el entorno virtual
- Ejecuta `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Asegúrate de estar en el directorio correcto al activar el entorno

### Error al instalar dependencias
- Verifica que estés usando pip desde el entorno virtual
- Actualiza pip: `python -m pip install --upgrade pip`

### Errores de conexión con la SSN
- Verifica tus credenciales en el archivo `.env`
- Asegúrate de tener conexión a Internet
- Verifica que los endpoints en `upload/config.json` sean correctos

## Ayuda Adicional

Si encuentras algún problema durante la instalación:
1. Revisa la [documentación oficial](URL_DEL_REPO)
2. Crea un issue en el repositorio con los detalles del error
3. Contacta al equipo de soporte de tu compañía
