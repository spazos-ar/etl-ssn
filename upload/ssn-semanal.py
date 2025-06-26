#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para la carga y confirmación de datos semanales al sistema de la SSN.

Este script maneja el proceso de carga de información semanal a la Superintendencia
de Seguros de la Nación (SSN). Tiene dos funciones principales:
1. Enviar los datos de operaciones semanales al servidor de la SSN
2. Confirmar la entrega semanal (opcional, usando --confirm-week)

El script soporta las siguientes operaciones:
- Autenticación en el sistema SSN
- Envío de datos de operaciones semanales
- Confirmación de la entrega semanal
- Movimiento automático de archivos procesados

Uso:
    python ssn-semanal.py [--config CONFIG] [--confirm-week] data_file

Argumentos:
    data_file: Archivo JSON con los datos a enviar
    --config: Ruta al archivo de configuración (opcional)
    --confirm-week: Confirma la entrega y mueve el archivo a processed/ (opcional)

El archivo de configuración (config.json) debe contener:
    {
        "baseUrl": "URL base del servicio",
        "endpoints": {
            "login": "ruta del endpoint de login",
            "entregaSemanal": "ruta del endpoint de entrega",
            "confirmarEntregaSemanal": "ruta del endpoint de confirmación"
        },
        "retries": número de reintentos,
        "debug": boolean para modo debug
    }

Variables de entorno requeridas (.env):
    SSN_USER: Usuario para autenticación
    SSN_PASSWORD: Contraseña del usuario
    SSN_COMPANY: Código de la compañía

Autor: [Tu Nombre]
Fecha: Mayo 2025
"""

import sys
import json
import requests
import os
import argparse
import shutil
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import urljoin
import re
import logging

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

def get_config_path():
    """Obtiene la ruta del archivo de configuración y procesa argumentos.
    
    Returns:
        tuple: (config_path, data_path, confirm_week, fix_week, query_week, empty_week)
            config_path: Ruta al archivo de configuración
            data_path: Ruta al archivo de datos (None si se usa --fix-week o --query-week o --empty-week)
            confirm_week: Bool indicando si se debe confirmar la semana
            fix_week: String con la semana a corregir (formato YYYY-WW)
            query_week: String con la semana a consultar (formato YYYY-WW)
            empty_week: String con la semana a enviar vacía (formato YYYY-WW)
    """
    parser = argparse.ArgumentParser(description='Envía datos semanales a la SSN')
    parser.add_argument('--config', help='Ruta al archivo de configuración', default='config-semanal.json')
    
    # Grupo mutuamente excluyente para los modos de operación
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--confirm-week', action='store_true', 
                      help='Confirma la entrega semanal y mueve el archivo a processed/')
    group.add_argument('--fix-week', metavar='YYYY-WW',
                      help='Pide rectificativa de una semana específica (formato YYYY-WW)')
    group.add_argument('--query-week', metavar='YYYY-WW',
                      help='Consulta el estado de una semana específica (formato YYYY-WW)')
    group.add_argument('--empty-week', metavar='YYYY-WW',
                      help='Envía una semana vacía sin operaciones (formato YYYY-WW)')
    
    # El archivo de datos es obligatorio solo si no se usa --fix-week o --query-week o --empty-week
    parser.add_argument('data_file', nargs='?', 
                       help='Archivo JSON con los datos a enviar (no requerido con --fix-week, --query-week o --empty-week)')
    
    args = parser.parse_args()
    
    # Validar combinación de argumentos
    if args.fix_week or args.query_week or args.empty_week:
        if args.data_file:
            parser.error("El argumento 'data_file' no debe especificarse cuando se usa --fix-week, --query-week o --empty-week")
        # Validar formato de semana (YYYY-WW)
        week_arg = args.fix_week or args.query_week or args.empty_week
        if not re.match(r'^\d{4}-\d{2}$', week_arg):
            parser.error("El formato de semana debe ser YYYY-WW (ejemplo: 2025-33)")
        año, semana = map(int, week_arg.split('-'))
        if not (2000 <= año <= 2100 and 1 <= semana <= 53):
            parser.error("Valores inválidos. El año debe estar entre 2000 y 2100, y la semana entre 1 y 53")
    elif not args.data_file:
        parser.error("Se requiere el archivo de datos cuando no se usa --fix-week, --query-week o --empty-week")
    
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
        # Si no se especifica, usar el config.json en el directorio del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config-semanal.json')
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"No se encuentra el archivo de configuración por defecto en '{config_path}'")
    
    return config_path, args.data_file, args.confirm_week, args.fix_week, args.query_week, args.empty_week

def load_config(config_path):
    """Carga la configuración desde un archivo JSON.
    
    Args:
        config_path (str): Ruta al archivo de configuración
    
    Returns:
        dict: Configuración cargada
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Validar configuración mínima requerida
    required_fields = ['baseUrl', 'endpoints']
    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        raise ValueError(f"Campos requeridos faltantes en config.json: {', '.join(missing_fields)}")
    
    return config

def setup_logging(debug_mode):
    """Configura el sistema de logging.
    
    Args:
        debug_mode (bool): Si True, establece el nivel de logging a DEBUG
    """
    level = logging.DEBUG if debug_mode else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def build_url(config, endpoint):
    """Construye una URL completa para un endpoint.
    
    Args:
        config (dict): Configuración cargada del archivo JSON
        endpoint (str): Nombre del endpoint en la configuración
    
    Returns:
        str: URL completa
    """
    if endpoint not in config['endpoints']:
        raise ValueError(f"Endpoint '{endpoint}' no encontrado en la configuración")
    
    return config['baseUrl'].rstrip('/') + config['endpoints'][endpoint]

def authenticate(config, debug_enabled):
    """
    Autenticación en el servicio de SSN.
    :param config: Diccionario con la configuración operativa.
    :param debug_enabled: Booleano que indica si la depuración está habilitada.
    :return: Token de autenticación.
    """
    # Obtener credenciales desde variables de entorno
    user = os.getenv('SSN_USER')
    password = os.getenv('SSN_PASSWORD')
    company = os.getenv('SSN_COMPANY')

    if not all([user, password, company]):
        raise RuntimeError("Faltan variables de entorno. Asegúrate de que SSN_USER, SSN_PASSWORD y SSN_COMPANY estén definidas en el archivo .env")

    # Construir URL completa desde la configuración
    url = build_url(config, "login")
    payload = {
        "USER": user,
        "CIA": company,
        "PASSWORD": password
    }
    headers = {"Content-Type": "application/json"}
    
    if debug_enabled:
        print(f"DEBUG: Intentando login en URL: {url}")
        
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        data = response.json()
        token = data.get("TOKEN") or data.get("token")

        # DEBUG: Imprimir la respuesta completa
        if debug_enabled:
            print("DEBUG: Respuesta de autenticación:\n\r", json.dumps(data, indent=2)) 
        
        if not token:
            raise RuntimeError("No se encontró el TOKEN en la respuesta.")
        return token
    else:
        raise RuntimeError(f"Login fallido: {response.status_code} - {response.text}")

def enviar_entrega(token, company, records, cronograma, attempt, debug_enabled, config):
    # Construir URL completa desde la configuración
    url = build_url(config, "entregaSemanal")
    headers = {
        "Content-Type": "application/json",
        "Token": token
    }

    # Validar y agregar CODIGOCOMPANIA a cada registro
    for record in records:
        if not record.get("CODIGOCOMPANIA"):
            record["CODIGOCOMPANIA"] = company

    # Construir el JSON final sin la sección HEADER
    payload = {
        "CODIGOCOMPANIA": company,
        "TIPOENTREGA": "SEMANAL",
        "CRONOGRAMA": cronograma,
        "OPERACIONES": records
    }

    # Depurar el JSON enviado solo si la depuración está habilitada y es el primer reintento
    if debug_enabled and attempt == 1:
        print("DEBUG: JSON enviado:\n\r", json.dumps(payload, indent=2))

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(json.dumps({
            "type": "STATE",
            "value": {"last_sent": cronograma}
        }))
    else:
        # Extraer y mostrar errores de manera clara
        try:
            response_json = response.json()
            error_details = (
                response_json.get("errors") or
                response_json.get("message") or
                response_json.get("detail") or
                response.text
            )
            error_message = error_details if isinstance(error_details, str) else json.dumps(error_details, indent=2)
        except Exception as e:
            error_message = f"No se pudo procesar la respuesta del servidor: {str(e)}\nRespuesta completa: {response.text}"
        
        # Mostrar la respuesta del servidor solo en el primer intento fallido
        if attempt == 1:
            print("DEBUG: Respuesta del servidor:\n\r", response.text)
        raise RuntimeError(f"Error al enviar: {response.status_code} - {error_message}")

def confirmar_entrega(token, company, cronograma, attempt, debug_enabled, config):
    """Confirma la entrega semanal en el sistema de la SSN."""
    # Construir URL completa desde la configuración
    url = build_url(config, "confirmarEntregaSemanal")
    headers = {
        "Content-Type": "application/json",
        "Token": token
    }

    payload = {
        "CODIGOCOMPANIA": company,
        "TIPOENTREGA": "SEMANAL",
        "CRONOGRAMA": cronograma
    }

    if debug_enabled and attempt == 1:
        print("DEBUG: JSON de confirmación:\n\r", json.dumps(payload, indent=2))

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print("Entrega semanal confirmada exitosamente.")
        return True
    else:
        try:
            response_json = response.json()
            error_details = (
                response_json.get("errors") or
                response_json.get("message") or
                response_json.get("detail") or
                response.text
            )
            error_message = error_details if isinstance(error_details, str) else json.dumps(error_details, indent=2)
        except Exception as e:
            error_message = f"No se pudo procesar la respuesta del servidor: {str(e)}\nRespuesta completa: {response.text}"
        
        if attempt == 1:
            print("DEBUG: Respuesta del servidor (confirmación):\n\r", response.text)
        raise RuntimeError(f"Error al confirmar: {response.status_code} - {error_message}")

def mover_archivo_procesado(data_file):
    """Mueve el archivo JSON procesado a la carpeta processed/weekly/."""
    try:
        # Crear directorio processed/weekly/ si no existe
        processed_dir = os.path.join(os.path.dirname(data_file), "processed", "weekly")
        os.makedirs(processed_dir, exist_ok=True)

        # Mover el archivo
        archivo_destino = os.path.join(processed_dir, os.path.basename(data_file))
        shutil.move(data_file, archivo_destino)
        print(f"Archivo movido exitosamente a: {archivo_destino}")
    except Exception as e:
        print(f"Error al mover el archivo: {str(e)}", file=sys.stderr)
        raise

def fix_semana(token, company, cronograma, attempt, debug_enabled, config):
    """Envía una corrección para una semana específica.
    
    Args:
        token: Token de autenticación
        company: Código de la compañía
        cronograma: Semana a corregir (formato YYYY-WW)
        attempt: Número de intento actual
        debug_enabled: Si está en modo debug
        config: Configuración del script
    
    Raises:
        RuntimeError: Si hay un error al procesar la solicitud
    """
    url = build_url(config, "entregaSemanal")
    headers = {
        "Content-Type": "application/json",
        "Token": token
    }

    payload = {
        "CODIGOCOMPANIA": company,
        "TIPOENTREGA": "SEMANAL",
        "CRONOGRAMA": cronograma
    }

    if debug_enabled and attempt == 1:
        print("DEBUG: JSON de corrección de semana:\n\r", json.dumps(payload, indent=2))

    response = requests.post(url, json=payload, headers=headers)
    
    # Procesar respuesta
    try:
        response_json = response.json()
    except Exception:
        response_json = {}

    # En caso de éxito
    if response.status_code == 200:
        print(f"Semana {cronograma} corregida exitosamente.")
        return True
        
    # En caso de error
    error_message = (
        response_json.get("message") or  # Mensaje de error principal
        response_json.get("detail") or   # Detalle del error
        response_json.get("errors") or   # Lista de errores
        response.text                    # Respuesta cruda como último recurso
    )
    
    # Si el error_message es una lista o diccionario, convertirlo a string
    if not isinstance(error_message, str):
        error_message = json.dumps(error_message, indent=2, ensure_ascii=False)
    
    # En modo debug, mostrar la respuesta completa
    if debug_enabled and attempt == 1:
        print("DEBUG: Respuesta del servidor:\n\r", response.text)
    
    # Manejar códigos de error específicos
    if response.status_code == 409:
        raise RuntimeError(error_message)
    elif response.status_code == 401:
        raise RuntimeError("Error de autenticación. Verifique sus credenciales.")
    elif response.status_code == 403:
        raise RuntimeError("No tiene permisos para realizar esta operación.")
    else:
        raise RuntimeError(f"Error al corregir semana: {error_message}")

def query_semana(token, company, cronograma, attempt, debug_enabled, config):
    """Consulta el estado de una semana específica.
    
    Args:
        token: Token de autenticación
        company: Código de la compañía
        cronograma: Semana a consultar (formato YYYY-WW)
        attempt: Número de intento actual
        debug_enabled: Si está en modo debug
        config: Configuración del script
    """
    url = build_url(config, "entregaSemanal")
    headers = {
        "Content-Type": "application/json",
        "Token": token
    }    # Construir query params usando camelCase como especifica la documentación
    params = {
        "codigoCompania": company,
        "tipoEntrega": "SEMANAL",
        "cronograma": cronograma
    }

    if debug_enabled and attempt == 1:
        print("DEBUG: Consultando semana con parámetros:\n\r", json.dumps(params, indent=2))

    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Estado de la semana {cronograma}:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        except json.JSONDecodeError:
            print(f"La respuesta no es un JSON válido: {response.text}")
            raise RuntimeError("Error al procesar la respuesta del servidor")
    else:
        try:
            response_json = response.json()
            error_details = (
                response_json.get("errors") or
                response_json.get("message") or
                response_json.get("detail") or
                response.text
            )
            error_message = error_details if isinstance(error_details, str) else json.dumps(error_details, indent=2)
        except Exception as e:
            error_message = f"No se pudo procesar la respuesta del servidor: {str(e)}\nRespuesta completa: {response.text}"
        
        if attempt == 1:
            print("DEBUG: Respuesta del servidor:\n\r", response.text)
        raise RuntimeError(f"Error al consultar semana: {response.status_code} - {error_message}")

def load_data(data_file):
    """Carga los datos desde un archivo JSON.
    
    Args:
        data_file (str): Ruta al archivo de datos
    
    Returns:
        dict: Datos cargados del archivo
    
    Raises:
        FileNotFoundError: Si el archivo no existe
        json.JSONDecodeError: Si el archivo no es un JSON válido
        ValueError: Si faltan campos requeridos en los datos
    """
    if not os.path.isfile(data_file):
        raise FileNotFoundError(f"No se encuentra el archivo de datos: {data_file}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validar estructura mínima requerida
    if not isinstance(data, dict):
        raise ValueError("El archivo debe contener un objeto JSON")
    
    required_fields = ['CRONOGRAMA', 'OPERACIONES']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Campos requeridos faltantes en el archivo de datos: {', '.join(missing_fields)}")
    
    return data

def send_empty_week(token, company, cronograma, attempt, debug_enabled, config):
    """Envía una semana sin operaciones.
    
    Args:
        token: Token de autenticación
        company: Código de la compañía
        cronograma: Semana a enviar (formato YYYY-WW)
        attempt: Número de intento actual
        debug_enabled: Si está en modo debug
        config: Configuración del script
    
    Returns:
        bool: True si la operación fue exitosa

    Raises:
        RuntimeError: Si hay un error al procesar la solicitud
    """
    url = build_url(config, "entregaSemanal")
    headers = {
        "Content-Type": "application/json",
        "Token": token
    }

    # Crear payload con orden específico de campos
    from collections import OrderedDict
    payload = OrderedDict([
        ("CRONOGRAMA", cronograma),
        ("CODIGOCOMPANIA", company),
        ("TIPOENTREGA", "SEMANAL"),
        ("OPERACIONES", [])
    ])

    if debug_enabled and attempt == 1:
        print("DEBUG: JSON de semana vacía:\n\r", json.dumps(payload, indent=2))

    response = requests.post(url, json=payload, headers=headers)
    
    # Procesar respuesta
    try:
        response_json = response.json()
    except Exception:
        response_json = {}

    # En caso de éxito
    if response.status_code == 200:
        print(f"Semana vacía {cronograma} enviada exitosamente.")
        return True
        
    # En caso de error
    error_message = (
        response_json.get("message") or
        response_json.get("detail") or
        response_json.get("errors") or
        response.text
    )
    
    if not isinstance(error_message, str):
        error_message = json.dumps(error_message, indent=2, ensure_ascii=False)
    
    if debug_enabled and attempt == 1:
        print("DEBUG: Respuesta del servidor:\n\r", response.text)
    
    if response.status_code == 409:
        raise RuntimeError(error_message)
    elif response.status_code == 401:
        raise RuntimeError("Error de autenticación. Verifique sus credenciales.")
    elif response.status_code == 403:
        raise RuntimeError("No tiene permisos para realizar esta operación.")
    else:
        raise RuntimeError(f"Error al enviar semana vacía: {error_message}")

def main():
    """Función principal del script."""
    config = None  # Inicializar para evitar UnboundLocalError
    try:
        config_path, data_file, confirm_week, fix_week, query_week, empty_week = get_config_path()
        config = load_config(config_path)
        
        # Configurar logging
        setup_logging(config.get('debug', False))
        
        # Obtener el código de compañía desde las variables de entorno
        company = os.getenv('SSN_COMPANY')
        if not company:
            raise RuntimeError("Falta la variable de entorno SSN_COMPANY")
        
        # Iniciar sesión
        token = authenticate(config, config.get('debug', False))
        
        # Número máximo de reintentos (por defecto 3 si no está especificado)
        max_retries = config.get('retries', 3)
        
        if query_week:
            for attempt in range(1, max_retries + 1):
                try:
                    if query_semana(token, company, query_week, attempt, config.get('debug', False), config):
                        break
                except RuntimeError as e:
                    if attempt == max_retries:
                        raise
                    print(f"Intento {attempt} fallido: {str(e)}")
        elif fix_week:
            for attempt in range(1, max_retries + 1):
                try:
                    if fix_semana(token, company, fix_week, attempt, config.get('debug', False), config):
                        break
                except RuntimeError as e:
                    if attempt == max_retries:
                        raise
                    print(f"Intento {attempt} fallido: {str(e)}")
        elif empty_week:
            for attempt in range(1, max_retries + 1):
                try:
                    if send_empty_week(token, company, empty_week, attempt, config.get('debug', False), config):
                        break
                except RuntimeError as e:
                    if attempt == max_retries:
                        raise
                    print(f"Intento {attempt} fallido: {str(e)}")
        else:
            # Cargar datos desde el archivo JSON
            data = load_data(data_file)
            
            # Intentar enviar los datos con reintentos
            for attempt in range(1, max_retries + 1):
                try:
                    if enviar_entrega(token, company, data["OPERACIONES"], data["CRONOGRAMA"], 
                                    attempt, config.get('debug', False), config):
                        break
                except RuntimeError as e:
                    if attempt == max_retries:
                        raise
                    print(f"Intento {attempt} fallido: {str(e)}")
            
            # Si se solicitó confirmar la entrega
            if confirm_week:
                for attempt in range(1, max_retries + 1):
                    try:
                        if confirmar_entrega(token, company, data["CRONOGRAMA"], 
                                          attempt, config.get('debug', False), config):
                            # Si la confirmación fue exitosa, mover el archivo
                            mover_archivo_procesado(data_file)
                            break
                    except RuntimeError as e:
                        if attempt == max_retries:
                            raise
                        print(f"Intento {attempt} fallido: {str(e)}")
    
    except ValueError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except (requests.exceptions.HTTPError, RuntimeError) as e:
        # Errores esperados del API o de validación
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Errores inesperados
        if config and config.get('debug', False):
            import traceback
            traceback.print_exc()
        else:
            print(f"\nError inesperado: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
