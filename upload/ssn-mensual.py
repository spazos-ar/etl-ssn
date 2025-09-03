#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para la carga y procesamiento de datos mensuales al sistema de la SSN.

Este script maneja el proceso completo de carga de información mensual a la Superintendencia
de Seguros de la Nación (SSN). Soporta las siguientes operaciones:

1. Envío de datos:
   - Validación del formato JSON
   - Envío de datos de inversiones mensuales
   - Confirmación de la entrega
   - Movimiento automático de archivos procesados

2. Gestión de entregas:
   - Consulta de estado (--query-month)
   - Solicitud de rectificativas (--fix-month)
   - Envío de meses vacíos (--empty-month)
   - Confirmación de entregas (--confirm-month)

Uso:
    python ssn-mensual.py [--config CONFIG] [opciones] [data_file]

Argumentos:
    data_file: Archivo JSON con los datos a enviar
    --config: Ruta al archivo de configuración (opcional)
    --confirm-month: Confirma la entrega y mueve el archivo a processed/
    --fix-month YYYY-MM: Solicita rectificativa para un mes
    --query-month YYYY-MM: Consulta estado de un mes
    --empty-month YYYY-MM: Envía un mes sin inversiones

El archivo de configuración (config.json) debe contener:
    {
        "baseUrl": "URL base del servicio",
        "endpoints": {
            "login": "ruta del endpoint de login",
            "entregaMensual": "ruta de entrega mensual",
            "confirmarEntregaMensual": "ruta de confirmación"
        },
        "debug": boolean para modo debug
    }

Variables de entorno requeridas (.env):
    SSN_USER: Usuario para autenticación
    SSN_PASSWORD: Contraseña del usuario
    SSN_COMPANY: Código de la compañía

Autor: G. Casanova
Fecha: Septiembre 2025
"""

import os
import sys
import platform

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

import sys
import json
import os
import argparse
import shutil
from dotenv import load_dotenv
from pathlib import Path
import re
from lib.ssn_client import SSNClient  # TODO: Actualizar a ssn-client en v2.0

def show_error_message(error_message):
    """Muestra un mensaje de error destacado y bien formateado."""
    print("\n" + "="*80)
    print("|| ERROR:")
    print("||")
    # Dividir el mensaje en líneas para ajustar al ancho
    for line in error_message.split('\n'):
        if line.strip():
            # Dividir líneas muy largas
            while len(line) > 74:  # 80 - 4 (para "|| ") - 2 (margen)
                print(f"|| {line[:74]}")
                line = line[74:]
            if line:
                print(f"|| {line}")
        else:
            print("||")
    print("||")
    print("="*80)
    print()  # Línea adicional después del cuadro de error

env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

def get_args():
    parser = argparse.ArgumentParser(description='Envía datos mensuales a la SSN')
    parser.add_argument('--config', help='Ruta al archivo de configuración')
    parser.add_argument('--test', action='store_true', help='Prueba la conexión SSL con el servidor')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--confirm-month', action='store_true', help='Confirma la entrega mensual y mueve el archivo a processed/')
    group.add_argument('--fix-month', metavar='YYYY-MM', help='Pide rectificativa de un mes específico (formato YYYY-MM)')
    group.add_argument('--query-month', metavar='YYYY-MM', help='Consulta el estado de un mes específico (formato YYYY-MM)')
    group.add_argument('--empty-month', metavar='YYYY-MM', help='Envía un mes vacío sin inversiones (formato YYYY-MM)')

    parser.add_argument('data_file', nargs='?', help='Archivo JSON con los datos a enviar (no requerido con --fix-month, --query-month, --empty-month o --test)')
    args = parser.parse_args()

    if args.test:
        if args.data_file:
            parser.error("No se debe especificar data_file cuando se usa --test")
    elif args.fix_month or args.query_month or args.empty_month:
        if args.data_file:
            parser.error("No se debe especificar data_file cuando se usa --fix-month, --query-month o --empty-month")
        if not re.match(r'^\d{4}-\d{2}$', args.fix_month or args.query_month or args.empty_month):
            parser.error("El formato debe ser YYYY-MM (ejemplo: 2025-01)")
    elif not args.data_file:
        parser.error("Debe especificarse el archivo de datos a enviar")

    if args.config:
        if os.path.isfile(args.config):
            config_path = args.config
        else:
            # Si la ruta es relativa, buscar en la carpeta del script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            alt_path = os.path.join(script_dir, args.config)
            if os.path.isfile(alt_path):
                config_path = alt_path
            else:
                raise FileNotFoundError(f"El archivo de configuración '{args.config}' no existe ni en el directorio actual ni en '{alt_path}'.")
    else:
        # Si no se especifica, usar el config-mensual.json en el directorio del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config-mensual.json')
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"No se encuentra el archivo de configuración por defecto en '{config_path}'")
    return config_path, args.data_file, args.confirm_month, args.fix_month, args.query_month, args.empty_month, args.test

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def show_startup_banner(config):
    """Muestra el banner inicial con información del script y ambiente."""
    env = config.get('environment', 'prod').upper()
    base_url = config.get('baseUrl', 'URL no configurada')
    
    print("=" * 60)
    print("📊 SCRIPT DE CARGA MENSUAL SSN")
    print("=" * 60)
    print(f"🏢 Tipo de entrega: MENSUAL")
    print(f"🌐 Ambiente: {env}")
    print(f"🔗 Servidor: {base_url}")
    print(f"📅 Fecha: {os.environ.get('DATE', 'No disponible')}")
    print("-" * 60)

def authenticate(config):
    """Autentica con el servicio SSN usando el cliente HTTP."""
    try:
        with SSNClient(config, debug=config.get('debug', False)) as client:
            return client.authenticate()
    except Exception as e:
        raise RuntimeError(f"Error de autenticación: {str(e)}")


def enviar_entrega(token, data, config):
    # Procesa y valida cada registro en STOCKS
    for reg in data.get("STOCKS", []):
        # Corrige FECHAPASEVT y PRECIOPASEVT
        if reg.get("TIPOESPECIE") not in ["TP", "ON"] or reg.get("TIPOVALUACION") != "T":
            reg["FECHAPASEVT"] = ""
            reg["PRECIOPASEVT"] = ""
            
        # Validación de cantidades según tipo de especie
        tipo_especie = reg.get("TIPOESPECIE", "")
        
        # Asegurarse de que los campos numéricos sean números y no strings vacíos
        if reg.get("CANTIDADDEVENGADOESPECIES") == "":
            reg["CANTIDADDEVENGADOESPECIES"] = 0
        if reg.get("CANTIDADPERCIBIDOESPECIES") == "":
            reg["CANTIDADPERCIBIDOESPECIES"] = 0
            
        cant_devengada = float(reg.get("CANTIDADDEVENGADOESPECIES", 0))
        cant_percibida = float(reg.get("CANTIDADPERCIBIDOESPECIES", 0))
        
        # Para especies tipo TP, AC, FF aseguramos que las cantidades sean números positivos
        if tipo_especie in ["TP", "AC", "FF"]:
            # Si las cantidades son muy grandes o negativas, las reseteamos a 0
            if cant_devengada < 0 or cant_devengada > 1e9:
                reg["CANTIDADDEVENGADOESPECIES"] = 0
            if cant_percibida < 0 or cant_percibida > 1e9:
                reg["CANTIDADPERCIBIDOESPECIES"] = 0

    try:
        print("📤 Enviando entrega mensual a la SSN...")
        with SSNClient(config, debug=config.get('debug', False)) as client:
            client.token = token
            client.post("entregaMensual", data)
            print("✅ Entrega mensual enviada correctamente")
    except Exception as e:
        raise RuntimeError(f"Error al enviar entrega mensual: {str(e)}")

def confirmar_entrega(token, company, cronograma, config):
    try:
        print("📋 Confirmando entrega mensual...")
        with SSNClient(config, debug=config.get('debug', False)) as client:
            client.token = token
            payload = {
                "CODIGOCOMPANIA": company,
                "TIPOENTREGA": "MENSUAL",
                "CRONOGRAMA": cronograma
            }
            client.post("confirmarEntregaMensual", payload)
            print("✅ Entrega mensual confirmada correctamente")
    except Exception as e:
        raise RuntimeError(f"Error al confirmar: {str(e)}")

def mover_archivo_procesado(data_file):
    # Mueve el archivo JSON procesado a data/processed/monthly/
    base_dir = os.path.dirname(data_file)
    # Si el archivo está en 'data', mover a 'data/processed/monthly/'
    if os.path.basename(base_dir) == 'data':
        processed_dir = os.path.join(base_dir, 'processed', 'monthly')
    else:
        # Si está en otro lado, igual crear la ruta relativa a data/processed/monthly
        processed_dir = os.path.join('data', 'processed', 'monthly')
    os.makedirs(processed_dir, exist_ok=True)
    archivo_destino = os.path.join(processed_dir, os.path.basename(data_file))
    shutil.move(data_file, archivo_destino)
    print(f"📁 Archivo movido exitosamente a: {archivo_destino}")

def fix_mes(token, company, cronograma, config):
    """Solicita rectificativa mensual usando PUT con el body requerido por la SSN."""
    try:
        print(f"🔄 Solicitando rectificativa para el mes {cronograma}...")
        with SSNClient(config, debug=config.get('debug', False)) as client:
            client.token = token
            payload = {
                "cronograma": cronograma,
                "codigoCompania": company,
                "tipoEntrega": "Mensual"
            }
            if config.get('debug', False):
                client.logger.debug(f"JSON de rectificativa mensual (PUT): {json.dumps(payload, indent=2)}")
                
            client.put("entregaMensual", payload)
            print(f"✅ Rectificativa del mes {cronograma} solicitada exitosamente")
            return True
    except Exception as e:
        raise RuntimeError(f"Error al pedir rectificativa mensual: {str(e)}")

def query_mes(token, company, cronograma, config):
    """Consulta el estado de un mes específico.
    
    Args:
        token: Token de autenticación
        company: Código de la compañía
        cronograma: Mes a consultar (formato YYYY-MM)
        config: Configuración del script
    """
    try:
        print(f"📊 Consultando estado del mes {cronograma}...")
        with SSNClient(config, debug=config.get('debug', False)) as client:
            client.token = token
            params = {
                "codigoCompania": company,
                "tipoEntrega": "Mensual",
                "cronograma": cronograma
            }
            
            # Para debugging
            if config.get('debug', False):
                client.logger.debug(f"Parámetros: {json.dumps(params, indent=2)}")
            
            response = client.get("entregaMensual", params=params)
            print(f"Estado del mes {cronograma}:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return True
    except Exception as e:
        raise RuntimeError(f"Error al consultar mes: {str(e)}")

def test_ssl_connection(config):
    """Prueba la conexión SSL con el servidor."""
    try:
        with SSNClient(config, debug=config.get('debug', False)) as client:
            # La inicialización del cliente ya prueba la conexión SSL
            # Hacer un test simple adicional para confirmar que funciona
            base_url = config.get('baseUrl', '')
            if config.get('debug', False):
                print(f"DEBUG: Cliente creado para {base_url}")
            if not config.get('debug', False):
                print("✅ Conexión SSL verificada correctamente")
            return True
    except Exception as e:
        print(f"❌ Error en la prueba de conexión SSL: {str(e)}")
        raise RuntimeError(f"Error en la prueba de conexión SSL: {str(e)}")

def main():
    config_path, data_file, confirm, fix, query, empty, test = get_args()
    config = load_config(config_path)

    # Mostrar banner de inicio (excepto para tests SSL)
    if not test:
        show_startup_banner(config)

    if test:
        test_ssl_connection(config)
        return

    token = authenticate(config)
    company = os.getenv('SSN_COMPANY')

    if query:
        query_mes(token, company, query, config)
        return

    if fix:
        fix_mes(token, company, fix, config)
        return

    if data_file:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not all(k in data for k in ("CRONOGRAMA", "TIPOENTREGA", "STOCKS", "CODIGOCOMPANIA")):
            raise ValueError("El JSON debe contener CRONOGRAMA, TIPOENTREGA, CODIGOCOMPANIA y STOCKS")
        enviar_entrega(token, data, config)
        if confirm:
            confirmar_entrega(token, company, data['CRONOGRAMA'], config)
            mover_archivo_procesado(data_file)

if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        show_error_message(f"Error de validación: {str(e)}")
        sys.exit(1)
    except FileNotFoundError as e:
        show_error_message(f"Archivo no encontrado: {str(e)}")
        sys.exit(1)
    except RuntimeError as e:
        show_error_message(str(e))
        sys.exit(1)
    except Exception as e:
        show_error_message(f"Error inesperado: {str(e)}")
        sys.exit(1)
