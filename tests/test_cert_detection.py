#!/usr/bin/env python
import os
import sys
# Ajustar path para el directorio tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from upload.lib.cert_utils import cert_manager

print("=== Prueba de Detección Automática de Certificados ===")
print()

# Probar ambiente de producción
env = 'prod'
config = cert_manager.get_environment_config(env)

print(f"Ambiente: {env}")
print(f"Certificado detectado: {config['cert_path']}")
print(f"Ruta completa: {config['full_cert_path']}")
print(f"Existe el archivo: {config['cert_exists']}")
print(f"URL: {config['url']}")
print(f"Verificación SSL: {config['ssl_verify']}")
print()

# Probar ambiente de test
env = 'test'
config = cert_manager.get_environment_config(env)

print(f"Ambiente: {env}")
print(f"Certificado detectado: {config['cert_path']}")
print(f"Ruta completa: {config['full_cert_path']}")
print(f"Existe el archivo: {config['cert_exists']}")
print(f"URL: {config['url']}")
print(f"Verificación SSL: {config['ssl_verify']}")
print()

# Listar todos los certificados disponibles
print("=== Certificados Disponibles ===")
certs = cert_manager.list_available_certs()
for cert in certs:
    print(f"📜 {cert['filename']} - {cert['environment']} - {cert['modified'].strftime('%Y-%m-%d %H:%M:%S')}")