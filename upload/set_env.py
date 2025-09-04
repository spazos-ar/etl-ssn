import sys
import json
import os
import shutil
import glob

CONFIG_FILES = [
    os.path.join(os.path.dirname(__file__), 'config-mensual.json'),
    os.path.join(os.path.dirname(__file__), 'config-semanal.json'),
]

def get_latest_cert_file(environment):
    """Busca el certificado más reciente para el ambiente especificado."""
    script_dir = os.path.dirname(__file__)
    cert_dir = os.path.join(script_dir, 'certs')
    
    if environment == 'test':
        pattern = os.path.join(cert_dir, 'ssn_cert_test_*.pem')
    else:
        pattern = os.path.join(cert_dir, 'ssn_cert_*.pem')
    
    cert_files = glob.glob(pattern)
    if cert_files:
        # Filtrar archivos de test para ambiente prod
        if environment == 'prod':
            cert_files = [f for f in cert_files if 'test' not in os.path.basename(f)]
        
        if cert_files:
            # Retornar el más reciente basado en el nombre (fecha)
            latest_cert = sorted(cert_files)[-1]
            return os.path.relpath(latest_cert, script_dir).replace('\\', '/')
    
    # Fallback a valores por defecto si no se encuentra
    if environment == 'test':
        return 'certs/ssn_cert_test_20250903.pem'
    else:
        return 'certs/ssn_cert_20250903.pem'

# Configuración base de ambientes (sin certificados hardcodeados)
ENVIRONMENTS = {
    'prod': {
        'url': 'https://ri.ssn.gob.ar/api',
        'ssl_verify': True
    },
    'test': {
        'url': 'https://testri.ssn.gob.ar/api',
        'ssl_verify': False
    }
}

def set_environment(env):
    """Cambia el ambiente activo actualizando las configuraciones."""
    if env not in ENVIRONMENTS:
        print(f"❌ Ambiente inválido: {env}. Use 'prod' o 'test'.")
        sys.exit(1)
    
    env_config = ENVIRONMENTS[env]
    url = env_config['url']
    ssl_verify = env_config['ssl_verify']
    
    # Buscar el certificado más reciente dinámicamente
    cert_file = get_latest_cert_file(env)
    
    # Verificar que el certificado exista
    script_dir = os.path.dirname(__file__)
    cert_path = os.path.join(script_dir, cert_file)
    if not os.path.isfile(cert_path):
        print(f"❌ Error: No se encuentra el certificado para el ambiente {env}: {cert_path}")
        print(f"💡 Asegúrese de que el certificado esté disponible antes de cambiar al ambiente {env}")
        sys.exit(1)
    
    print(f"🔧 Configurando ambiente: {env.upper()}")
    print(f"🌐 URL del servicio: {url}")
    print(f"🔒 Certificado: {cert_file}")
    
    updated_count = 0
    for config_path in CONFIG_FILES:
        if not os.path.isfile(config_path):
            print(f"⚠️  No se encuentra {config_path}")
            continue
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Actualizar configuración
            data['environment'] = env
            data['baseUrl'] = url
            data['ssl']['cafile'] = cert_file
            data['ssl']['verify'] = ssl_verify
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            config_name = os.path.basename(config_path)
            print(f"✅ Actualizado {config_name}")
            updated_count += 1
            
        except Exception as e:
            print(f"❌ Error actualizando {config_path}: {str(e)}")
            sys.exit(1)
    
    if updated_count > 0:
        print(f"🎯 Ambiente cambiado exitosamente a {env.upper()}")
        print(f"📋 Se actualizaron {updated_count} archivo(s) de configuración")
    else:
        print("⚠️  No se pudo actualizar ningún archivo de configuración")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Uso: python set_env.py [prod|test]")
        sys.exit(1)
    set_environment(sys.argv[1])
