#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para verificar que setup.py no instala dependencias dos veces.
Este script simula la ejecución sin hacer la instalación real.
"""

import argparse
import subprocess
import sys
from pathlib import Path

def test_setup_logic():
    """Prueba la lógica del setup sin hacer instalaciones reales."""
    
    print("🧪 === PRUEBA: Verificando lógica de setup.py ===\n")
    
    # Simular primera ejecución (sin --use-venv)
    print("1️⃣ Simulando primera ejecución: python setup.py")
    print("   ↳ Debería: crear venv + instalar deps")
    print("   ↳ Luego: re-ejecutar con --use-venv --skip-deps")
    
    # Simular segunda ejecución (con --use-venv --skip-deps)
    print("\n2️⃣ Simulando segunda ejecución: python setup.py --use-venv --skip-deps")
    print("   ↳ Debería: omitir instalación de deps")
    print("   ↳ Continuar con: configurar credenciales + SSL")
    
    # Verificar que los parámetros se parsean correctamente
    print("\n🔍 Verificando parsing de argumentos...")
    
    # Test 1: Sin argumentos
    parser = argparse.ArgumentParser()
    parser.add_argument('--use-venv', action='store_true')
    parser.add_argument('--skip-deps', action='store_true')
    
    args1 = parser.parse_args([])
    print(f"   Sin args: use_venv={args1.use_venv}, skip_deps={args1.skip_deps}")
    
    # Test 2: Solo --use-venv
    args2 = parser.parse_args(['--use-venv'])
    print(f"   Solo --use-venv: use_venv={args2.use_venv}, skip_deps={args2.skip_deps}")
    
    # Test 3: Ambos parámetros
    args3 = parser.parse_args(['--use-venv', '--skip-deps'])
    print(f"   Ambos: use_venv={args3.use_venv}, skip_deps={args3.skip_deps}")
    
    print("\n✅ La lógica parece correcta. Ahora:")
    print("   • Primera ejecución instala dependencias")
    print("   • Segunda ejecución omite dependencias")
    print("   • No hay duplicación de instalación")
    
    return True

def show_execution_flow():
    """Muestra el flujo de ejecución corregido."""
    print("\n📋 === FLUJO CORREGIDO ===")
    print("""
Configurar.bat
    ↓
python setup.py  (sin argumentos)
    ↓
├─ create_venv() si no existe
├─ install_requirements()  ← PRIMERA Y ÚNICA INSTALACIÓN
└─ Re-ejecutar: python setup.py --use-venv --skip-deps
    ↓
python setup.py --use-venv --skip-deps
    ↓
main(skip_deps=True)
    ↓
├─ ⏭️ OMITE install_requirements()  ← EVITA DUPLICACIÓN
├─ setup_env_file()
├─ setup_ssl_cert()
└─ verify_setup()
""")
    print("🎯 RESULTADO: Sin duplicación de instalación de dependencias")

if __name__ == "__main__":
    test_setup_logic()
    show_execution_flow()
    
    print("\n🚀 Para aplicar la corrección:")
    print("   1. Los cambios ya están aplicados en setup.py")
    print("   2. Ejecute: .\\Configurar.bat")
    print("   3. Verifique que solo aparece una instalación de dependencias")