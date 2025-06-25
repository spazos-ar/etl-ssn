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
    group.add_argument('--fix-month', metavar='YYYY-MM', help='Corrige un mes específico (formato YYYY-MM)')
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

    config_path = args.config or os.path.join(os.path.dirname(__file__), 'config-mensual.json')
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
    url = build_url(config, "entregaMensual")
    headers = {"Content-Type": "application/json", "Token": token}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Error al enviar: {response.status_code} - {response.text}")
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

def main():
    config_path, data_file, confirm, fix, query, empty = get_args()
    config = load_config(config_path)
    token = authenticate(config)
    company = os.getenv('SSN_COMPANY')

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
    main()
