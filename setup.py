#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de configuración inicial para el proyecto ETL-SSN.
Este script:
1. Configura el entorno virtual
2. Instala las dependencias
3. Obtiene y configura el certificado SSL
4. Verifica la configuración

Autor: G. Casanova
Fecha: Septiembre 2025
"""

import os
import sys
import venv
import subprocess
import platform
from pathlib import Path

def create_venv():
    """Crea el entorno virtual si no existe."""
    venv_dir = Path('.venv')
    if not venv_dir.exists():
        print("Creando entorno virtual...")
        venv.create('.venv', with_pip=True)
        return True
    return False

def get_python_path():
    """Obtiene la ruta al ejecutable de Python en el entorno virtual."""
    if platform.system() == "Windows":
        python_path = Path('.venv/Scripts/python.exe')
    else:
        python_path = Path('.venv/bin/python')
    return str(python_path.absolute())

def install_requirements():
    """Instala las dependencias del proyecto."""
    python_path = get_python_path()
    print("Instalando dependencias...")
    subprocess.check_call([python_path, '-m', 'pip', 'install', '-r', 'requirements.txt'])

def setup_ssl_cert():
    """Configura el certificado SSL."""
    python_path = get_python_path()
    
    # Crear directorio de certificados si no existe
    cert_dir = Path('upload/certs')
    cert_dir.mkdir(parents=True, exist_ok=True)
    
    print("Obteniendo certificado SSL de la SSN...")
    try:
        subprocess.check_call([python_path, 'upload/get_cert.py'])
        
        # Mover el certificado a la carpeta correcta
        cert_files = list(Path('.').glob('ssn_cert_*.pem'))
        if cert_files:
            latest_cert = max(cert_files, key=lambda x: x.stat().st_mtime)
            dest_path = cert_dir / latest_cert.name
            latest_cert.rename(dest_path)
            print(f"Certificado guardado en: {dest_path}")
            
            # Actualizar la configuración
            update_config(latest_cert.name)
        else:
            print("ADVERTENCIA: No se pudo obtener el certificado automáticamente.")
            print("Por favor, siga las instrucciones en docs/INSTALACION.md para la configuración manual.")
    except Exception as e:
        print(f"Error al obtener el certificado: {e}")
        print("Por favor, siga las instrucciones en docs/INSTALACION.md para la configuración manual.")

def update_config(cert_filename):
    """Actualiza los archivos de configuración con el nuevo certificado."""
    config_files = ['upload/config-mensual.json', 'upload/config-semanal.json']
    
    for config_file in config_files:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if '"cafile":' not in content:
                # Si no existe la configuración SSL, la agregamos
                content = content.replace(
                    '"verify": true\n    }',
                    f'"verify": true,\n        "cafile": "certs/{cert_filename}"\n    }}'
                )
            else:
                # Si existe, actualizamos el nombre del archivo
                import re
                content = re.sub(
                    r'"cafile":\s*"[^"]*"',
                    f'"cafile": "certs/{cert_filename}"',
                    content
                )
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Configuración actualizada: {config_file}")

def setup_env_file():
    """Configura el archivo .env con las credenciales del usuario."""
    print("\n=== Configuración de credenciales ===")
    print("Por favor, ingrese los siguientes datos para acceder al servicio de la SSN:\n")
    
    # Solicitar datos al usuario
    user = input("Usuario SSN: ").strip()
    while not user:
        print("El usuario es obligatorio.")
        user = input("Usuario SSN: ").strip()
    
    password = input("Contraseña SSN: ").strip()
    while not password:
        print("La contraseña es obligatoria.")
        password = input("Contraseña SSN: ").strip()
    
    company = input("Código de compañía (4 dígitos): ").strip()
    while not (company.isdigit() and len(company) == 4):
        print("El código de compañía debe ser un número de 4 dígitos.")
        company = input("Código de compañía (4 dígitos): ").strip()
    
    # Crear el archivo .env
    env_content = f"""# Credenciales para el servicio SSN
SSN_USER={user}
SSN_PASSWORD={password}
SSN_COMPANY={company}

# Ejemplo:
# SSN_USER=usuario_ssn
# SSN_COMPANY=0777
# SSN_PASSWORD=******"""
    
    env_path = Path('.env')
    if env_path.exists():
        print("\n⚠️ El archivo .env ya existe. ¿Desea sobrescribirlo? (s/n)")
        response = input().lower().strip()
        if response != 's':
            print("Configuración de credenciales cancelada.")
            return False
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✓ Archivo .env creado correctamente")
    return True

def verify_setup():
    """Verifica que todo esté correctamente configurado."""
    python_path = get_python_path()
    print("\nVerificando configuración...")
    
    # Verificar que existe el archivo .env
    if not Path('.env').exists():
        print("✗ No se encuentra el archivo .env con las credenciales")
        return False
    
    try:
        # Intentar una conexión de prueba
        result = subprocess.run(
            [python_path, 'upload/ssn-mensual.py', '--test'],
            capture_output=True,
            text=True
        )
        if "Conexión SSL verificada correctamente" in result.stdout:
            print("✓ Configuración SSL verificada correctamente")
            return True
        else:
            print("✗ Error en la verificación SSL")
            print(result.stdout)
            return False
    except Exception as e:
        print(f"✗ Error en la verificación: {e}")
        return False

def main():
    """Función principal de configuración."""
    print("""
=== Configuración inicial del proyecto ETL-SSN ===

Este asistente lo guiará en la configuración inicial del sistema:
1. Creación del entorno virtual Python
2. Instalación de dependencias
3. Configuración de credenciales SSN
4. Configuración del certificado SSL
5. Verificación de la configuración
""")
    
    input("Presione Enter para comenzar...")
    
    print("\n=== Paso 1: Configuración del entorno virtual ===")
    # Crear entorno virtual si no existe
    if create_venv():
        print("✓ Entorno virtual creado")
    else:
        print("✓ Entorno virtual ya existe")
    
    try:
        print("\n=== Paso 2: Instalación de dependencias ===")
        # Instalar dependencias
        install_requirements()
        print("✓ Dependencias instaladas")
        
        print("\n=== Paso 3: Configuración de credenciales ===")
        # Configurar archivo .env
        if not setup_env_file():
            print("\n⚠️ La configuración de credenciales fue cancelada")
            print("Para completar la configuración manualmente, siga las instrucciones en docs/INSTALACION.md")
            sys.exit(1)
        
        print("\n=== Paso 4: Configuración SSL ===")
        # Configurar certificado SSL
        setup_ssl_cert()
        
        print("\n=== Paso 5: Verificación final ===")
        # Verificar configuración
        if verify_setup():
            print("\n✨ ¡Configuración completada exitosamente! ✨")
            print("\nPuede comenzar a usar el sistema. Para más información, consulte docs/INSTALACION.md")
        else:
            print("\n⚠️ La configuración no pudo ser verificada completamente")
            print("Por favor, revise los errores anteriores y consulte docs/INSTALACION.md")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n✗ Error durante la configuración: {e}")
        print("Por favor, consulte docs/INSTALACION.md para instrucciones de configuración manual")
        sys.exit(1)

if __name__ == "__main__":
    main()
