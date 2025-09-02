#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para procesar archivos Excel y generar JSONs para el sistema de la SSN.

Este script procesa archivos Excel que contienen datos de operaciones semanales
y los convierte al formato JSON requerido por la Superintendencia de Seguros
de la Nación (SSN). Maneja cuatro tipos de operaciones:
1. Compras
2. Ventas
3. Canjes
4. Plazos Fijos

El script realiza las siguientes tareas:
- Lee archivos Excel con múltiples hojas
- Procesa y valida los datos según los requerimientos de la SSN
- Formatea fechas y números según las especificaciones
- Genera archivos JSON por semana
- Agrupa operaciones por cronograma semanal

Uso:
    python xls-semanal.py --xls-path EXCEL_FILE [--config CONFIG_FILE]

Argumentos:
    --xls-path: Ruta al archivo Excel a procesar
    --config: Ruta al archivo de configuración (opcional)

El archivo de configuración (config.json) debe contener:
    {
        "decimal_separator": separador decimal a usar ("." o ","),
        "date_format": formato de fecha ("DDMMYYYY", "YYYYMMDD", "MMDDYYYY"),
        "company": código de la compañía
    }

Estructura del Excel requerida:
    - Hoja 'Compra': Operaciones de compra
    - Hoja 'Venta': Operaciones de venta
    - Hoja 'Canje': Operaciones de canje
    - Hoja 'Plazo-Fijo': Operaciones de plazo fijo

Autor: G. Casanova
Fecha: Junio 2025
"""

import pandas as pd
import os
import json
import re
import argparse
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
from collections import defaultdict

def get_config_path():
    """Obtiene la ruta del archivo de configuración y el archivo Excel.
    
    Busca primero en los argumentos de línea de comando, 
    si no encuentra usa el config.json en el directorio del script.
    """
    parser = argparse.ArgumentParser(description='Procesa archivo Excel con datos semanales')
    parser.add_argument('--config', help='Ruta al archivo de configuración')
    parser.add_argument('--xls-path', help='Ruta al archivo Excel a procesar', required=True)
    args = parser.parse_args()
    
    if args.config:
        if not os.path.isfile(args.config):
            raise FileNotFoundError(f"El archivo de configuración '{args.config}' no existe.")
        config_path = args.config
    else:
        # Si no se especifica, usar el config-semanal.json en el directorio del script
        config_path = os.path.join(os.path.dirname(__file__), 'config-semanal.json')
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"No se encuentra el archivo de configuración por defecto en '{config_path}'")
    
    return config_path, args.xls_path

def load_config():
    config_path, xls_path = get_config_path()
    with open(config_path, 'r') as f:
        config = json.load(f)
    # Sobreescribir xls_path con el valor de línea de comando
    config['xls_path'] = xls_path
    
    # Usar SSN_COMPANY desde variables de entorno
    company = os.getenv('SSN_COMPANY')
    if not company:
        raise ValueError("La variable de entorno SSN_COMPANY no está definida")
    config['company'] = company
    
    return config

def convert_excel_date(excel_number):
    """Convierte un número de fecha de Excel a objeto datetime.
    
    Args:
        excel_number (int/float): Número que representa una fecha en Excel.
            Excel usa un sistema donde las fechas son números secuenciales,
            siendo 1 = 1/1/1900. Los decimales representan la hora del día.
        
    Returns:
        datetime: Objeto datetime si la conversión es exitosa
        None: Si la entrada es inválida o la conversión falla
        
    Notas:
        - Excel tiene un error histórico donde considera 1900 como año bisiesto
        - Los números < 60 representan fechas de enero y febrero de 1900
        - Se resta 1 día para números >= 60 para compensar el error del año bisiesto
    """
    try:
        # Validar que es un número positivo
        if not isinstance(excel_number, (int, float)) or excel_number < 0:
            return None
            
        # Manejar el error del año bisiesto 1900 en Excel
        if excel_number < 60:
            base_date = datetime(1900, 1, 1)
            days_to_add = int(excel_number - 1)
        else:
            base_date = datetime(1900, 1, 1)
            days_to_add = int(excel_number - 2)
            
        try:
            return pd.Timestamp.fromordinal(base_date.toordinal() + days_to_add)
        except (ValueError, OverflowError):
            return None
            
    except Exception:
        return None

def convert_date_format(date_str, from_format, to_format):
    """Convierte una fecha string de un formato a otro.
    
    Args:
        date_str: String que representa la fecha
        from_format: Formato original ('DDMMYYYY', 'YYYYMMDD', 'MMDDYYYY')
        to_format: Formato destino ('DDMMYYYY', 'YYYYMMDD', 'MMDDYYYY')
        
    Returns:
        str: Fecha en el formato destino o None si la conversión falla
    """
    try:
        # Limpiar y validar entrada
        if not isinstance(date_str, str):
            date_str = str(int(date_str))
        
        date_str = date_str.strip()
        if len(date_str) != 8:
            return None
            
        # Extraer componentes según formato origen
        if from_format == 'DDMMYYYY':
            day = int(date_str[:2])
            month = int(date_str[2:4])
            year = int(date_str[4:])
        elif from_format == 'YYYYMMDD':
            year = int(date_str[:4])
            month = int(date_str[4:6])
            day = int(date_str[6:])
        elif from_format == 'MMDDYYYY':
            month = int(date_str[:2])
            day = int(date_str[2:4])
            year = int(date_str[4:])
        else:
            return None
            
        # Validar componentes
        if not (1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100):
            return None
            
        # Validar días según el mes
        days_in_month = {
            2: 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
            4: 30, 6: 30, 9: 30, 11: 30
        }
        max_days = days_in_month.get(month, 31)
        if day > max_days:
            return None
            
        # Generar salida según formato destino
        if to_format == 'YYYYMMDD':
            return f"{year:04d}{month:02d}{day:02d}"
        elif to_format == 'DDMMYYYY':
            return f"{day:02d}{month:02d}{year:04d}"
        elif to_format == 'MMDDYYYY':
            return f"{month:02d}{day:02d}{year:04d}"
        else:
            return None
            
    except (ValueError, IndexError, TypeError):
        return None

def format_number(number, decimal_separator='.', is_fc=False):
    """Formatea números según los requerimientos de la SSN.
    
    Args:
        number (int/float/str): Número a formatear
        decimal_separator (str): Separador decimal a usar ('.' o ',')
        is_fc (bool): Si es True, aplica reglas especiales para Fondos Comunes
    
    Returns:
        str: Número formateado según las reglas:
            - FC: 6 decimales, máx 14 dígitos enteros
            - Otros: Sin decimales, máximo 14 dígitos
        
    Raises:
        ValueError: Si el número excede los límites o el formato es inválido
    """
    if pd.isna(number):
        return ""
    try:
        # Convertir a número
        if isinstance(number, str):
            number = number.strip()
            if ',' in number and decimal_separator == '.':
                number = number.replace(',', '.')
            elif '.' in number and decimal_separator == ',':
                number = number.replace('.', ',')
        
        # Convertir a float
        value = float(str(number).replace(',', '.'))
        
        if is_fc:
            # Para FC, formato con 6 decimales
            if abs(value) > 99999999999999.999999:  # 14 dígitos enteros + 6 decimales
                raise ValueError(f"Valor {value} excede el límite de 14 dígitos enteros y 6 decimales")
            return f"{value:.6f}".replace('.', decimal_separator)
        else:
            # Para otros tipos, formato entero
            if abs(value) > 99999999999999:  # 14 dígitos enteros
                raise ValueError(f"Valor {value} excede el límite de 14 dígitos enteros")
            return str(int(round(value)))  # Redondear y convertir a entero
            
            # Si el número usa un separador diferente al configurado, sugerir cambio
            if has_comma and decimal_separator == '.':
                raise ValueError(
                    f"El número '{number}' usa coma como separador decimal, pero está configurado punto (.). "
                    "Por favor, modifique el archivo 'extract/config_xls.json' y configure "
                    "'decimal_separator': ',' para que coincida con el formato del Excel."
                )
            elif has_point and decimal_separator == ',':
                raise ValueError(
                    f"El número '{number}' usa punto como separador decimal, pero está configurado coma (,). "
                    "Por favor, modifique el archivo 'extract/config_xls.json' y configure "
                    "'decimal_separator': '.' para que coincida con el formato del Excel."
                )
            
            # Convertir según el separador configurado
            if decimal_separator == ',':
                return float(number.replace(',', '.'))
            return float(number)
        
        return 0.0
    except ValueError as e:
        print(f"\nError de formato numérico: {str(e)}")
        raise

def format_date(date, date_format='DDMMYYYY'):
    """Formatea fechas al formato requerido por la SSN.
    
    Args:
        date: Fecha a formatear. Puede ser:
            - datetime/pd.Timestamp
            - número de Excel
            - string en formato DDMMYYYY/YYYYMMDD
            - None/NaT/NaN
        date_format (str): Formato deseado:
            - 'DDMMYYYY': día/mes/año (por defecto)
            - 'YYYYMMDD': año/mes/día
            - 'MMDDYYYY': mes/día/año
    
    Returns:
        str: Fecha formateada en el formato especificado
        str vacío: Si la entrada es None/NaT/NaN
        
    Raises:
        ValueError: Si la fecha no se puede convertir al formato especificado
    """
    if pd.isna(date):
        return ""
    
    try:
        # Si es un número, primero intentar como fecha de Excel
        if isinstance(date, (int, float)):
            excel_date = convert_excel_date(date)
            if excel_date is not None:
                format_map = {
                    'DDMMYYYY': '%d%m%Y',
                    'YYYYMMDD': '%Y%m%d',
                    'MMDDYYYY': '%m%d%Y'
                }
                return excel_date.strftime(format_map.get(date_format, '%d%m%Y'))
            
            # Si no es fecha Excel válida, intentar como string numérico
            date_str = str(int(date))
            if len(date_str) == 8:
                # Detectar formato de entrada basado en el año
                potential_year = int(date_str[:4])
                if 1900 <= potential_year <= 2100:
                    # Probablemente YYYYMMDD
                    from_format = 'YYYYMMDD'
                else:
                    # Asumimos DDMMYYYY
                    from_format = 'DDMMYYYY'
                
                result = convert_date_format(date_str, from_format, date_format)
                if result:
                    return result
        
        # Si es datetime/Timestamp
        if isinstance(date, (datetime, pd.Timestamp)):
            format_map = {
                'DDMMYYYY': '%d%m%Y',
                'YYYYMMDD': '%Y%m%d',
                'MMDDYYYY': '%m%d%Y'
            }
            return date.strftime(format_map.get(date_format, '%d%m%Y'))
            
        # Si es string, intentar convertir
        if isinstance(date, str):
            date = date.strip()
            if len(date) == 8 and date.isdigit():
                # Detectar formato de entrada
                potential_year = int(date[:4])
                if 1900 <= potential_year <= 2100:
                    from_format = 'YYYYMMDD'
                else:
                    from_format = 'DDMMYYYY'
                    
                result = convert_date_format(date, from_format, date_format)
                if result:
                    return result
        
        # Si llegamos aquí, no pudimos convertir la fecha
        raise ValueError(f"No se pudo convertir la fecha '{date}' ({type(date)}) al formato {date_format}")
        
    except ValueError as e:
        print(f"\nError al formatear fecha: {str(e)}")
        if isinstance(date, (int, float)):
            print(f"Sugerencia: Revise si el valor {date} es realmente una fecha")
        elif isinstance(date, str):
            print(f"Sugerencia: Verifique que '{date}' esté en alguno de los formatos soportados")
        raise
    except Exception as e:
        print(f"\nError inesperado al formatear fecha: {str(e)}")
        raise

def validate_date_format(date_str, expected_format):
    """Valida si una fecha string está en el formato esperado."""
    format_map = {
        'DDMMYYYY': r'^(0[1-9]|[12][0-9]|3[01])(0[1-9]|1[0-2])\d{4}$',
        'YYYYMMDD': r'^\d{4}(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])$',
        'MMDDYYYY': r'^(0[1-9]|1[0-2])(0[1-9]|[12][0-9]|3[01])\d{4}$'
    }
    import re
    pattern = format_map.get(expected_format)
    if not pattern:
        raise ValueError(f"Formato de fecha no soportado: {expected_format}")
    return bool(re.match(pattern, date_str))

def process_compra(df, decimal_separator='.', date_format='DDMMYYYY'):
    """Procesa operaciones de compra desde un DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame con las operaciones de compra
        decimal_separator (str): Separador decimal a usar
        date_format (str): Formato para las fechas
    
    Returns:
        list: Lista de diccionarios con las operaciones procesadas
        
    Cada registro incluye:
        - TIPOOPERACION: Siempre "C" para compras
        - TIPOESPECIE: Tipo de especie
        - CODIGOESPECIE: Código de la especie
        - CANTESPECIES: Cantidad (formato especial para FC)
        - CODIGOAFECTACION: Código de afectación
        - TIPOVALUACION: Tipo de valuación
        - FECHAMOVIMIENTO: Fecha del movimiento
        - PRECIOCOMPRA: Precio de compra
        - FECHALIQUIDACION: Fecha de liquidación
    """
    records = []
    for _, row in df.iterrows():
        is_fc = str(row['TIPOESPECIE']).strip() == 'FC'
        record = {
            "TIPOOPERACION": "C",
            "TIPOESPECIE": str(row['TIPOESPECIE']),
            "CODIGOESPECIE": str(row['CODIGOESPECIE']),
            "CANTESPECIES": format_number(row['CANTESPECIES'], decimal_separator, is_fc),
            "CODIGOAFECTACION": str(row['CODIGOAFECTACION']),
            "TIPOVALUACION": str(row['TIPOVALUACION']),
            "FECHAMOVIMIENTO": format_date(row['FECHAMOVIMIENTO'], date_format),
            "PRECIOCOMPRA": format_number(row['PRECIOCOMPRA'], decimal_separator),
            "FECHALIQUIDACION": format_date(row['FECHALIQUIDACION'], date_format),
            "__CRONOGRAMA": str(row['CRONOGRAMA'])
        }
        records.append(record)
    return records

def process_venta(df, decimal_separator='.', date_format='DDMMYYYY'):
    """Procesa operaciones de venta desde un DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame con las operaciones de venta
        decimal_separator (str): Separador decimal a usar
        date_format (str): Formato para las fechas
    
    Returns:
        list: Lista de diccionarios con las operaciones procesadas
        
    Cada registro incluye los campos de compra más:
        - FECHAPASEVT: Fecha de pase (opcional)
        - PRECIOPASEVT: Precio de pase (opcional)
        - PRECIOVENTA: Precio de venta
    """
    records = []
    for _, row in df.iterrows():
        is_fc = str(row['TIPOESPECIE']).strip() == 'FC'
        record = {
            "TIPOOPERACION": "V",
            "TIPOESPECIE": str(row['TIPOESPECIE']),
            "CODIGOESPECIE": str(row['CODIGOESPECIE']),
            "CANTESPECIES": format_number(row['CANTESPECIES'], decimal_separator, is_fc),
            "CODIGOAFECTACION": str(row['CODIGOAFECTACION']),
            "TIPOVALUACION": str(row['TIPOVALUACION']),
            "FECHAMOVIMIENTO": format_date(row['FECHAMOVIMIENTO'], date_format),
            "FECHAPASEVT": format_date(row['FECHAPASEVT'], date_format) if 'FECHAPASEVT' in row else "",
            "PRECIOPASEVT": format_date(row['PRECIOPASEVT']) if 'PRECIOPASEVT' in row else "",
            "FECHALIQUIDACION": format_date(row['FECHALIQUIDACION'], date_format),
            "PRECIOVENTA": format_number(row['PRECIOVENTA'], decimal_separator),
            "__CRONOGRAMA": str(row['CRONOGRAMA'])
        }
        records.append(record)
    return records

def process_canje(df, decimal_separator='.', date_format='DDMMYYYY'):
    """Procesa operaciones de canje desde un DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame con las operaciones de canje
        decimal_separator (str): Separador decimal a usar
        date_format (str): Formato para las fechas
    
    Returns:
        list: Lista de diccionarios con las operaciones procesadas
        
    Cada registro incluye campos para ambas especies (A y B):
        - TIPOESPECIEA/B: Tipo de especie
        - CODIGOESPECIEA/B: Código de la especie
        - CANTESPECIESA/B: Cantidad
        - CODIGOAFECTACIONA/B: Código de afectación
        - TIPOVALUACIONA/B: Tipo de valuación
        - FECHAPASEVTA/B: Fecha de pase (opcional)
        - PRECIOPASEVTA/B: Precio de pase (opcional)
    """
    records = []
    for _, row in df.iterrows():
        is_fc_a = str(row['TIPOESPECIEA']).strip() == 'FC'
        is_fc_b = str(row['TIPOESPECIEB']).strip() == 'FC'
        record = {
            "TIPOOPERACION": "J",
            "TIPOESPECIEA": str(row['TIPOESPECIEA']),
            "CODIGOESPECIEA": str(row['CODIGOESPECIEA']),
            "CANTESPECIESA": format_number(row['CANTESPECIESA'], decimal_separator, is_fc_a),
            "CODIGOAFECTACIONA": str(row['CODIGOAFECTACIONA']),
            "TIPOVALUACIONA": str(row['TIPOVALUACIONA']),
            "FECHAPASEVTA": format_date(row['FECHAPASEVTA'], date_format) if 'FECHAPASEVTA' in row else "",
            "PRECIOPASEVTA": format_date(row['PRECIOPASEVTA']) if 'PRECIOPASEVTA' in row else "",
            "TIPOESPECIEB": str(row['TIPOESPECIEB']),
            "CODIGOESPECIEB": str(row['CODIGOESPECIEB']),
            "CANTESPECIESB": format_number(row['CANTESPECIESB'], decimal_separator, is_fc_b),
            "CODIGOAFECTACIONB": str(row['CODIGOAFECTACIONB']),
            "TIPOVALUACIONB": str(row['TIPOVALUACIONB']),
            "FECHAPASEVTB": format_date(row['FECHAPASEVTB'], date_format) if 'FECHAPASEVTB' in row else "",
            "PRECIOPASEVTB": format_date(row['PRECIOPASEVTB']) if 'PRECIOPASEVTB' in row else "",
            "FECHAMOVIMIENTO": format_date(row['FECHAMOVIMIENTO'], date_format),
            "FECHALIQUIDACION": format_date(row['FECHALIQUIDACION'], date_format),
            "__CRONOGRAMA": str(row['CRONOGRAMA'])
        }
        records.append(record)
    return records

def process_plazo_fijo(df, decimal_separator='.', date_format='DDMMYYYY'):
    """Procesa operaciones de plazo fijo desde un DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame con las operaciones de plazo fijo
        decimal_separator (str): Separador decimal a usar
        date_format (str): Formato para las fechas
    
    Returns:
        list: Lista de diccionarios con las operaciones procesadas
        
    Cada registro incluye:
        - TIPOOPERACION: Siempre "P" para plazos fijos
        - TIPOPF: Tipo de plazo fijo
        - BIC: Código BIC
        - CDF: Código CDF
        - FECHACONSTITUCION: Fecha de constitución
        - FECHAVENCIMIENTO: Fecha de vencimiento
        - MONEDA: Moneda del plazo fijo
        - VALORNOMINALORIGEN: Valor nominal en origen
        - VALORNOMINALNACIONAL: Valor nominal en moneda nacional
        - CODIGOAFECTACION: Código de afectación
        - TIPOTASA: Tipo de tasa
        - TASA: Tasa de interés
        - TITULODEUDA: Título de deuda (número entero)
        - CODIGOTITULO: Código de título (opcional)
    """
    records = []
    for _, row in df.iterrows():
        record = {
            "TIPOOPERACION": "P",
            "TIPOPF": str(row['TIPOPF']),
            "BIC": str(row['BIC']),
            "CDF": str(row['CDF']),
            "FECHACONSTITUCION": format_date(row['FECHACONSTITUCION'], date_format),
            "FECHAVENCIMIENTO": format_date(row['FECHAVENCIMIENTO'], date_format),
            "MONEDA": str(row['MONEDA']),
            "VALORNOMINALORIGEN": format_number(row['VALORNOMINALORIGEN'], decimal_separator),
            "VALORNOMINALNACIONAL": format_number(row['VALORNOMINALNACIONAL'], decimal_separator),
            "CODIGOAFECTACION": str(row['CODIGOAFECTACION']),
            "TIPOTASA": str(row['TIPOTASA']),
            "TASA": format_number(row['TASA'], decimal_separator),
            "TITULODEUDA": int(row['TITULODEUDA']),
            "CODIGOTITULO": str(row['CODIGOTITULO'] if not pd.isna(row['CODIGOTITULO']) else ""),
            "__CRONOGRAMA": str(row['CRONOGRAMA'])  # Campo auxiliar para agrupar por semana
        }
        records.append(record)
    return records

def agrupar_por_semana(operaciones):
    """Agrupa las operaciones por semana usando el campo __CRONOGRAMA.
    
    Args:
        operaciones (list): Lista de diccionarios con las operaciones
    
    Returns:
        dict: Diccionario donde:
            - Claves: Cronogramas (formato YYYY-WW)
            - Valores: Listas de operaciones de esa semana
            
    Notas:
        - Elimina el campo auxiliar __CRONOGRAMA de cada operación
        - Mantiene el orden original de las operaciones en cada semana
    """
    operaciones_por_semana = defaultdict(list)
    
    for op in operaciones:
        cronograma = op.pop('__CRONOGRAMA', None)  # Eliminar campo auxiliar y obtener valor
        if cronograma:
            operaciones_por_semana[cronograma].append(op)
    
    return dict(operaciones_por_semana)

def guardar_json_por_semana(codigo_compania, operaciones_por_semana):
    """Guarda archivos JSON separados para cada semana.
    
    Args:
        codigo_compania (str): Código de la compañía para los JSONs
        operaciones_por_semana (dict): Operaciones agrupadas por semana
    
    Returns:
        list: Lista de tuplas (nombre_archivo, cantidad_operaciones)
        
    Formato del JSON generado:
        {
            "CODIGOCOMPANIA": str,
            "TIPOENTREGA": "SEMANAL",
            "CRONOGRAMA": "YYYY-WW",
            "OPERACIONES": [...]
        }
    """
    archivos_generados = []
    
    for cronograma, operaciones in operaciones_por_semana.items():
        # Crear el JSON
        output_data = {
            "CODIGOCOMPANIA": codigo_compania,
            "TIPOENTREGA": "SEMANAL",
            "CRONOGRAMA": cronograma,
            "OPERACIONES": operaciones
        }
        
        # Extraer año y semana del cronograma (formato YYYY-SS)
        year, week = cronograma.split('-')
        
        # Generar nombre del archivo de salida
        output_filename = f"Semana{week}.json"
        output_path = os.path.join('data', output_filename)
        
        # Guardar el JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
            
        archivos_generados.append((output_filename, len(operaciones)))
    
    return archivos_generados

def generate_empty_week_json(codigo_compania, cronograma):
    """Genera un archivo JSON con solo la cabecera para una semana específica."""
    output_data = {
        "CODIGOCOMPANIA": codigo_compania,
        "TIPOENTREGA": "SEMANAL",
        "CRONOGRAMA": cronograma
    }
    
    # Extraer semana del cronograma
    _, week = cronograma.split('-')
    
    # Generar nombre del archivo
    output_filename = f"Semana{week}.json"
    output_path = os.path.join('data', output_filename)
    
    # Guardar el JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    return output_filename

def validate_week_format(week_str):
    """Valida que una cadena tenga formato de semana válido.
    
    Args:
        week_str (str): Cadena a validar (formato esperado: YYYY-WW)
    
    Returns:
        bool: True si el formato es válido y los valores son razonables:
            - Año entre 2000 y 2100
            - Semana entre 1 y 53
    """
    if not re.match(r'^\d{4}-\d{2}$', week_str):
        return False
    
    try:
        year, week = map(int, week_str.split('-'))
        return 2000 <= year <= 2100 and 1 <= week <= 53
    except ValueError:
        return False

def main():
    try:
        print("📊 === Procesador de datos semanales SSN ===")
        print("🔧 Iniciando procesamiento...")
        
        # Cargar configuración
        config = load_config()
        
        # Procesar configuración
        decimal_separator = config.get('decimal_separator', '.')
        date_format = config.get('date_format', 'DDMMYYYY')
        xls_path = config.get('xls_path')
        company = config.get('company')
        
        if not all([xls_path, company]):
            raise ValueError("Faltan parámetros obligatorios en la configuración (xls_path, company)")
            
        # Verificar que el archivo Excel existe
        if not os.path.isfile(xls_path):
            raise FileNotFoundError(f"No se encuentra el archivo Excel en '{xls_path}'")
            
        print(f"📁 Leyendo archivo: {os.path.basename(xls_path)}")
        
        # Leer las hojas del Excel
        df_compra = pd.read_excel(xls_path, sheet_name='Compra')
        df_venta = pd.read_excel(xls_path, sheet_name='Venta')
        df_canje = pd.read_excel(xls_path, sheet_name='Canje')
        df_plazo = pd.read_excel(xls_path, sheet_name='Plazo-Fijo')
        
        print("📋 Procesando hojas del Excel:")
        print(f"  • Compra: {len(df_compra)} operaciones")
        print(f"  • Venta: {len(df_venta)} operaciones")
        print(f"  • Canje: {len(df_canje)} operaciones")
        print(f"  • Plazo-Fijo: {len(df_plazo)} operaciones")
        
        # Procesar cada tipo de operación
        operaciones = []
        operaciones.extend(process_compra(df_compra, decimal_separator, date_format))
        operaciones.extend(process_venta(df_venta, decimal_separator, date_format))
        operaciones.extend(process_canje(df_canje, decimal_separator, date_format))
        operaciones.extend(process_plazo_fijo(df_plazo, decimal_separator, date_format))
        
        # Agrupar por semana y generar JSONs
        operaciones_por_semana = agrupar_por_semana(operaciones)
        archivos = guardar_json_por_semana(company, operaciones_por_semana)
        
        # Informar resultado
        print("✅ Procesamiento completado")
        total_operaciones = sum(cantidad for _, cantidad in archivos)
        print(f"📊 Total de operaciones procesadas: {total_operaciones}")
        print("📄 Archivos generados:")
        for archivo, cantidad in archivos:
            print(f"  • {archivo}: {cantidad} operaciones")
            
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
