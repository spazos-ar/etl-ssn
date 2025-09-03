import sys
import json
import os
import shutil

CONFIG_FILES = [
    os.path.join(os.path.dirname(__file__), 'config-mensual.json'),
    os.path.join(os.path.dirname(__file__), 'config-semanal.json'),
]

ENVIRONMENTS = {
    'prod': {
        'url': 'https://ri.ssn.gob.ar/api',
        'cert': 'certs/ssn_cert_20250903.pem',
        'ssl_verify': True
    },
    'test': {
        'url': 'https://testri.ssn.gob.ar/api',
        'cert': 'certs/ssn_cert_test_20250903.pem',
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
    cert_file = env_config['cert']
    ssl_verify = env_config['ssl_verify']
    
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
