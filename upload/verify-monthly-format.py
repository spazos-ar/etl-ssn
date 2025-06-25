import requests
import json
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Configuración
BASE_URL = "https://testri.ssn.gob.ar/api/"
LOGIN_ENDPOINT = "/login"
ENTREGA_ENDPOINT = "/inv/entregaMensual"

# Credenciales desde .env
USER = os.getenv("SSN_USER")
PASSWORD = os.getenv("SSN_PASSWORD")
COMPANY = os.getenv("SSN_COMPANY")

# 1. Obtener el token
login_url = BASE_URL.rstrip("/") + LOGIN_ENDPOINT
login_payload = {
    "USER": USER,
    "CIA": COMPANY,
    "PASSWORD": PASSWORD
}
login_headers = {"Content-Type": "application/json"}
login_response = requests.post(login_url, json=login_payload, headers=login_headers)
login_data = login_response.json()
print("Respuesta login:", login_data)
token = login_data.get("TOKEN") or login_data.get("token")
if not token:
    print("No se pudo obtener el token. Revisa las credenciales y la respuesta.")
    exit(1)

# 2. Probar el endpoint mensual
entrega_url = BASE_URL.rstrip("/") + ENTREGA_ENDPOINT
data = {
    "CODIGOCOMPANIA": COMPANY,
    "TIPOENTREGA": "MENSUAL",
    "CRONOGRAMA": "2025-05",
    "STOCKS": []
}
headers = {
    "Content-Type": "application/json",
    "Token": token
}
response = requests.post(entrega_url, json=data, headers=headers)
print("Status:", response.status_code)
print("Respuesta:", response.text)