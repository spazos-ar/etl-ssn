# ETL SSN

Sistema de extracción y carga de datos para el Servicio de Supervisión Nacional (SSN).

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

Para ejecutar el proceso de carga semanal:

```powershell
.\ejecutar.bat
```

El script utilizará la configuración operativa del archivo `upload/config_ssn.json` y las credenciales del archivo `.env`.
