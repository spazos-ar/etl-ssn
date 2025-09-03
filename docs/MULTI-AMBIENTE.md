# Configuración Multi-Ambiente para SSN

## Resumen

El sistema ETL-SSN ahora soporta múltiples ambientes (producción y test) con configuraciones y certificados específicos para cada uno.

## Estructura de Archivos

### Certificados
- `upload/certs/ssn_cert_20250903.pem` - Certificado de producción
- `upload/certs/ssn_cert_test_20250903.pem` - Certificado de test (placeholder)

### Configuraciones por Ambiente
- `upload/config-mensual.json` - Configuración mensual activa
- `upload/config-semanal.json` - Configuración semanal activa
- `upload/config-mensual-prod.json` - Configuración mensual para producción
- `upload/config-mensual-test.json` - Configuración mensual para test
- `upload/config-semanal-prod.json` - Configuración semanal para producción
- `upload/config-semanal-test.json` - Configuración semanal para test

## Uso

### Cambiar Ambiente
```batch
# Cambiar a producción
SetAmbiente.bat prod

# Cambiar a test  
SetAmbiente.bat test
```

### Ejecutar Scripts
Los scripts ahora muestran información del ambiente al inicio:

```batch
# Script mensual
.\ProcesarMes.bat query 2025-06

# Script semanal  
.\ProcesarSem.bat query 2025-33
```

## Mensajes de Inicio

### Mensual
```
============================================================
📊 SCRIPT DE CARGA MENSUAL - SUPERINTENDENCIA DE SEGUROS
============================================================
🏢 Tipo de entrega: MENSUAL
🌐 Ambiente: PROD
🔗 Servidor: https://ri.ssn.gob.ar/api
📅 Fecha: No disponible
------------------------------------------------------------
```

### Semanal
```
============================================================
📈 SCRIPT DE CARGA SEMANAL - SUPERINTENDENCIA DE SEGUROS
============================================================
🏢 Tipo de entrega: SEMANAL
🌐 Ambiente: PROD
🔗 Servidor: https://ri.ssn.gob.ar/api
📅 Fecha: No disponible
------------------------------------------------------------
```

## Ambientes Disponibles

## Configuración SSL Inteligente

El sistema ahora incluye configuración SSL diferenciada por ambiente:

### Producción (`prod`)
- **URL**: https://ri.ssn.gob.ar/api
- **Certificado**: certs/ssn_cert_20250903.pem
- **Verificación SSL**: **Habilitada** (`verify: true`)
- **Timeout**: 30 segundos
- **Características**: Conexión segura completa con validación de certificados

### Test (`test`)
- **URL**: https://testri.ssn.gob.ar/api  
- **Certificado**: certs/ssn_cert_test_20250903.pem
- **Verificación SSL**: **Deshabilitada** (`verify: false`)
- **Timeout**: 15 segundos
- **Características**: Conexión sin verificación SSL para evitar problemas del servidor test

## Configuración Automática

El script `SetAmbiente.bat` ahora configura automáticamente:

1. **URL del servidor** según el ambiente
2. **Certificado apropiado** para cada ambiente
3. **Configuración SSL** (`verify: true/false`)
4. **Timeouts optimizados** para cada servidor

```batch
# El script actualiza automáticamente todos los parámetros SSL
SetAmbiente.bat prod   # Configura verify: true, timeout: 30s
SetAmbiente.bat test   # Configura verify: false, timeout: 15s
```

## Verificación de Conexión

Para verificar que el ambiente está configurado correctamente:

```batch
# Probar conexión SSL
python upload/ssn-mensual.py --test
python upload/ssn-semanal.py --test
```

**Mensajes esperados:**

**En PROD:**
```
🔐 Certificados de seguridad SSN cargados correctamente
🔒 Configurando conexión segura SSL/TLS...
✅ Conexión SSL verificada correctamente
```

**En TEST:**
```
🔐 Certificados de seguridad SSN cargados correctamente
✅ Conexión SSL configurada (verificación deshabilitada)
✅ Conexión SSL verificada correctamente
```

## Requisitos

1. **Certificados**: Los certificados se generan automáticamente al ejecutar `python setup.py`

2. **Variables de Entorno**: Las variables SSN_USER, SSN_PASSWORD y SSN_COMPANY deben estar configuradas en el archivo `.env`

## Troubleshooting

### Problemas Comunes

**1. Error de Certificado en PROD**
```
Error crítico en la configuración SSL: certificate verify failed
```
**Solución**: Regenerar certificado ejecutando `python upload/get_cert.py --env prod`

**2. Timeout en TEST**
```
Error de autenticación: The handshake operation timed out
```
**Solución**: Normal para servidor TEST. El sistema está configurado para manejar estos casos automáticamente con `verify: false`.

**3. Cambio de Ambiente Falla**
```
❌ Error actualizando config-mensual.json
```
**Solución**: Verificar que los archivos de configuración no estén corruptos. Recrear desde templates:
```batch
copy upload\config-mensual-prod.json upload\config-mensual.json
copy upload\config-semanal-prod.json upload\config-semanal.json
```

**4. Variables de Entorno No Encontradas**
```
❌ Error: La variable de entorno SSN_COMPANY no está definida
```
**Solución**: 
- Verificar que existe el archivo `.env` en la raíz del proyecto
- Ejecutar `python setup.py` para recrear la configuración

### Verificación de Estado

Para verificar el estado actual del ambiente:
```batch
# Ver configuración actual
type upload\config-mensual.json | findstr "environment\|baseUrl\|verify"

# Probar conexión
python upload\ssn-mensual.py --test
```

### Archivos de Log y Debug

Si hay problemas, habilitar modo debug editando temporalmente el archivo config:
```json
{
    "debug": true,
    // ... resto de configuración
}
```

Esto mostrará información detallada sobre el proceso de conexión SSL.
