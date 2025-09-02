#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para la carga y confirmación de datos semanales al sistema de la SSN.

Este script maneja el proceso de carga de información semanal a la Superintendencia
de Seguros de la Nación (SSN). Tiene dos funciones principales:
1. Enviar los datos de operaciones semanales al servidor de la SSN
2. Confirmar la entrega semanal (opcional, usando --confirm-week)

El script soporta las siguientes operaciones:
- Autenticación en el sistema SSN
- Envío de datos de operaciones semanales
- Confirmación de la entrega semanal
- Movimiento automático de archivos procesados

Uso:
    python ssn-semanal.py [--config CONFIG] [--confirm-week] data_file

Argumentos:
    data_file: Archivo JSON con los datos a enviar
    --config: Ruta al archivo de configuración (opcional)
    --confirm-week: Confirma la entrega y mueve el archivo a processed/ (opcional)

El archivo de configuración (config.json) debe contener:
    {
        "baseUrl": "URL base del servicio",
        "endpoints": {
            "login": "ruta del endpoint de login",
            "entregaSemanal": "ruta del endpoint de entrega",
            "confirmarEntregaSemanal": "ruta del endpoint de confirmación"
        },
        "retries": número de reintentos,
        "debug": boolean para modo debug
    }

Variables de entorno requeridas (.env):
    SSN_USER: Usuario para autenticación
    SSN_PASSWORD: Contraseña del usuario
    SSN_COMPANY: Código de la compañía

Autor: G. Casanova
Fecha: Septiembre 2025
"""

import sys
import json
import os
import argparse
import shutil
from dotenv import load_dotenv
from pathlib import Path
import re
import logging
from lib.ssn_client import SSNClient  # TODO: Actualizar a ssn-client en v2.0

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
env_path = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(dotenv_path=env_path)

def get_config_path():
    """Obtiene la ruta del archivo de configuración y procesa argumentos.
    
    Returns:
        tuple: (config_path, data_path, confirm_week, fix_week, query_week, empty_week)
            config_path: Ruta al archivo de configuración
            data_path: Ruta al archivo de datos (None si se usa --fix-week o --query-week o --empty-week)
            confirm_week: Bool indicando si se debe confirmar la semana
            fix_week: String con la semana a corregir (formato YYYY-WW)
            query_week: String con la semana a consultar (formato YYYY-WW)
            empty_week: String con la semana a enviar vacía (formato YYYY-WW)
    """
    parser = argparse.ArgumentParser(description='Envía datos semanales a la SSN')
    parser.add_argument('--config', help='Ruta al archivo de configuración', default='config-semanal.json')
    parser.add_argument('--test', action='store_true', help='Prueba la conexión SSL con el servidor')
    
    # Grupo mutuamente excluyente para los modos de operación
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--confirm-week', action='store_true', 
                      help='Confirma la entrega semanal y mueve el archivo a processed/')
    group.add_argument('--fix-week', metavar='YYYY-WW',
                      help='Pide rectificativa de una semana específica (formato YYYY-WW)')
    group.add_argument('--query-week', metavar='YYYY-WW',
                      help='Consulta el estado de una semana específica (formato YYYY-WW)')
    group.add_argument('--empty-week', metavar='YYYY-WW',
                      help='Envía una semana vacía sin operaciones (formato YYYY-WW)')
    
    # El archivo de datos es obligatorio solo si no se usa --fix-week o --query-week o --empty-week
    parser.add_argument('data_file', nargs='?', 
                       help='Archivo JSON con los datos a enviar (no requerido con --fix-week, --query-week o --empty-week)')
    
    args = parser.parse_args()
    
    # Validar combinación de argumentos
    if args.test:
        if args.data_file:
            parser.error("No se debe especificar data_file cuando se usa --test")
    elif args.fix_week or args.query_week or args.empty_week:
        if args.data_file:
            parser.error("El argumento 'data_file' no debe especificarse cuando se usa --fix-week, --query-week o --empty-week")
        # Validar formato de semana (YYYY-WW)
        week_arg = args.fix_week or args.query_week or args.empty_week
        if not re.match(r'^\d{4}-\d{2}$', week_arg):
            parser.error("El formato de semana debe ser YYYY-WW (ejemplo: 2025-33)")
        año, semana = map(int, week_arg.split('-'))
        if not (2000 <= año <= 2100 and 1 <= semana <= 53):
            parser.error("Valores inválidos. El año debe estar entre 2000 y 2100, y la semana entre 1 y 53")
    elif not args.data_file:
        parser.error("Se requiere el archivo de datos cuando no se usa --test, --fix-week, --query-week o --empty-week")
    
    if args.config:
        if os.path.isfile(args.config):
            config_path = args.config
        else:
            # Si la ruta es relativa, buscar en la carpeta del script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            alt_path = os.path.join(script_dir, args.config)
            if os.path.isfile(alt_path):
                config_path = alt_path
            else:
                raise FileNotFoundError(f"El archivo de configuración '{args.config}' no existe ni en el directorio actual ni en '{alt_path}'.")
    else:
        # Si no se especifica, usar el config.json en el directorio del script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config-semanal.json')
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"No se encuentra el archivo de configuración por defecto en '{config_path}'")
    
    return config_path, args.data_file, args.confirm_week, args.fix_week, args.query_week, args.empty_week, args.test

def load_config(config_path):
    """Carga la configuración desde un archivo JSON.
    
    Args:
        config_path (str): Ruta al archivo de configuración
    
    Returns:
        dict: Configuración cargada
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Validar configuración mínima requerida
    required_fields = ['baseUrl', 'endpoints']
    missing_fields = [field for field in required_fields if field not in config]
    if missing_fields:
        raise ValueError(f"Campos requeridos faltantes en config.json: {', '.join(missing_fields)}")
    
    return config

def setup_logging(debug_mode):
    """Configura el sistema de logging.
    
    Args:
        debug_mode (bool): Si True, establece el nivel de logging a DEBUG
    """
    # Configuración básica
    logging.basicConfig(
        level=logging.DEBUG if debug_mode else logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Ajustar niveles por logger
    if not debug_mode:
        # En modo no-debug, solo mostramos WARNING y superior
        for logger_name in ['httpx', 'httpcore', 'urllib3', 'ssn_client']:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
    else:
        # En modo debug, configuramos niveles específicos
        logging.getLogger('ssn_client').setLevel(logging.DEBUG)
        for logger_name in ['httpx', 'httpcore', 'urllib3']:
            logging.getLogger(logger_name).setLevel(logging.WARNING)

def authenticate(config, debug_enabled):
    """
    Autenticación en el servicio de SSN usando el cliente HTTP.
    
    Args:
        config: Diccionario con la configuración operativa
        debug_enabled: Booleano que indica si la depuración está habilitada
    
    Returns:
        str: Token de autenticación
    
    Raises:
        RuntimeError: Si hay error de autenticación
    """
    try:
        with SSNClient(config, debug=debug_enabled) as client:
            return client.authenticate()
    except Exception as e:
        raise RuntimeError(f"Error de autenticación: {str(e)}")

def enviar_entrega(token, company, records, cronograma, attempt, debug_enabled, config):
    """Envía la entrega semanal al sistema SSN."""
    try:
        # Validar y agregar CODIGOCOMPANIA a cada registro
        for record in records:
            if not record.get("CODIGOCOMPANIA"):
                record["CODIGOCOMPANIA"] = company

        # Construir el JSON final sin la sección HEADER
        payload = {
            "CODIGOCOMPANIA": company,
            "TIPOENTREGA": "SEMANAL",
            "CRONOGRAMA": cronograma,
            "OPERACIONES": records
        }

        with SSNClient(config, debug=debug_enabled) as client:
            client.token = token
            client.post("entregaSemanal", payload)
            print(json.dumps({
                "type": "STATE",
                "value": {"last_sent": cronograma}
            }))
            return True
    except Exception as e:
        raise RuntimeError(f"Error al enviar entrega semanal: {str(e)}")

def confirmar_entrega(token, company, cronograma, attempt, debug_enabled, config):
    """Confirma la entrega semanal en el sistema de la SSN."""
    try:
        with SSNClient(config, debug=debug_enabled) as client:
            client.token = token
            payload = {
                "CODIGOCOMPANIA": company,
                "TIPOENTREGA": "SEMANAL",
                "CRONOGRAMA": cronograma
            }
            client.post("confirmarEntregaSemanal", payload)
            print("Entrega semanal confirmada exitosamente.")
            return True
    except Exception as e:
        raise RuntimeError(f"Error al confirmar: {str(e)}")

def mover_archivo_procesado(data_file):
    """Mueve el archivo JSON procesado a la carpeta processed/weekly/."""
    try:
        # Crear directorio processed/weekly/ si no existe
        processed_dir = os.path.join(os.path.dirname(data_file), "processed", "weekly")
        os.makedirs(processed_dir, exist_ok=True)

        # Mover el archivo
        archivo_destino = os.path.join(processed_dir, os.path.basename(data_file))
        shutil.move(data_file, archivo_destino)
        print(f"Archivo movido exitosamente a: {archivo_destino}")
    except Exception as e:
        print(f"Error al mover el archivo: {str(e)}", file=sys.stderr)
        raise

def fix_semana(token, company, cronograma, attempt, debug_enabled, config):
    """Envía una corrección (rectificativa) para una semana específica usando PUT.
    Args:
        token: Token de autenticación
        company: Código de la compañía
        cronograma: Semana a corregir (formato YYYY-WW)
        attempt: Número de intento actual
        debug_enabled: Si está en modo debug
        config: Configuración del script
    Raises:
        RuntimeError: Si hay un error al procesar la solicitud
    """
    try:
        with SSNClient(config, debug=debug_enabled) as client:
            client.token = token
            payload = {
                "cronograma": cronograma,
                "codigoCompania": company,
                "tipoEntrega": "Semanal"
            }
            client.put("entregaSemanal", payload)
            print(f"Semana {cronograma} (rectificativa) solicitada exitosamente.")
            return True
    except Exception as e:
        raise RuntimeError(f"Error al pedir rectificativa: {str(e)}")

def query_semana(token, company, cronograma, attempt, debug_enabled, config):
    """Consulta el estado de una semana específica.
    
    Args:
        token: Token de autenticación
        company: Código de la compañía
        cronograma: Semana a consultar (formato YYYY-WW)
        attempt: Número de intento actual
        debug_enabled: Si está en modo debug
        config: Configuración del script
    """
    try:
        with SSNClient(config, debug=debug_enabled) as client:
            client.token = token
            params = {
                "codigoCompania": company,
                "tipoEntrega": "SEMANAL",
                "cronograma": cronograma
            }
            
            response = client.get("entregaSemanal", params=params)
            print(f"Estado de la semana {cronograma}:")
            print(json.dumps(response, indent=2, ensure_ascii=False))
            return True
    except Exception as e:
        raise RuntimeError(f"Error al consultar semana: {str(e)}")

def load_data(data_file):
    """Carga los datos desde un archivo JSON.
    
    Args:
        data_file (str): Ruta al archivo de datos
    
    Returns:
        dict: Datos cargados del archivo
    
    Raises:
        FileNotFoundError: Si el archivo no existe
        json.JSONDecodeError: Si el archivo no es un JSON válido
        ValueError: Si faltan campos requeridos en los datos
    """
    if not os.path.isfile(data_file):
        raise FileNotFoundError(f"No se encuentra el archivo de datos: {data_file}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Validar estructura mínima requerida
    if not isinstance(data, dict):
        raise ValueError("El archivo debe contener un objeto JSON")
    
    required_fields = ['CRONOGRAMA', 'OPERACIONES']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Campos requeridos faltantes en el archivo de datos: {', '.join(missing_fields)}")
    
    return data

def send_empty_week(token, company, cronograma, attempt, debug_enabled, config):
    """Envía una semana sin operaciones.
    
    Args:
        token: Token de autenticación
        company: Código de la compañía
        cronograma: Semana a enviar (formato YYYY-WW)
        attempt: Número de intento actual
        debug_enabled: Si está en modo debug
        config: Configuración del script
    
    Returns:
        bool: True si la operación fue exitosa

    Raises:
        RuntimeError: Si hay un error al procesar la solicitud
    """
    try:
        with SSNClient(config, debug=debug_enabled) as client:
            client.token = token
            
            # Crear payload con orden específico de campos
            from collections import OrderedDict
            payload = OrderedDict([
                ("CRONOGRAMA", cronograma),
                ("CODIGOCOMPANIA", company),
                ("TIPOENTREGA", "SEMANAL"),
                ("OPERACIONES", [])
            ])
            
            client.post("entregaSemanal", payload)
            print(f"Semana vacía {cronograma} enviada exitosamente.")
            return True
    except Exception as e:
        raise RuntimeError(f"Error al enviar semana vacía: {str(e)}")

def test_ssl_connection(config):
    """Prueba la conexión SSL con el servidor."""
    try:
        with SSNClient(config, debug=True) as client:
            # La inicialización del cliente ya prueba la conexión SSL
            return True
    except Exception as e:
        raise RuntimeError(f"Error en la prueba de conexión SSL: {str(e)}")

def main():
    """Función principal del script."""
    config = None  # Inicializar para evitar UnboundLocalError
    try:
        config_path, data_file, confirm_week, fix_week, query_week, empty_week, test = get_config_path()
        config = load_config(config_path)
        
        # Configurar logging
        setup_logging(config.get('debug', False))
        
        # Verificar si se solicitó una prueba de conexión SSL
        if test:
            test_ssl_connection(config)
            print("Conexión SSL verificada correctamente")
            return
        
        # Configurar logging
        setup_logging(config.get('debug', False))
        
        # Obtener el código de compañía desde las variables de entorno
        company = os.getenv('SSN_COMPANY')
        if not company:
            raise RuntimeError("Falta la variable de entorno SSN_COMPANY")
        
        # Iniciar sesión
        token = authenticate(config, config.get('debug', False))
        
        # Número máximo de reintentos (por defecto 3 si no está especificado)
        max_retries = config.get('retries', 3)
        
        if query_week:
            for attempt in range(1, max_retries + 1):
                try:
                    if query_semana(token, company, query_week, attempt, config.get('debug', False), config):
                        break
                except RuntimeError as e:
                    if attempt == max_retries:
                        raise
                    print(f"Intento {attempt} fallido: {str(e)}")
        elif fix_week:
            for attempt in range(1, max_retries + 1):
                try:
                    if fix_semana(token, company, fix_week, attempt, config.get('debug', False), config):
                        break
                except RuntimeError as e:
                    if attempt == max_retries:
                        raise
                    print(f"Intento {attempt} fallido: {str(e)}")
        elif empty_week:
            for attempt in range(1, max_retries + 1):
                try:
                    if send_empty_week(token, company, empty_week, attempt, config.get('debug', False), config):
                        break
                except RuntimeError as e:
                    if attempt == max_retries:
                        raise
                    print(f"Intento {attempt} fallido: {str(e)}")
        else:
            # Cargar datos desde el archivo JSON
            data = load_data(data_file)
            
            # Intentar enviar los datos con reintentos
            for attempt in range(1, max_retries + 1):
                try:
                    if enviar_entrega(token, company, data["OPERACIONES"], data["CRONOGRAMA"], 
                                    attempt, config.get('debug', False), config):
                        break
                except RuntimeError as e:
                    if attempt == max_retries:
                        raise
                    print(f"Intento {attempt} fallido: {str(e)}")
            
            # Si se solicitó confirmar la entrega
            if confirm_week:
                for attempt in range(1, max_retries + 1):
                    try:
                        if confirmar_entrega(token, company, data["CRONOGRAMA"], 
                                          attempt, config.get('debug', False), config):
                            # Si la confirmación fue exitosa, mover el archivo
                            mover_archivo_procesado(data_file)
                            break
                    except RuntimeError as e:
                        if attempt == max_retries:
                            raise
                        print(f"Intento {attempt} fallido: {str(e)}")
    
    except ValueError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        # Errores esperados del API o de validación
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Errores inesperados
        if config and config.get('debug', False):
            import traceback
            traceback.print_exc()
        else:
            print(f"\nError inesperado: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
