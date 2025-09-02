import sys
import json
import os

CONFIG_FILES = [
    os.path.join(os.path.dirname(__file__), 'config-mensual.json'),
    os.path.join(os.path.dirname(__file__), 'config-semanal.json'),
]

URLS = {
    'prod': 'https://ri.ssn.gob.ar/api',
    'test': 'https://testri.ssn.gob.ar/api',
}

def set_base_url(env):
    if env not in URLS:
        print(f"Ambiente inválido: {env}. Use 'prod' o 'test'.")
        sys.exit(1)
    url = URLS[env]
    for config_path in CONFIG_FILES:
        if not os.path.isfile(config_path):
            print(f"No se encuentra {config_path}")
            continue
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['baseUrl'] = url
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"Actualizado {config_path} a {url}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Uso: python set_env.py [prod|test]")
        sys.exit(1)
    set_base_url(sys.argv[1])
