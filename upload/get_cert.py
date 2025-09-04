import ssl
import socket
import certifi
import logging
import os
import sys
import platform
import argparse
from datetime import datetime

# Configurar la codificación para sistemas Windows
if platform.system() == "Windows":
    # Forzar UTF-8 para stdout y stderr
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    # Configurar la consola para UTF-8 si es posible
    try:
        os.system('chcp 65001 >nul 2>&1')
    except:
        pass

# Configuración de servidores por ambiente
SERVERS = {
    'prod': 'ri.ssn.gob.ar',
    'test': 'testri.ssn.gob.ar'
}

def get_server_certificate(hostname, port=443, environment='prod', timeout=30):
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Crear contexto SSL
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        logger.info(f"🌐 Conectando a {hostname}:{port} (ambiente: {environment.upper()})...")
        logger.info(f"⏱️ Timeout configurado: {timeout} segundos")
        
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            logger.info("🔗 Conexión TCP establecida, iniciando handshake SSL...")
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                logger.info("✅ Conexión SSL establecida exitosamente")
                
                # Obtener certificado en formato PEM
                cert = ssl.DER_cert_to_PEM_cert(ssock.getpeercert(binary_form=True))
                
                # Obtener información del certificado para validación
                cert_info = ssock.getpeercert()
                
                # Guardar certificado con nombre específico por ambiente
                if environment == 'prod':
                    cert_file = f"ssn_cert_{datetime.now().strftime('%Y%m%d')}.pem"
                else:
                    cert_file = f"ssn_cert_{environment}_{datetime.now().strftime('%Y%m%d')}.pem"
                    
                with open(cert_file, "w") as f:
                    f.write(cert)
                logger.info(f"📁 Certificado guardado temporalmente como: {cert_file}")
                
                # Verificar validez del certificado
                if 'notAfter' in cert_info:
                    expiry_date = cert_info['notAfter']
                    logger.info(f"✅ Certificado obtenido (válido hasta: {expiry_date})")
                
                return cert_file
                
    except ssl.SSLError as e:
        logger.error(f"❌ Error SSL: {e}")
        raise
    except socket.gaierror as e:
        logger.error(f"❌ Error de resolución DNS: {e}")
        raise
    except ConnectionResetError as e:
        logger.error(f"❌ Error de conexión: El servidor {hostname} rechazó la conexión")
        logger.error(f"💡 Esto puede ocurrir si el servidor está inactivo o no permite conexiones SSL")
        raise
    except socket.timeout as e:
        logger.error(f"❌ Timeout de conexión: No se pudo conectar a {hostname}")
        logger.error(f"💡 Verifique su conexión a internet o que el servidor esté disponible")
        raise
    except OSError as e:
        if "WinError 10054" in str(e) or "connection was forcibly closed" in str(e).lower():
            logger.error(f"❌ Conexión cerrada por el servidor {hostname}")
            logger.error(f"💡 El servidor de TEST puede estar inactivo o con configuración diferente")
        else:
            logger.error(f"❌ Error de sistema: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        raise

def get_certificates_for_all_environments():
    """Obtiene certificados para todos los ambientes disponibles."""
    certificates = {}
    
    for env, hostname in SERVERS.items():
        try:
            print(f"\n🔒 Obteniendo certificado para ambiente {env.upper()}...")
            cert_file = get_server_certificate(hostname, environment=env, timeout=15)
            certificates[env] = cert_file
            print(f"✅ Certificado {env.upper()} obtenido correctamente")
        except (ConnectionResetError, OSError) as e:
            print(f"⚠️ No se pudo conectar al servidor de {env.upper()}")
            if env == 'test':
                print(f"   💡 El servidor de TEST puede estar inactivo")
            certificates[env] = None
        except Exception as e:
            print(f"❌ Error obteniendo certificado para {env.upper()}: {e}")
            certificates[env] = None
    
    return certificates

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Obtener certificados SSL de servidores SSN')
    parser.add_argument('--env', choices=['prod', 'test', 'all'], default='prod',
                       help='Ambiente del cual obtener el certificado')
    
    args = parser.parse_args()
    
    try:
        if args.env == 'all':
            get_certificates_for_all_environments()
        else:
            hostname = SERVERS[args.env]
            get_server_certificate(hostname, environment=args.env, timeout=15)
    except KeyboardInterrupt:
        print("\n⚠️ Operación cancelada por el usuario")
        sys.exit(1)
    except (ConnectionResetError, OSError, socket.timeout, socket.gaierror, ssl.SSLError) as e:
        # Errores de conexión ya fueron loggeados en la función
        print(f"\n💡 No se pudo obtener el certificado para el ambiente {args.env.upper()}")
        if args.env == 'test':
            print("   El servidor de TEST puede estar temporalmente inactivo")
            print("   Puede usar el certificado de PROD como placeholder para desarrollo")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        sys.exit(1)
