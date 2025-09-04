import sys
import json
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from lib.cert_utils import cert_manager

# Cargar variables de entorno
env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

CONFIG_FILES = [
    os.path.join(os.path.dirname(__file__), 'config-mensual.json'),
    os.path.join(os.path.dirname(__file__), 'config-semanal.json'),
]

CONFIG_FILES = [
    os.path.join(os.path.dirname(__file__), 'config-mensual.json'),
    os.path.join(os.path.dirname(__file__), 'config-semanal.json'),
]

def set_environment(env):
    """Cambia el ambiente activo actualizando las configuraciones."""
    print(f"🔧 Configurando ambiente: {env.upper()}")
    
    # Obtener configuración del ambiente usando el gestor de certificados
    config = cert_manager.get_environment_config(env)
    
    if not config['cert_path']:
        print(f"❌ Error: No se encontró certificado para el ambiente {env}")
        print(f"💡 Verifique que existan certificados en el directorio: {cert_manager.cert_dir}")
        sys.exit(1)
    
    if not config['cert_exists']:
        cert_full_path = cert_manager.get_full_cert_path(config['cert_path'])
        print(f"❌ Error: No se encuentra el certificado para el ambiente {env}: {cert_full_path}")
        print(f"💡 Asegúrese de que el certificado esté disponible antes de cambiar al ambiente {env}")
        sys.exit(1)
    
    print(f"🌐 URL del servicio: {config['url']}")
    print(f"🔒 Certificado: {config['cert_path']}")
    print(f"🛡️ Verificación SSL: {'Activada' if config['ssl_verify'] else 'Desactivada'}")
    
    updated_count = 0
    for config_path in CONFIG_FILES:
        if not os.path.isfile(config_path):
            print(f"⚠️  No se encuentra {config_path}")
            continue
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Actualizar configuración (sin certificados)
            data['environment'] = env
            data['baseUrl'] = config['url']
            data['ssl']['verify'] = config['ssl_verify']
            
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
        
        # Mostrar información adicional sobre los certificados disponibles
        available_certs = cert_manager.list_available_certs()
        if len(available_certs) > 1:
            print(f"📜 Certificados disponibles en {cert_manager.cert_dir}:")
            for cert_info in available_certs:
                cert_name = cert_info['filename']
                is_current = cert_name in config['cert_path']
                status = "🟢 ACTIVO" if is_current else "📄"
                env_label = cert_info['environment'].upper()
                print(f"   {status} {cert_name} ({env_label})")
    else:
        print("⚠️  No se pudo actualizar ningún archivo de configuración")
        sys.exit(1)
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Uso: python set_env.py [prod|test]")
        sys.exit(1)
    
    env = sys.argv[1].lower()
    if env not in ['prod', 'test']:
        print(f"❌ Ambiente inválido: {env}. Use 'prod' o 'test'.")
        sys.exit(1)
    
    set_environment(env)
