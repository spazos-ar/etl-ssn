#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script actualizado para enviar datos mensuales a la SSN usando directamente el JSON
generado por xls-mensual.py

Autor: Adaptado por ChatGPT
Fecha: Junio 2025
"""

import sys
import json
import requests
import os
import argparse
import shutil
from dotenv import load_dotenv
from pathlib import Path
import re

env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

def get_args():
    parser = argparse.ArgumentParser(description='Envía datos mensuales a la SSN')
    parser.add_argument('--config', help='Ruta al archivo de configuración')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--confirm-month', action='store_true', help='Confirma la entrega mensual y mueve el archivo a processed/')
    group.add_argument('--fix-month', metavar='YYYY-MM', help='Pide rectificativa de un mes específico (formato YYYY-MM)')
    group.add_argument('--query-month', metavar='YYYY-MM', help='Consulta el estado de un mes específico (formato YYYY-MM)')
    group.add_argument('--empty-month', metavar='YYYY-MM', help='Envía un mes vacío sin inversiones (formato YYYY-MM)')

    parser.add_argument('data_file', nargs='?', help='Archivo JSON con los datos a enviar (no requerido con --fix-month, --query-month o --empty-month)')
    args = parser.parse_args()

    if args.fix_month or args.query_month or args.empty_month:
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
    return config_path, args.data_file, args.confirm_month, args.fix_month, args.query_month, args.empty_month

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def authenticate(config):
    user = os.getenv('SSN_USER')
    password = os.getenv('SSN_PASSWORD')
    company = os.getenv('SSN_COMPANY')
    url = config['baseUrl'].rstrip('/') + config['endpoints']['login']
    response = requests.post(url, json={"USER": user, "CIA": company, "PASSWORD": password}, headers={"Content-Type": "application/json"})
    data = response.json()
    print("Respuesta de login:", data)  # Depuración
    token = data.get('TOKEN') or data.get('token')
    if not token:
        raise RuntimeError(f"No se encontró el token en la respuesta: {data}")
    return token

def build_url(config, endpoint):
    return config['baseUrl'].rstrip('/') + config['endpoints'][endpoint]

def enviar_entrega(token, data, config):
    # Procesa y valida cada registro en STOCKS
    for reg in data.get("STOCKS", []):
        # Corrige FECHAPASEVT y PRECIOPASEVT
        if reg.get("TIPOESPECIE") not in ["TP", "ON"] or reg.get("TIPOVALUACION") != "T":
            reg["FECHAPASEVT"] = ""
            reg["PRECIOPASEVT"] = 0.0
            
        # Validación de cantidades según tipo de especie
        tipo_especie = reg.get("TIPOESPECIE", "")
        cant_devengada = reg.get("CANTIDADDEVENGADOESPECIES", 0)
        cant_percibida = reg.get("CANTIDADPERCIBIDOESPECIES", 0)
        
        # Para especies tipo TP, AC, FF aseguramos que las cantidades sean números positivos
        if tipo_especie in ["TP", "AC", "FF"]:
            # Si las cantidades son muy grandes o negativas, las reseteamos a 0
            if cant_devengada < 0 or cant_devengada > 1e9:
                reg["CANTIDADDEVENGADOESPECIES"] = 0.0
            if cant_percibida < 0 or cant_percibida > 1e9:
                reg["CANTIDADPERCIBIDOESPECIES"] = 0.0
    url = build_url(config, "entregaMensual")
    headers = {"Content-Type": "application/json", "Token": token}
    print("DEBUG: JSON enviado:\n", json.dumps(data, indent=2, ensure_ascii=False))
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        print("\nDEBUG: Headers de respuesta:", dict(response.headers))
        # Manejo de error amigable
        try:
            resp_json = response.json()
            print("DEBUG: Respuesta JSON completa:", json.dumps(resp_json, indent=2, ensure_ascii=False))
            errors = resp_json.get("errores") or resp_json.get("errors")
            if errors and isinstance(errors, list):
                print("\nErrores encontrados:")
                for error in errors:
                    print(f"- {error}")
            else:
                msg = resp_json.get("message", "") or resp_json.get("detail", "") or response.text
                print(f"\nError ({response.status_code}): {msg}")
        except Exception as e:
            print(f"\nDEBUG: Error al parsear JSON: {str(e)}")
            print(f"\nError al enviar ({response.status_code}): {response.text}")
            print("\nDEBUG: Contenido raw de la respuesta:", response.content)
        sys.exit(1)
    print("Entrega mensual enviada correctamente.")

def confirmar_entrega(token, company, cronograma, config):
    url = build_url(config, "confirmarEntregaMensual")
    headers = {"Content-Type": "application/json", "Token": token}
    payload = {
        "CODIGOCOMPANIA": company,
        "TIPOENTREGA": "MENSUAL",
        "CRONOGRAMA": cronograma
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Error al confirmar: {response.status_code} - {response.text}")
    print("Entrega mensual confirmada correctamente.")

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
    print(f"Archivo movido exitosamente a: {archivo_destino}")

def fix_mes(token, company, cronograma, config):
    """Solicita rectificativa mensual usando PUT con el body requerido por la SSN."""
    url = build_url(config, "entregaMensual")
    headers = {"Content-Type": "application/json", "Token": token}
    payload = {
        "cronograma": cronograma,
        "codigoCompania": company,
        "tipoEntrega": "Mensual"
    }
    print("DEBUG: JSON de rectificativa mensual (PUT):\n", json.dumps(payload, indent=2))
    response = requests.put(url, json=payload, headers=headers)
    try:
        resp_json = response.json()
    except Exception:
        resp_json = {}
    if response.status_code == 200:
        print(f"Mes {cronograma} (rectificativa) solicitado exitosamente.")
        return True
    error_message = (
        resp_json.get("message") or
        resp_json.get("detail") or
        resp_json.get("errors") or
        response.text
    )
    if not isinstance(error_message, str):
        error_message = json.dumps(error_message, indent=2, ensure_ascii=False)
    print("DEBUG: Respuesta del servidor (PUT):\n", response.text)
    raise RuntimeError(f"Error al pedir rectificativa mensual: {error_message}")

def query_mes(token, company, cronograma, config):
    """Consulta el estado de un mes específico.
    
    Args:
        token: Token de autenticación
        company: Código de la compañía
        cronograma: Mes a consultar (formato YYYY-MM)
        config: Configuración del script
    """
    url = build_url(config, "entregaMensual")
    headers = {"Content-Type": "application/json", "Token": token}
    
    # Construir query params usando camelCase como especifica la documentación
    params = {
        "codigoCompania": company,
        "tipoEntrega": "Mensual",
        "cronograma": cronograma
    }

    print("DEBUG: Consultando mes con parámetros:\n", json.dumps(params, indent=2))
    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Estado del mes {cronograma}:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return True
        except json.JSONDecodeError:
            print(f"La respuesta no es un JSON válido: {response.text}")
            raise RuntimeError("Error al procesar la respuesta del servidor")
    else:
        try:
            resp_json = response.json()
            error_message = (
                resp_json.get("errors") or
                resp_json.get("message") or
                resp_json.get("detail") or
                response.text
            )
            if not isinstance(error_message, str):
                error_message = json.dumps(error_message, indent=2, ensure_ascii=False)
        except Exception as e:
            error_message = f"No se pudo procesar la respuesta del servidor: {str(e)}\nRespuesta completa: {response.text}"
        
        print("DEBUG: Respuesta del servidor:\n", response.text)
        raise RuntimeError(f"Error al consultar mes: {response.status_code} - {error_message}")

def main():
    config_path, data_file, confirm, fix, query, empty = get_args()
    config = load_config(config_path)
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
        print(f"\nError: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError inesperado: {e}")
        sys.exit(1)
