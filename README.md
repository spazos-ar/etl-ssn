# ETL SSN

Sistema de extracción y carga de datos de inversiones en los servicios de la Superintendencia de Seguros de la Nación (SSN). Este proyecto automatiza el proceso de carga de información semanal y mensual requerida por la SSN, facilitando el cumplimiento de las obligaciones regulatorias de las compañías de seguros.

---

## 🚀 Instalación y configuración

### Si ya tenés instalados los prerrequisitos de software
(Si nos los tenés, revisá la [guía detallada](docs/INSTALACION.md)).

**Paso 1**: Cloná este repositorio en tu computadora:
```powershell
# Crear carpeta y navegar
New-Item -ItemType Directory -Force -Path "$HOME\source\repos"
cd $HOME\source\repos

# Clonar proyecto
git clone https://github.com/spazos-ar/etl-ssn.git
cd etl-ssn
```

**Paso 2**: Ejecutá la configuración automática:
```powershell
python setup.py
```

**¡Eso es todo!** 🎉 El script `setup.py` se encarga de:
- ✅ Crear el entorno virtual (.venv)
- ✅ Instalar todas las dependencias necesarias (incluyendo dotenv)
- ✅ Configurar el certificado SSL automáticamente  
- ✅ Validar tus credenciales de SSN con el endpoint de login
- ✅ Crear el archivo `.env` con la configuración
- ✅ Verificar la conexión con el sistema SSN

### Comandos disponibles después de la instalación:

Después de ejecutar `python setup.py`, tenés estos comandos disponibles:

```powershell
# Activar entorno virtual (si no está activado)
.\.venv\Scripts\Activate

# Cambiar ambiente de trabajo
.\SetAmbiente.bat prod    # Para ambiente de producción
.\SetAmbiente.bat test    # Para ambiente de pruebas

# Procesar datos semanales
.\ProcesarSem.bat query 2025-15

# Procesar datos mensuales  
.\ProcesarMes.bat upload
```

### 🌐 Sistema Multi-Ambiente:

El sistema soporta dos ambientes con configuración SSL inteligente:
- **Producción** (`prod`): https://ri.ssn.gob.ar/api - SSL verificado, certificados completos
- **Pruebas** (`test`): https://testri.ssn.gob.ar/api - SSL sin verificación para evitar problemas del servidor

```powershell
# Cambiar a ambiente de pruebas (SSL deshabilitado, timeout: 15s)
.\SetAmbiente.bat test

# Cambiar a ambiente de producción (SSL habilitado, timeout: 30s)
.\SetAmbiente.bat prod

# Verificar conexión del ambiente actual
python upload\ssn-mensual.py --test
```

El cambio de ambiente configura automáticamente:
✅ URL del servidor apropiada  
✅ Certificados específicos por ambiente  
✅ Configuración SSL optimizada  
✅ Timeouts diferenciados por servidor  

**Nota**: Por defecto se configura el ambiente de **producción**. Para más información consulte [docs/MULTI-AMBIENTE.md](docs/MULTI-AMBIENTE.md).

### Instalación manual (solo si setup.py falla):

1. **Instalá las dependencias del proyecto:**
   ```powershell
   pip install -r requirements.txt
   ```
2. **Configurá las credenciales:**
   - Copiá el archivo `.env.example` y renombralo a `.env`
   - Editá el archivo `.env` y completá tus credenciales:
     ```
     SSN_USER=tu_usuario
     SSN_PASSWORD=tu_contraseña
     SSN_COMPANY=tu_codigo_compania
     ```

Para una guía detallada de instalación en Windows 10/11, consultá [docs/INSTALACION.md](docs/INSTALACION.md).

---

# 📊 Flujo de trabajo SEMANAL

## 1. Extracción de datos semanales

Colocá el archivo Excel semanal en la carpeta `data/` con el nombre `datos_semanales.xlsx`.

Ejecutá el script de extracción:
```powershell
python extract/xls-semanal.py --xls-path data/datos_semanales.xlsx
```
Opcionalmente, podés especificar un archivo de configuración alternativo:
```powershell
python extract/xls-semanal.py --config extract/config-semanal.json --xls-path data/datos_semanales.xlsx
```
Esto generará archivos JSON en `data/` con el formato `SemanaXX.json`.

## 2. Carga de datos semanales

Para subir los datos a la SSN:
```powershell
python upload/ssn-semanal.py data/Semana15.json
```
Opciones adicionales:
- Confirmar la entrega y mover el archivo a la carpeta de procesados:
  ```powershell
  python upload/ssn-semanal.py --confirm-week data/Semana15.json
  ```
- Consultar el estado de una semana:
  ```powershell
  python upload/ssn-semanal.py --query-week 2025-15
  ```
- Pedir rectificativa de una semana:
  ```powershell
  python upload/ssn-semanal.py --fix-week 2025-15
  ```
- Enviar una semana vacía:
  ```powershell
  python upload/ssn-semanal.py --empty-week 2025-15
  ```
- Usar un archivo de configuración alternativo:
  ```powershell
  python upload/ssn-semanal.py --config upload/config-semanal.json data/Semana15.json
  ```

## 3. Automatización semanal

Podés usar el script batch para automatizar el flujo completo. Opciones:

- `./ProcesarSem.bat datos_semanales.xlsx`  
  Extrae los datos del Excel semanal y genera los archivos JSON correspondientes en la carpeta `data/`.
- `./ProcesarSem.bat datos_semanales.xlsx full`  
  Extrae los datos y, además, los envía automáticamente a la SSN con confirmación. Los archivos procesados se mueven a `data/processed/weekly/`.
- `./ProcesarSem.bat upload`  
  Envía y confirma todos los archivos JSON que ya están en `data/processed/weekly/`.

---

# 📅 Flujo de trabajo MENSUAL

## 1. Extracción de datos mensuales

Colocá el archivo Excel mensual en la carpeta `data/` con el nombre `datos_mensuales.xlsx`.

Ejecutá el script de extracción:
```powershell
python extract/xls-mensual.py --xls-path data/datos_mensuales.xlsx
```
Opcionalmente, podés especificar un archivo de configuración alternativo:
```powershell
python extract/xls-mensual.py --config extract/config-mensual.json --xls-path data/datos_mensuales.xlsx
```
Esto generará archivos JSON en `data/` con el formato `Mes-YYYY-MM.json`.

## 2. Carga de datos mensuales

Para subir los datos a la SSN:
```powershell
python upload/ssn-mensual.py data/Mes-2025-05.json
```
Opciones adicionales soportadas por `ssn-mensual.py`:
- Confirmar la entrega y mover el archivo a la carpeta de procesados:
  ```powershell
  python upload/ssn-mensual.py --confirm-month data/Mes-2025-05.json
  ```
- Consultar el estado de un mes:
  ```powershell
  python upload/ssn-mensual.py --query-month 2025-05
  ```
- Pedir rectificativa de un mes:
  ```powershell
  python upload/ssn-mensual.py --fix-month 2025-05
  ```
- Enviar un mes vacío (sin inversiones):
  ```powershell
  python upload/ssn-mensual.py --empty-month 2025-05
  ```
- Usar un archivo de configuración alternativo:
  ```powershell
  python upload/ssn-mensual.py --config upload/config-mensual.json data/Mes-2025-05.json
  ```

### Resumen de argumentos para `ssn-mensual.py`:
- `--config`: Ruta al archivo de configuración (opcional)
- `--confirm-month`: Confirma la entrega y mueve el archivo a la carpeta de procesados
- `--fix-month YYYY-MM`: Pide rectificativa para el mes indicado
- `--query-month YYYY-MM`: Consulta el estado del mes indicado
- `--empty-month YYYY-MM`: Envía un mes vacío sin inversiones
- `data_file`: Archivo JSON a enviar (no requerido con las opciones anteriores)

## 3. Automatización mensual

Podés usar el script batch para automatizar el flujo completo. Opciones:

- `./ProcesarMes.bat datos_mensuales.xlsx`  
  Extrae los datos del Excel mensual y genera los archivos JSON correspondientes en la carpeta `data/`.
- `./ProcesarMes.bat datos_mensuales.xlsx full`  
  Extrae los datos y, además, los envía automáticamente a la SSN con confirmación. Los archivos procesados se mueven a `data/processed/monthly/`.
- `./ProcesarMes.bat upload`  
  Envía y confirma todos los archivos JSON que ya están en `data/processed/monthly/`.

---

# ⚙️ Archivos de configuración

- `extract/config-semanal.json`: Configuración del proceso de extracción semanal
- `extract/config-mensual.json`: Configuración del proceso de extracción mensual
- `upload/config-semanal.json`: Configuración del proceso de carga semanal
- `upload/config-mensual.json`: Configuración del proceso de carga mensual

---

# 📂 Estructura de carpetas

- `data/`: Archivos de datos de entrada y salida
  - `datos_semanales.xlsx`, `datos_mensuales.xlsx`
  - `processed/weekly/`, `processed/monthly/`: Archivos JSON ya procesados
- `extract/`: Scripts y configuraciones de extracción
- `upload/`: Scripts y configuraciones de carga
- `docs/`: Documentación técnica y ejemplos

---

# 🔧 Troubleshooting

## Problemas Comunes

**Error de variables de entorno:**
```
❌ Error: La variable de entorno SSN_COMPANY no está definida
```
**Solución**: Ejecutar `python setup.py` para recrear el archivo `.env`

**Error de certificado en PROD:**
```
Error crítico en la configuración SSL: certificate verify failed
```
**Solución**: Regenerar certificados ejecutando `python upload/get_cert.py`

**Timeout en TEST:**
```
Error de autenticación: The handshake operation timed out  
```
**Solución**: Normal para servidor TEST. El sistema maneja estos casos automáticamente.

**Para más información**: Consultar [docs/MULTI-AMBIENTE.md](docs/MULTI-AMBIENTE.md) y [docs/INSTALACION.md](docs/INSTALACION.md)

---

# 🔧 Documentación adicional y soporte

En la carpeta `docs/` vas a encontrar:
- Especificaciones del formato de datos requerido por la SSN (por versiones actualizadas, visitá el sitio web de la SSN)
- Ejemplos de archivos Excel de datos para hacer pruebas
- Guía de instalación detallada para Windows 10/11

Si encontrás algún problema o querés sugerir mejoras, creá un issue en el repositorio.
