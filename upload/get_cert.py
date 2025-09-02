import ssl
import socket
import certifi
import logging
import os
import sys
import platform
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

def get_server_certificate(hostname, port=443):
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Crear contexto SSL
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        logger.debug(f"Conectando a {hostname}:{port}...")
        
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                logger.debug("Conexión SSL establecida")
                
                # Obtener certificado en formato PEM
                cert = ssl.DER_cert_to_PEM_cert(ssock.getpeercert(binary_form=True))
                
                # Obtener información del certificado para validación
                cert_info = ssock.getpeercert()
                
                # Guardar certificado
                cert_file = f"ssn_cert_{datetime.now().strftime('%Y%m%d')}.pem"
                with open(cert_file, "w") as f:
                    f.write(cert)
                logger.debug(f"Certificado guardado temporalmente como: {cert_file}")
                
                # Verificar validez del certificado
                if 'notAfter' in cert_info:
                    expiry_date = cert_info['notAfter']
                    logger.info(f"✅ Certificado obtenido (válido hasta: {expiry_date})")
                
                return cert_file
                
    except ssl.SSLError as e:
        logger.error(f"Error SSL: {e}")
        raise
    except socket.gaierror as e:
        logger.error(f"Error de resolución DNS: {e}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        raise

if __name__ == "__main__":
    get_server_certificate("ri.ssn.gob.ar")
