import ssl
import socket
import certifi
import logging
from datetime import datetime

def get_server_certificate(hostname, port=443):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        # Crear contexto SSL
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        logger.info(f"Conectando a {hostname}:{port}...")
        
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                logger.info("Conexión SSL establecida")
                
                # Obtener certificado en formato PEM
                cert = ssl.DER_cert_to_PEM_cert(ssock.getpeercert(binary_form=True))
                
                # Obtener información del certificado
                cert_info = ssock.getpeercert()
                
                # Mostrar información relevante
                logger.info("\nInformación del certificado:")
                logger.info("-" * 50)
                
                if 'subject' in cert_info:
                    subject = dict(x[0] for x in cert_info['subject'])
                    logger.info(f"Emitido para: {subject.get('commonName', 'N/A')}")
                
                if 'issuer' in cert_info:
                    issuer = dict(x[0] for x in cert_info['issuer'])
                    logger.info(f"Emitido por: {issuer.get('commonName', 'N/A')}")
                
                if 'notBefore' in cert_info:
                    logger.info(f"Válido desde: {cert_info['notBefore']}")
                
                if 'notAfter' in cert_info:
                    logger.info(f"Válido hasta: {cert_info['notAfter']}")
                
                # Guardar certificado
                cert_file = f"ssn_cert_{datetime.now().strftime('%Y%m%d')}.pem"
                with open(cert_file, "w") as f:
                    f.write(cert)
                logger.info(f"\nCertificado guardado en: {cert_file}")
                
                # Verificar si el certificado está en el almacén de certifi
                with open(certifi.where(), 'r') as f:
                    certifi_store = f.read()
                    if cert in certifi_store:
                        logger.info("El certificado YA está en el almacén de certifi")
                    else:
                        logger.info("El certificado NO está en el almacén de certifi")
                
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
