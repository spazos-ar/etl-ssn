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

# Configurar la codificación para sistemas Windows
if platform.system() == "Windows":
    # Forzar UTF-8 para stdout y stderr
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    # Configurar la consola para UTF-8 si es posible
    try:
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass

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
    subprocess.check_call([python_path, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         encoding='utf-8', errors='replace')

def setup_ssl_cert():
    """Configura el certificado SSL."""
    python_path = get_python_path()
    
    # Crear directorio de certificados si no existe
    cert_dir = Path('upload/certs')
    cert_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Ejecutar script para obtener el certificado
        subprocess.check_call([python_path, 'upload/get_cert.py'], 
                             encoding='utf-8', errors='replace')
        
        # Mover el certificado a la carpeta correcta
        cert_files = list(Path('.').glob('ssn_cert_*.pem'))
        if cert_files:
            latest_cert = max(cert_files, key=lambda x: x.stat().st_mtime)
            dest_path = cert_dir / latest_cert.name
            
            # Si el archivo ya existe, lo eliminamos primero
            if dest_path.exists():
                dest_path.unlink()
            
            latest_cert.rename(dest_path)
            print(f"📁 Certificado guardado en: {dest_path}")
            
            # Actualizar la configuración
            update_config(latest_cert.name)
            print("⚙️  Configuración actualizada correctamente")
        else:
            print("❌ No se pudo obtener el certificado automáticamente.")
            print("📝 Por favor, siga las instrucciones en docs/INSTALACION.md para la configuración manual.")
    except Exception as e:
        print(f"❌ Error al configurar el certificado: {e}")
        print("📝 Por favor, siga las instrucciones en docs/INSTALACION.md para la configuración manual.")

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

def get_masked_input(prompt):
    """Lee la entrada del usuario mostrando asteriscos. Compatible con Windows y Linux."""
    import sys
    import platform
    
    # Determinar el sistema operativo
    if platform.system() == 'Windows':
        return _get_masked_input_windows(prompt)
    else:
        return _get_masked_input_unix(prompt)

def _get_masked_input_windows(prompt):
    """Implementación para Windows usando msvcrt."""
    import msvcrt
    
    print(prompt, end='', flush=True)
    password = []
    
    while True:
        char = msvcrt.getwch()  # Lee un caracter sin mostrarlo
        
        if char == '\r' or char == '\n':  # Enter
            print()  # Nueva línea
            break
        elif char == '\b':  # Backspace
            if password:
                password.pop()
                # Borra el último asterisco
                sys.stdout.write('\b \b')
                sys.stdout.flush()
        else:
            password.append(char)
            # Muestra un asterisco
            sys.stdout.write('*')
            sys.stdout.flush()
    
    return ''.join(password)

def _get_masked_input_unix(prompt):
    """Implementación para sistemas Unix/Linux usando termios."""
    import termios
    import tty
    
    print(prompt, end='', flush=True)
    password = []
    
    # Guardar configuración actual de la terminal
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        # Configurar la terminal para lectura char por char
        tty.setraw(fd)
        
        while True:
            char = sys.stdin.read(1)
            
            if char == '\r' or char == '\n':  # Enter
                sys.stdout.write('\n')
                sys.stdout.flush()
                break
            elif char == '\x7f':  # Backspace en Unix
                if password:
                    password.pop()
                    # Borra el último asterisco
                    sys.stdout.write('\b \b')
                    sys.stdout.flush()
            elif char == '\x03':  # Ctrl+C
                raise KeyboardInterrupt
            else:
                password.append(char)
                # Muestra un asterisco
                sys.stdout.write('*')
                sys.stdout.flush()
                
    finally:
        # Restaurar configuración original de la terminal
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    
    return ''.join(password)

def setup_env_file():
    """Configura el archivo .env con las credenciales del usuario."""
    print("\n=== Configuración de credenciales ===")
    print("Por favor, ingrese los siguientes datos para acceder al servicio de la SSN:\n")
    
    # Solicitar datos al usuario
    user = input("Usuario SSN: ").strip()
    while not user:
        print("El usuario es obligatorio.")
        user = input("Usuario SSN: ").strip()
    
    password = get_masked_input("Contraseña SSN: ").strip()
    while not password:
        print("La contraseña es obligatoria.")
        password = get_masked_input("Contraseña SSN: ").strip()
    
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
        response = input("\n⚠️ El archivo .env ya existe. ¿Desea sobrescribirlo? (s/n): ").lower().strip()
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
        # Primero verificar conexión SSL
        result = subprocess.run(
            [python_path, 'upload/ssn-mensual.py', '--test'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        
        if "Conexión SSL verificada correctamente" not in stdout:
            print("✗ Error en la verificación SSL")
            print(stdout)
            print(stderr)
            return False
        
        print("✓ Conexión SSL establecida correctamente")
        
        # Ahora verificar credenciales haciendo una consulta real
        print("✓ Verificando credenciales con la SSN...")
        result = subprocess.run(
            [python_path, 'upload/ssn-mensual.py', '--query-month', '2025-01'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        stdout = result.stdout or ""
        stderr = result.stderr or ""
        
        # Verificar si hay errores de autenticación en stdout o stderr
        auth_error_indicators = [
            "Error de autenticación",
            "401",
            "Unauthorized",
            "Authentication failed",
            "Invalid credentials",
            "Login failed"
        ]
        
        # Buscar indicadores de error de autenticación en ambas salidas
        auth_error_found = any(
            indicator in stdout or indicator in stderr 
            for indicator in auth_error_indicators
        )
        
        # Si el comando falló (return code != 0) y hay indicios de error de autenticación
        if result.returncode != 0 and auth_error_found:
            print("✗ Las credenciales SSN no son válidas")
            print("⚠️ Por favor, verifique usuario, contraseña y código de compañía")
            # Mostrar el error específico
            if "Error de autenticación" in stdout:
                error_line = next((line for line in stdout.split('\n') if "Error de autenticación" in line), "")
                if error_line:
                    print(f"Detalle: {error_line}")
            return False
        elif result.returncode != 0:
            # Error general (no de autenticación)
            print("✗ Error en la verificación de credenciales")
            if stderr.strip():
                print(f"Error: {stderr}")
            elif "Error:" in stdout:
                error_line = next((line for line in stdout.split('\n') if "Error:" in line), "")
                if error_line:
                    print(f"Detalle: {error_line}")
            return False
        else:
            # Comando exitoso (return code = 0)
            print("✓ Credenciales SSN verificadas correctamente")
            return True
            
    except Exception as e:
        print(f"✗ Error en la verificación: {e}")
        return False

def main():
    """Función principal de configuración."""
    print("""
🔧 === Configuración inicial del proyecto ETL-SSN === 🔧

Este asistente lo guiará en la configuración inicial del sistema:
1. 🐍 Creación del entorno virtual Python
2. 📦 Instalación de dependencias
3. 🔑 Configuración de credenciales SSN
4. 🔒 Configuración del certificado de seguridad
5. ✅ Verificación de la configuración
""")
    
    input("Presione Enter para comenzar...")
    
    print("\n🐍 === Paso 1: Configuración del entorno virtual ===")
    # Crear entorno virtual si no existe
    if create_venv():
        print("✅ Entorno virtual creado correctamente")
    else:
        print("✅ Entorno virtual ya existe y está listo para usar")
    
    try:
        print("\n📦 === Paso 2: Instalación de dependencias ===")
        # Instalar dependencias
        install_requirements()
        print("✅ Todas las dependencias han sido instaladas correctamente")
        
        print("\n🔑 === Paso 3: Configuración de credenciales ===")
        # Configurar archivo .env
        if not setup_env_file():
            print("\n⚠️ La configuración de credenciales fue cancelada")
            print("📝 Para completar la configuración manualmente, siga las instrucciones en docs/INSTALACION.md")
            sys.exit(1)
        
        print("\n🔒 === Paso 4: Configuración del certificado de seguridad ===")
        print("🌐 Conectando con la SSN para obtener el certificado de seguridad...")
        # Configurar certificado SSL
        setup_ssl_cert()
        print("\n✅ El certificado se ha configurado correctamente para comunicarse de forma segura con la SSN")
        
        print("\n🎯 === Paso 5: Verificación final ===")
        # Verificar configuración
        if verify_setup():
            print("\n🎉 ¡Configuración completada exitosamente! 🎉")
            print("\nResumen de comandos disponibles:")
            print("  1️⃣ python extract\\xls-mensual.py   : Procesa datos mensuales")
            print("  2️⃣ python extract\\xls-semanal.py   : Procesa datos semanales") 
            print("  3️⃣ python upload\\ssn-mensual.py    : Sube datos mensuales a SSN")
            print("  4️⃣ python upload\\ssn-semanal.py    : Sube datos semanales a SSN")
            print("\n🔧 Para usar Python con las dependencias instaladas, use:")
            print("  1. Para cambiar política de PowerShell (recomendado):")
            print("     🏃▶️ Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser")
            print("     🏃▶️ Luego: .\\.venv\\Scripts\\Activate")
            print("  2. O ejecute directamente con Python del entorno virtual:")
            print("     🏃▶️ .\\.venv\\Scripts\\python.exe <script>")
            print("\nPara más información, consulte docs/INSTALACION.md\n\r")
        else:
            print("\n❌ La configuración no pudo ser verificada completamente")
            print("⚠️ Por favor, revise los errores anteriores")
            print("📝 Para más ayuda, consulte docs/INSTALACION.md\n\r")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error durante la configuración: {e}")
        print("📝 Por favor, consulte docs/INSTALACION.md para instrucciones de configuración manual")
        sys.exit(1)

if __name__ == "__main__":
    main()
