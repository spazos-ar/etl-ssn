#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para probar que las leyendas innecesarias fueron eliminadas correctamente.
"""

def test_removed_messages():
    """Verifica que los mensajes eliminados no estén en el código."""
    
    setup_py_path = "setup.py"
    
    print("🧪 === VERIFICANDO ELIMINACIÓN DE LEYENDAS ===\n")
    
    with open(setup_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Mensajes que deben haber sido eliminados
    removed_messages = [
        "y reemplazar el archivo: upload/certs/ssn_cert_test_20250903.pem",
        "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser",
        "Para cambiar política de PowerShell",
        "O ejecute directamente con Python del entorno virtual",
        "Re-ejecutando script con el entorno virtual para configuración completa"
        # Nota: Eliminamos "Configuración completada exitosamente" porque el mensaje principal debe mantenerse
    ]
    
    all_good = True
    
    for i, message in enumerate(removed_messages, 1):
        if message in content:
            print(f"❌ {i}. Mensaje aún presente: '{message[:50]}...'")
            all_good = False
        else:
            print(f"✅ {i}. Mensaje eliminado correctamente: '{message[:50]}...'")
    
    print(f"\n📋 === RESUMEN ===")
    if all_good:
        print("🎉 ¡Todas las leyendas innecesarias fueron eliminadas correctamente!")
        return True
    else:
        print("⚠️  Algunas leyendas aún están presentes en el código")
        return False

def test_essential_messages_remain():
    """Verifica que los mensajes esenciales permanezcan."""
    
    setup_py_path = "setup.py"
    
    print("\n🧪 === VERIFICANDO MENSAJES ESENCIALES ===\n")
    
    with open(setup_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Mensajes que deben permanecer
    essential_messages = [
        "Configuración inicial del proyecto ETL-SSN",
        "Creación del entorno virtual Python",
        "Instalación de dependencias",
        "Configuración de credenciales SSN", 
        "Configuración del certificado de seguridad",
        "Verificación de la configuración",
        "¡Configuración completada exitosamente!"
    ]
    
    all_present = True
    
    for i, message in enumerate(essential_messages, 1):
        if message in content:
            print(f"✅ {i}. Mensaje esencial presente: '{message[:50]}...'")
        else:
            print(f"❌ {i}. Mensaje esencial faltante: '{message[:50]}...'")
            all_present = False
    
    print(f"\n📋 === RESUMEN ===")
    if all_present:
        print("✅ Todos los mensajes esenciales están presentes")
        return True
    else:
        print("❌ Algunos mensajes esenciales faltan")
        return False

if __name__ == "__main__":
    print("🔧 === VERIFICACIÓN DE LIMPIEZA DE SETUP.PY ===\n")
    
    test1_ok = test_removed_messages()
    test2_ok = test_essential_messages_remain()
    
    if test1_ok and test2_ok:
        print("\n🎉 ¡Limpieza de setup.py completada exitosamente!")
        print("   El script ahora es más limpio y menos redundante")
    else:
        print("\n⚠️  Hay problemas pendientes por resolver")