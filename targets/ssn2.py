# -*- coding: utf-8 -*-
import requests
import json
import sys
import os
import socket
import traceback

# URL base y endpoints
BASE_URL = "https://testri.ssn.gob.ar"
LOGIN_URL = f"{BASE_URL}/api/login"
ENTREGA_URL = f"{BASE_URL}/api/inv/entregaSemanal"

# Verificar conectividad básica al servidor
def check_server_connection(url):
    """Verifica si el servidor está accesible"""
    try:
        domain = url.split("//")[1].split("/")[0]
        print(f"Verificando conexión a: {domain}")
        
        # Intenta resolver el nombre de dominio
        socket.gethostbyname(domain)
        
        # Intenta una solicitud simple
        response = requests.get(f"https://{domain}", timeout=5)
        print(f"Servidor accesible. Código: {response.status_code}")
        return True
    except socket.gaierror:
        print(f"No se puede resolver el nombre de dominio: {domain}")
        return False
    except requests.exceptions.ConnectionError:
        print(f"No se puede conectar al servidor: {domain}")
        return False
    except requests.exceptions.Timeout:
        print(f"Tiempo de espera agotado al conectar a: {domain}")
        return False
    except Exception as e:
        print(f"Error al verificar conexión: {e}")
        return False

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

# ======= PROGRAMA PRINCIPAL =======
def main():
    # Validar argumento: nombre del archivo JSON
    if len(sys.argv) != 2:
        print("Uso: python ssn.py SemanaXX.json")
        return 1

    archivo_json = sys.argv[1]
    print(f"Archivo JSON: {archivo_json}")

    if not os.path.isfile(archivo_json):
        print(f"Error: el archivo '{archivo_json}' no existe.")
        return 1

    # Verificar conexión al servidor
    if not check_server_connection(BASE_URL):
        print("No se puede continuar sin conexión al servidor.")
        return 1

    try:
        # Paso 1: Login
        print(f"\nIntentando login en: {LOGIN_URL}")
        print(f"Credenciales: CIA={CIA}, USER=user")
        
        response = requests.post(LOGIN_URL, json=payload_login, headers=headers, timeout=10)
        print(f"Código de estado: {response.status_code}")
        
        # Intenta obtener texto de respuesta de forma segura
        try:
            response_text = response.text
            print(f"Respuesta: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
        except Exception as e:
            print(f"Error al leer la respuesta: {e}")

        if response.status_code == 200:
            try:
                data = response.json()
                
                # CAMBIO IMPORTANTE: Verificar "token" (minúsculas) en lugar de "TOKEN" (mayúsculas)
                token = data.get("token")  
                
                if not token:
                    print("No se encontró el token en la respuesta.")
                    print(f"Respuesta completa: {data}")
                    return 1

                print(f"Token obtenido: {token[:50]}...")

                # Paso 2: Cargar contenido JSON de la semana
                with open(archivo_json, "r", encoding="utf-8") as f:
                    entrega_data = json.load(f)
                print(f"Datos cargados del archivo: {len(str(entrega_data))} caracteres")

                # Asegurar que el campo CODIGOCOMPANIA esté alineado con la CIA usada en login
                entrega_data["CODIGOCOMPANIA"] = CIA

                # Paso 3: Agregar token al header (clave exacta: "Token")
                headers["Token"] = token
                print(f"Headers para la solicitud: {headers}")
                
                # Paso 4: Enviar los datos al endpoint de presentación semanal
                print(f"\nEnviando datos a: {ENTREGA_URL}")
                response = requests.post(
                    ENTREGA_URL, 
                    json=entrega_data, 
                    headers=headers,
                    timeout=30  # Tiempo de espera aumentado para envíos grandes
                )
                
                print(f"Código de estado: {response.status_code}")
                
                # Intenta obtener texto de respuesta de forma segura
                try:
                    response_text = response.text
                    print(f"Respuesta: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")
                except Exception as e:
                    print(f"Error al leer la respuesta: {e}")

                if response.status_code == 200:
                    print("\nEntrega enviada correctamente.")
                    try:
                        print("Respuesta del servidor:")
                        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
                    except:
                        print(f"Respuesta: {response.text}")
                else:
                    print(f"\nError al enviar la entrega. Código HTTP: {response.status_code}")
                    print("Respuesta del servidor:")
                    print(response.text)

            except json.JSONDecodeError as e:
                print(f"Error al procesar JSON de respuesta: {e}")
                print(f"Texto recibido: {response.text[:200]}...")
                return 1

        else:
            print(f"\nError en el login. Código HTTP: {response.status_code}")
            print("Respuesta del servidor:")
            print(response.text)
            return 1

    except requests.exceptions.RequestException as e:
        print(f"\nError de conexión: {e}")
        return 1
    except Exception as e:
        print(f"\nError inesperado: {e}")
        # Imprimir el traceback para más detalles
        print("\nDetalles del error:")
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
