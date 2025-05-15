# -*- coding: utf-8 -*-
import requests
import json
import sys
import os

# URL base y endpoints
BASE_URL = "https://testri.ssn.gob.ar"
LOGIN_URL = f"{BASE_URL}/api/login"
ENTREGA_URL = f"{BASE_URL}/api/inv/entregaSemanal"

# Credenciales de acceso
CIA = "0540"
payload_login = {
    "USER": "spazos",
    "CIA": CIA,
    "PASSWORD": "ARVIDA750A"
}

# Headers iniciales
headers = {
    "Content-Type": "application/json"
}

# Validar argumento: nombre del archivo JSON
if len(sys.argv) != 2:
    print("Uso: python ssn.py SemanaXX.json")
    sys.exit(1)

archivo_json = sys.argv[1]

if not os.path.isfile(archivo_json):
    print(f"Error: el archivo '{archivo_json}' no existe.")
    sys.exit(1)

try:
    # Paso 1: Login
    response = requests.post(LOGIN_URL, json=payload_login, headers=headers)

    if response.status_code == 200:
        data = response.json()
        token = data.get("TOKEN") or data.get("token")

        if not token:
            print("No se encontró el TOKEN en la respuesta.")
            print("Respuesta del login:", data)
            sys.exit(1)

        print(f"Token obtenido: {token}")

        # Paso 2: Cargar contenido JSON de la semana
        try:
            with open(archivo_json, "r", encoding="utf-8") as f:
                entrega_data = json.load(f)
        except json.JSONDecodeError as e:
            print("❌ Error al parsear el archivo JSON:")
            print(f"→ {e.msg} en línea {e.lineno}, columna {e.colno}")
            print("📌 Sugerencia: Revisá comillas, comas, true/false y estructura del archivo.")
            sys.exit(1)

        # Asegurar que el campo CODIGOCOMPANIA esté alineado con la CIA usada en login
        entrega_data["CODIGOCOMPANIA"] = CIA

        # Paso 3: Agregar token al header
        headers["Token"] = token

        # Paso 4: Enviar los datos al endpoint
        response = requests.post(ENTREGA_URL, json=entrega_data, headers=headers)

        if response.status_code == 200:
            print("✅ Entrega enviada correctamente.")
            print("Respuesta del servidor:")
            print(response.json())
        else:
            print(f"❌ Error al enviar la entrega. Código HTTP: {response.status_code}")
            print("Respuesta del servidor:")
            print(response.text)

    else:
        print(f"❌ Error en el login. Código HTTP: {response.status_code}")
        print("Respuesta del servidor:")
        print(response.text)

except requests.exceptions.RequestException as e:
    print(f"❌ Error de conexión: {e}")
