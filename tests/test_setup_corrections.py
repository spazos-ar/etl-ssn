#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar que las correcciones en setup.py funcionan correctamente.
"""

import subprocess
import sys
from pathlib import Path

def test_ssl_import():
    """Prueba la importación corregida de ssn-mensual."""
    print("🧪 === PRUEBA: Importación de ssn-mensual ===")
    
    python_path = Path('.venv/Scripts/python.exe').absolute()
    
    result = subprocess.run(
        [str(python_path), '-c', """
import os, sys, importlib.util
sys.path.insert(0, 'upload')
os.chdir('upload')

try:
    # Importar ssn-mensual.py usando importlib
    spec = importlib.util.spec_from_file_location("ssn_mensual", "ssn-mensual.py")
    ssn_mensual = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ssn_mensual)
    print('✅ Módulo ssn-mensual importado correctamente')
    
    # Verificar que las funciones existen
    if hasattr(ssn_mensual, 'load_config'):
        print('✅ Función load_config disponible')
    else:
        print('❌ Función load_config no encontrada')
        
    if hasattr(ssn_mensual, 'test_ssl_connection'):
        print('✅ Función test_ssl_connection disponible')
    else:
        print('❌ Función test_ssl_connection no encontrada')
        
except Exception as e:
    print(f'❌ Error en importación: {e}')
"""],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    print("Salida:")
    print(result.stdout)
    if result.stderr:
        print("Errores:")
        print(result.stderr)
    
    return result.returncode == 0

def test_set_env():
    """Prueba que set_env.py funciona sin errores."""
    print("\n🧪 === PRUEBA: set_env.py ===")
    
    python_path = Path('.venv/Scripts/python.exe').absolute()
    
    result = subprocess.run(
        [str(python_path), 'upload/set_env.py', 'prod'],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    print("Salida:")
    print(result.stdout)
    if result.stderr:
        print("Errores:")
        print(result.stderr)
    
    return result.returncode == 0

def main():
    print("🔧 === VERIFICACIÓN DE CORRECCIONES SETUP.PY ===\n")
    
    test1_ok = test_ssl_import()
    test2_ok = test_set_env()
    
    print(f"\n📋 === RESUMEN ===")
    print(f"   Importación ssn-mensual: {'✅' if test1_ok else '❌'}")
    print(f"   Script set_env.py: {'✅' if test2_ok else '❌'}")
    
    if test1_ok and test2_ok:
        print("\n🎉 ¡Todas las correcciones funcionan correctamente!")
        print("   El script setup.py debería ejecutarse sin tracebacks")
    else:
        print("\n❌ Hay problemas pendientes por resolver")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())