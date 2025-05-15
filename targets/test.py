# -*- coding: utf-8 -*-
import requests
import json
import sys
import os
import traceback
import logging
import datetime

# Configurar logging
log_file = f"ssn_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# URL base y endpoints
BASE_URL = "https://testri.ssn.gob.ar"
LOGIN_URL = f"{BASE_URL}/api/login"
ENTREGA_URL = f"{BASE_URL}/api/inv/entregaSemanal"

# Credenciales de acceso
CIA = "0555"
payload_login = {
    "USER": "user", 
    "CIA": CIA,
    "PASSWORD": "passwd"
}

# Headers iniciales
headers = {
    "Content-Type": "application/json"
}

def log_message(message):
    """Escribe un mensaje tanto al log como a la consola"""
    print(message)
    logging.info(message)

def main():
    log_message("Iniciando script de SSN")
    
    # Validar argumento: nombre del archivo JSON
    if len(sys.argv) != 2:
        log_message("Uso: python ssn.py SemanaXX.json")
        return 1

    archivo_json = sys.argv[1]
    log_message(f"Archivo JSON: {archivo_json}")

    if not os.path.isfile(archivo_json):
        log_message(f"Error: el archivo '{archivo_json}' no existe.")
        return 1

    try:
        # Paso 1: Login
        log_message(f"Intentando login en: {LOGIN_URL}")
        log_message(f"Payload de login: {payload_login}")
        
        response = requests.post(LOGIN_URL, json=payload_login, headers=headers, timeout=30)
        log_message(f"Código de estado: {response.status_code}")
        
        response_text = "No se pudo obtener respuesta"
        try:
            response_text = response.text
        except:
            pass
        
        log_message(f"Respuesta del servidor: {response_text[:200]}")

        if response.status_code == 200:
            try:
                data = response.json()
                log_message(f"Datos de respuesta JSON: {data}")
                
                token = data.get("TOKEN")
                if not token:
                    log_message("No se encontró el TOKEN en la respuesta.")
                    return 1

                log_message(f"Token obtenido: {token[:10]}...")

                # Paso 2: Cargar contenido JSON de la semana
                try:
                    with open(archivo_json, "r", encoding="utf-8") as f:
                        entrega_data = json.load(f)
                    log_message(f"Datos cargados del archivo: {len(str(entrega_data))} caracteres")
                except Exception as e:
                    log_message(f"Error al cargar el archivo JSON: {e}")
                    return 1

                # Asegurar que el campo CODIGOCOMPANIA esté alineado con la CIA usada en login
                entrega_data["CODIGOCOMPANIA"] = CIA

                # Paso 3: Agregar token al header
                headers["Token"] = token
                log_message(f"Headers para la entrega: {headers}")
                
                # Paso 4: Enviar los datos al endpoint
                log_message(f"Enviando datos a: {ENTREGA_URL}")
                response = requests.post(
                    ENTREGA_URL, 
                    json=entrega_data, 
                    headers=headers,
                    timeout=60
                )
                
                log_message(f"Código de estado: {response.status_code}")
                
                try:
                    response_text = response.text
                    log_message(f"Respuesta: {response_text[:200]}")
                except Exception as e:
                    log_message(f"Error al leer la respuesta: {e}")

                if response.status_code == 200:
                    log_message("Entrega enviada correctamente.")
                    try:
                        log_message("Respuesta del servidor:")
                        log_message(json.dumps(response.json(), indent=2, ensure_ascii=False))
                    except:
                        log_message(f"Respuesta (texto): {response.text}")
                else:
                    log_message(f"Error al enviar la entrega. Código HTTP: {response.status_code}")
                    log_message(f"Respuesta del servidor: {response.text}")

            except json.JSONDecodeError as e:
                log_message(f"Error al procesar JSON de respuesta: {e}")
                log_message(f"Texto recibido: {response.text[:200]}")
                return 1
            except Exception as e:
                log_message(f"Error inesperado al procesar respuesta: {e}")
                traceback.print_exc()
                logging.error(traceback.format_exc())
                return 1

        else:
            log_message(f"Error en el login. Código HTTP: {response.status_code}")
            log_message(f"Respuesta del servidor: {response.text}")
            return 1

    except requests.exceptions.RequestException as e:
        log_message(f"Error de conexión: {e}")
        return 1
    except Exception as e:
        log_message(f"Error inesperado: {e}")
        traceback.print_exc()
        logging.error(traceback.format_exc())
        return 1

    log_message("Script finalizado")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        log_message(f"Script finalizado con código: {exit_code}")
        log_message(f"Se ha creado un archivo de registro: {log_file}")
    except Exception as e:
        logging.error(f"ERROR CRÍTICO: {e}")
        logging.error(traceback.format_exc())
        print(f"ERROR CRÍTICO: {e}")
        print(f"Detalles en el archivo de registro: {log_file}")
    
    # Esta línea es para mantener la consola abierta si se está ejecutando haciendo doble clic
    # Puedes comentarla si ejecutas desde la terminal
    input("Presiona Enter para salir...")
