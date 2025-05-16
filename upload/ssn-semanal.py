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

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

def get_config_path():
    """Obtiene la ruta del archivo de configuración.
    
    Busca primero en los argumentos de línea de comando,
    si no encuentra usa el config.json en el directorio del script.
    """
    parser = argparse.ArgumentParser(description='Envía datos semanales a la SSN')
    parser.add_argument('--config', help='Ruta al archivo de configuración')
    parser.add_argument('--confirm-week', action='store_true', 
                       help='Confirma la entrega semanal y mueve el archivo a processed/')
    parser.add_argument('data_file', help='Archivo JSON con los datos a enviar')
    args = parser.parse_args()
    
    if args.config:
        if not os.path.isfile(args.config):
            raise FileNotFoundError(f"El archivo de configuración '{args.config}' no existe.")
        return args.config, args.data_file, args.confirm_week
        
    # Si no se especifica, usar el config.json en el directorio del script
    default_config = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.isfile(default_config):
        raise FileNotFoundError(f"No se encuentra el archivo de configuración por defecto en '{default_config}'")
    return default_config, args.data_file, args.confirm_week

def build_url(config, endpoint):
    """Construye una URL completa asegurándose que la concatenación sea correcta.
    
    Args:
        config: Diccionario con la configuración que contiene baseUrl y endpoints
        endpoint: Nombre del endpoint en la configuración
    Returns:
        str: URL completa
    """
    base_url = config["baseUrl"]
    if not base_url.endswith('/'):
        base_url += '/'
    return urljoin(base_url, config["endpoints"][endpoint].lstrip('/'))

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
    """Mueve el archivo JSON procesado a la carpeta processed/."""
    try:
        # Crear directorio processed/ si no existe
        processed_dir = os.path.join(os.path.dirname(data_file), "processed")
        os.makedirs(processed_dir, exist_ok=True)

        # Mover el archivo
        archivo_destino = os.path.join(processed_dir, os.path.basename(data_file))
        shutil.move(data_file, archivo_destino)
        print(f"Archivo movido exitosamente a: {archivo_destino}")
    except Exception as e:
        print(f"Error al mover el archivo: {str(e)}", file=sys.stderr)
        raise

def main():
    try:
        config_path, data_path, confirm_week = get_config_path()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(data_path):
        print(f"Error: El archivo de datos '{data_path}' no existe.", file=sys.stderr)
        sys.exit(1)

    # Cargar la configuración operativa
    with open(config_path, 'r') as config_file:
        config = json.load(config_file)
        
    # Validar la configuración
    required_config = ["baseUrl", "endpoints"]
    required_endpoints = ["login", "entregaSemanal", "confirmarEntregaSemanal"]
    
    if not all(key in config for key in required_config):
        raise ValueError(f"Faltan campos requeridos en la configuración: {', '.join(required_config)}")
    if not all(key in config["endpoints"] for key in required_endpoints):
        raise ValueError(f"Faltan endpoints requeridos en la configuración: {', '.join(required_endpoints)}")

    with open(data_path, 'r') as data_file:
        data = json.load(data_file)

    cronograma = data.get("CRONOGRAMA", "")
    if not cronograma:
        raise ValueError("El campo 'CRONOGRAMA' está vacío o no existe en el archivo JSON.")

    token = authenticate(config, config.get("debug", False))
    company = os.getenv('SSN_COMPANY')
    retries = config.get("retries", 4)
    debug_enabled = config.get("debug", False)

    # Proceso de envío y confirmación
    for attempt in range(1, retries + 1):
        try:
            # Enviar entrega
            enviar_entrega(token, company, data.get("OPERACIONES", []), cronograma, attempt, debug_enabled, config)
            print("Entrega completada exitosamente.")

            # Si se solicitó confirmar la entrega
            if confirm_week:
                try:
                    # Confirmar entrega
                    confirmar_entrega(token, company, cronograma, attempt, debug_enabled, config)
                    # Mover archivo a processed/
                    mover_archivo_procesado(data_path)
                except Exception as e:
                    print(f"Error en el proceso de confirmación: {str(e)}", file=sys.stderr)
                    if attempt == retries:
                        sys.exit(1)
                    continue
            
            break
        except RuntimeError as e:
            print(f"Intento {attempt}/{retries} fallido: {e}", file=sys.stderr)
            if attempt == retries:
                print("El proceso falló después de todos los reintentos. Por favor, revise los detalles del error.", file=sys.stderr)
                sys.exit(1)

if __name__ == "__main__":
    main()
