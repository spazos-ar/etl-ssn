#!/usr/bin/env python3
import ssl
import socket
import httpx
import sys
import warnings

def test_ssl_connection(hostname, port=443):
    """Prueba diferentes configuraciones SSL"""
    
    print(f"🔍 Probando conexión SSL a {hostname}:{port}")
    
    # Prueba 1: SSL básico sin verificación
    print("\n1️⃣ Prueba SSL básico sin verificación...")
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((hostname, port), timeout=15) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                print(f"✅ SSL básico: ÉXITO")
                print(f"   Protocolo: {ssock.version()}")
                print(f"   Cipher: {ssock.cipher()}")
                return True
    except Exception as e:
        print(f"❌ SSL básico: FALLO - {e}")
    
    # Prueba 2: SSL sin SNI
    print("\n2️⃣ Prueba SSL sin Server Name Indication (SNI)...")
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((hostname, port), timeout=15) as sock:
            with context.wrap_socket(sock) as ssock:  # Sin server_hostname
                print(f"✅ SSL sin SNI: ÉXITO")
                print(f"   Protocolo: {ssock.version()}")
                return True
    except Exception as e:
        print(f"❌ SSL sin SNI: FALLO - {e}")
    
    # Prueba 3: SSL con TLS específicos
    for version in [ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3]:
        print(f"\n3️⃣ Prueba SSL con {version.name}...")
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            context.minimum_version = version
            context.maximum_version = version
            
            with socket.create_connection((hostname, port), timeout=15) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    print(f"✅ {version.name}: ÉXITO")
                    print(f"   Protocolo: {ssock.version()}")
                    return True
        except Exception as e:
            print(f"❌ {version.name}: FALLO - {e}")
    
    # Prueba 4: HTTPX con diferentes configuraciones
    print(f"\n4️⃣ Prueba HTTPX sin verificación...")
    try:
        warnings.filterwarnings('ignore')
        with httpx.Client(verify=False, timeout=15.0) as client:
            response = client.get(f'https://{hostname}/api')
            print(f"✅ HTTPX básico: ÉXITO - Status {response.status_code}")
            print(f"   Headers: {dict(list(response.headers.items())[:3])}")
            return True
    except Exception as e:
        print(f"❌ HTTPX básico: FALLO - {e}")
    
    print(f"\n❌ Todas las pruebas fallaron para {hostname}:{port}")
    return False

def test_login_endpoint(hostname, port=443):
    """Prueba el endpoint de login específicamente"""
    print(f"\n🔐 Probando endpoint de login...")
    
    try:
        warnings.filterwarnings('ignore')
        with httpx.Client(verify=False, timeout=30.0) as client:
            # Primero probamos GET al /api
            print("📡 GET /api...")
            response = client.get(f'https://{hostname}/api')
            print(f"   Status: {response.status_code}")
            
            # Luego probamos POST al /login
            print("📡 POST /api/login...")
            login_data = {
                "usuario": "test",
                "password": "test"
            }
            response = client.post(f'https://{hostname}/api/login', json=login_data)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            return True
    except Exception as e:
        print(f"❌ Endpoint login: FALLO - {e}")
        return False

if __name__ == "__main__":
    hostname = "testri.ssn.gob.ar"
    
    if test_ssl_connection(hostname):
        test_login_endpoint(hostname)
    else:
        print(f"\n💡 Sugerencias:")
        print(f"   - El servidor puede estar configurado con SSL muy restrictivo")
        print(f"   - Puede requerir certificado cliente específico")
        print(f"   - Puede estar usando un proxy o firewall que bloquea ciertas conexiones")
        print(f"   - Puede estar activo solo en horarios específicos")
