# Guía de Instalación

Esta guía te va a ayudar a configurar todo lo necesario para ejecutar el sistema ETL SSN en Windows 10/11.

## Prerrequisitos

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

### 🚀 Instalación Rápida (Recomendada)

**¿Acabás de clonar el repositorio? Seguí estos 3 pasos:**

1. **Clona el repositorio** (si no lo hiciste):
```powershell
# Crear carpeta y navegar
New-Item -ItemType Directory -Force -Path "$HOME\source\repos"
cd $HOME\source\repos

# Clonar proyecto
git clone https://github.com/spazos-ar/etl-ssn.git
cd etl-ssn
```

2. **Ejecuta la configuración automática**:
```powershell
python setup.py
```

3. **¡Listo! Ya podés usar el sistema** 🎉

El script automático se encarga de todo: crear el entorno virtual, instalar dependencias, configurar SSL, validar credenciales, y preparar el sistema.

---

### 📋 Instalación Manual Detallada (Solo si necesitás más control)

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

### 3. Configuración Automática ⭐ (RECOMENDADO)

**Esta es la forma más rápida y sencilla de completar la instalación:**

```powershell
# Con el entorno virtual activado, ejecutar:
python setup.py
```

🎉 **¡Eso es todo!** El script `setup.py` realizará automáticamente:
- ✅ Instalación de todas las dependencias (incluyendo python-dotenv)
- ✅ Configuración del certificado SSL
- ✅ Solicitud y validación de tus credenciales del SSN
- ✅ Creación del archivo `.env` con tu configuración  
- ✅ Verificación de la conexión con el sistema SSN
- ✅ Activación automática del entorno virtual

### Comandos disponibles después de `setup.py`:

Una vez completada la configuración automática, tenés estos comandos listos para usar:

```powershell
# Activar entorno virtual (si no está activado)
.\.venv\Scripts\Activate

# Consultar estado de una semana (año-número de semana)
.\ProcesarSem.bat query 2025-15

# Enviar datos de una semana (año-número de semana)
.\ProcesarSem.bat upload 2025-15

# Consultar estado de un mes (año-mes)
.\ProcesarMes.bat query 2025-05

# Enviar datos de un mes (año-mes)
.\ProcesarMes.bat upload 2025-05
```

### 4. Instalación Manual (Alternativa)

Si prefieres realizar la instalación manualmente o si la configuración automática falla:

#### 4.1 Instalar Dependencias

Con el entorno virtual activado, instala las dependencias:

```powershell
pip install -r requirements.txt
```

#### 4.2 Configurar Certificado SSL

Hay tres opciones para configurar el certificado SSL:

##### Opción A: Obtener el certificado automáticamente
```powershell
# Obtener el certificado
python upload/get_cert.py

# El certificado se guardará automáticamente en upload/certs/
```

##### Opción B: Deshabilitar verificación SSL (NO RECOMENDADO PARA PRODUCCIÓN)
Edita `upload/config-mensual.json` y `upload/config-semanal.json`:
```json
{
    "ssl": {
        "verify": false
    }
}
```

##### Opción C: Usar certificado corporativo
Si tu organización tiene un certificado propio o un proxy HTTPS:
1. Obtén el certificado de tu organización
2. Colócalo en `upload/certs/`
3. Configura la ruta en los archivos de configuración:
```json
{
    "ssl": {
        "verify": true,
        "cafile": "certs/certificado_corporativo.pem"
    }
}
```

### 5. Configurar Credenciales y Archivos de Configuración

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

2. Verifica la conexión SSL:
```powershell
python upload/ssn-mensual.py --test
```

3. Prueba el script de extracción semanal:
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

## Actualización y Desinstalación

### Actualización de versión

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

### Desinstalación del Sistema

Para desinstalar completamente el sistema, simplemente elimina el directorio del proyecto:

1. Primero, asegúrate de hacer una copia de seguridad de cualquier dato importante:
   - Archivos Excel en la carpeta `data/`
   - Archivo de credenciales `.env`
   - Archivos de configuración personalizados

2. Cierra cualquier terminal o editor que esté usando el proyecto

3. Elimina el directorio completo:
```powershell
# Navega al directorio padre
cd $HOME\source\repos

# Elimina el directorio del proyecto
Remove-Item -Recurse -Force etl-ssn
```

4. (Opcional) Si no vas a volver a usar el sistema, puedes eliminar el repositorio remoto de tus credenciales de Git:
```powershell
git config --global --unset credential.helper
```

Para reinstalar el sistema en el futuro:
1. Clona nuevamente el repositorio
2. Sigue las instrucciones de instalación en este documento
3. Restaura cualquier archivo de configuración o datos que hayas respaldado

## Solución de Problemas

### Errores SSL

Si obtienes errores relacionados con SSL:

1. Verifica que el certificado esté instalado:
```powershell
# Regenerar el certificado
python upload/get_cert.py

# Probar la conexión
python upload/ssn-mensual.py --test
```

2. Si el error persiste:
   - Verifica que el certificado esté en `upload/certs/`
   - Verifica que la ruta en la configuración sea correcta
   - Asegúrate de que el certificado esté actualizado

3. Para más detalles, habilita el modo debug en la configuración:
```json
{
    "debug": true
}
```

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

## Mantenimiento

### Actualización de Certificados SSL

Los certificados SSL suelen tener una validez limitada. Para actualizarlos:

1. Regenera el certificado:
```powershell
python upload/get_cert.py
```

2. Verifica la conexión:
```powershell
python upload/ssn-mensual.py --test
```

Si el certificado no se puede obtener automáticamente, sigue las instrucciones en la sección "Opción C: Usar certificado corporativo".

## Ayuda Adicional

Si encuentras algún problema durante la instalación:
1. Revisa la [documentación oficial](URL_DEL_REPO)
2. Habilita el modo debug en la configuración para obtener más detalles
3. Ejecuta las pruebas de conexión: `python upload/ssn-mensual.py --test`
4. Verifica los logs en modo debug
5. Crea un issue en el repositorio con los detalles del error
6. Contacta al equipo de soporte de tu compañía
