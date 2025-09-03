#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para mostrar los mensajes de éxito
"""

def show_success_message(message="Operación completada exitosamente!"):
    """Muestra un mensaje de éxito destacado y bien formateado."""
    print("\n" + "="*80)
    print("|| ✅ ÉXITO:")
    print("||")
    print(f"|| {message}")
    print("||")
    print("="*80)
    print()  # Línea adicional después del cuadro de éxito

def show_startup_banner():
    """Muestra un banner básico."""
    print("=" * 60)
    print("📊 SCRIPT DE PRUEBA SSN")
    print("=" * 60)
    print("🏢 Tipo de entrega: TEST")
    print("🌐 Ambiente: LOCAL")
    print("-" * 60)

if __name__ == "__main__":
    show_startup_banner()
    print("🔐 Simulando carga de certificados...")
    print("🔒 Simulando conexión SSL...")
    print("🔑 Simulando autenticación...")
    print("📤 Simulando envío de datos...")
    show_success_message("Entrega de prueba completada exitosamente!")
