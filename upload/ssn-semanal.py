#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import requests
import os

def authenticate(config, debug_enabled):
    """
    Autenticación en el servicio de SSN.
    :param config: Diccionario con la configuración de autenticación.
    :param debug_enabled: Booleano que indica si la depuración está habilitada.
    :return: Token de autenticación.
    """

    url = "https://testri.ssn.gob.ar/api/login"
    payload = {
        "USER": config["user"],
        "CIA": config["company"],
        "PASSWORD": config["password"]
    }
    headers = {"Content-Type": "application/json"}
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

def enviar_entrega(token, company, records, cronograma, attempt, debug_enabled):
    url = "https://testri.ssn.gob.ar/api/inv/entregaSemanal"
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
        "TIPOENTREGA": "SEMANAL",  # Ajustar según sea necesario
        "CRONOGRAMA": cronograma,  # Leer desde el nivel superior del archivo JSON
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
            print("DEBUG: Respuesta del servidor:", response.text)
        raise RuntimeError(f"Error al enviar: {response.status_code} - {error_message}")

def main():
    if len(sys.argv) < 4 or sys.argv[1] != "--config":
        print("Uso: python ssn-semanal.py --config <archivo_configuracion.json> <archivo_datos.json>", file=sys.stderr)
        sys.exit(1)

    config_path = sys.argv[2]
    data_path = sys.argv[3]

    if not os.path.isfile(config_path):
        print(f"Error: El archivo de configuración '{config_path}' no existe.", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(data_path):
        print(f"Error: El archivo de datos '{data_path}' no existe.", file=sys.stderr)
        sys.exit(1)

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    with open(data_path, 'r') as data_file:
        data = json.load(data_file)

    cronograma = data.get("CRONOGRAMA", "")
    if not cronograma:
        raise ValueError("El campo 'CRONOGRAMA' está vacío o no existe en el archivo JSON.")

    token = authenticate(config, config.get("debug", False))
    company = config["company"]
    retries = config.get("retries", 4)
    debug_enabled = config.get("debug", False)

    for attempt in range(1, retries + 1):
        try:
            enviar_entrega(token, company, data.get("OPERACIONES", []), cronograma, attempt, debug_enabled)
            print("Proceso completado exitosamente.")
            break
        except RuntimeError as e:
            print(f"Reintento {attempt}/{retries} fallido: {e}", file=sys.stderr)
            if attempt == retries:
                print("El proceso falló después de todos los reintentos. Por favor, revise los detalles del error.", file=sys.stderr)
                sys.exit(1)

if __name__ == "__main__":
    main()
