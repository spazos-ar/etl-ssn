#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para procesar archivos Excel y generar JSON mensual para el sistema de la SSN.

Este script procesa archivos Excel que contienen datos de inversiones mensuales,
plazos fijos y cheques de pago diferido, y los convierte al formato JSON requerido
por la Superintendencia de Seguros de la Nación (SSN).

El script realiza las siguientes tareas:
- Lee archivos Excel con múltiples hojas
- Procesa y valida los datos según los requerimientos de la SSN
- Formatea fechas y números según las especificaciones
- Genera un archivo JSON mensual

Uso:
    python xls-mensual.py --xls-path EXCEL_FILE [--config CONFIG_FILE]

Argumentos:
    --xls-path: Ruta al archivo Excel a procesar
    --config: Ruta al archivo de configuración (opcional)

El archivo de configuración debe contener:
    {
        "company": "Código de la compañía",
        "decimal_separator": ",",
        "date_format": "DDMMYYYY"
    }

Estructura del Excel requerida:
    - Hoja 'Inversiones': Inversiones mensuales
    - Hoja 'Plazo-Fijo': Plazos fijos
    - Hoja 'Cheques': Cheques de pago diferido

Autor: G. Casanova
Fecha: Junio 2025
"""

import pandas as pd
import os
import json
import argparse
import sys
from datetime import datetime

def get_config_path():
    """Obtiene la ruta del archivo de configuración y el archivo Excel.
    Busca primero en los argumentos de línea de comando, 
    si no encuentra usa el config.json en el directorio del script.
    """
    parser = argparse.ArgumentParser(description='Procesa archivo Excel mensual para SSN')
    parser.add_argument('--config', help='Ruta al archivo de configuración')
    parser.add_argument('--xls-path', help='Ruta al archivo Excel a procesar', required=True)
    args = parser.parse_args()
    
    if args.config:
        if not os.path.isfile(args.config):
            raise FileNotFoundError(f"El archivo de configuración '{args.config}' no existe.")
        config_path = args.config
    else:
        config_path = os.path.join(os.path.dirname(__file__), 'config-mensual.json')
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"No se encuentra el archivo de configuración por defecto en '{config_path}'")
    
    return config_path, args.xls_path

def load_config():
    config_path, xls_path = get_config_path()
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    config['xls_path'] = xls_path
    
    # Usar SSN_COMPANY desde variables de entorno
    company = os.getenv('SSN_COMPANY')
    if not company:
        raise ValueError("La variable de entorno SSN_COMPANY no está definida")
    config['company'] = company
    
    return config

def format_date(value):
    if pd.isna(value):
        return ""
    try:
        if isinstance(value, datetime):
            return value.strftime("%d%m%Y")
        if isinstance(value, (int, float)):
            return pd.to_datetime("1899-12-30") + pd.to_timedelta(float(value), unit="D")
        return str(value)
    except:
        return str(value)

def format_number(value, decimals=0):
    """Formatea números con las siguientes reglas:
    - Si el valor es vacío/nulo, devuelve ""
    - Si el valor es entero, devuelve int aunque decimals>0
    - Si el valor tiene decimales, devuelve float con los decimales especificados
    """
    try:
        if pd.isna(value) or value == "":
            return ""
        
        # Convertir el valor a float
        num = float(str(value).replace(",", "."))
        
        # Si decimals=0 o el número es entero, devolver como int
        if decimals == 0 or num.is_integer():
            return int(num)
            
        # Si tiene decimales, redondear al número especificado de decimales
        return round(num, decimals)
    except:
        return ""

def process_inversiones(df):
    records = []
    for idx, row in df.iterrows():
        try:
            record = {
                "TIPO": "I",
                "TIPOESPECIE": str(row["TIPOESPECIE"]),
                "CODIGOESPECIE": str(row["CODIGOESPECIE"]),
                "CANTIDADDEVENGADOESPECIES": format_number(row["CANTIDADDEVENGADOESPECIES"], 0),
                "CANTIDADPERCIBIDOESPECIES": format_number(row["CANTIDADPERCIBIDOESPECIES"], 0),
                "CODIGOAFECTACION": format_number(row["CODIGOAFECTACION"], 0),
                "TIPOVALUACION": str(row["TIPOVALUACION"]),
                "CONCOTIZACION": format_number(row["CONCOTIZACION"], 0),
                "LIBREDISPONIBILIDAD": format_number(row["LIBREDISPONIBILIDAD"], 0),
                "EMISORGRUPOECONOMICO": format_number(row["EMISORGRUPOECONOMICO"], 0),
                "EMISORARTRET": format_number(row["EMISORARTRET"], 0),
                "PREVISIONDESVALORIZACION": format_number(row["PREVISIONDESVALORIZACION"], 0),
                "VALORCONTABLE": format_number(row["VALORCONTABLE"], 0),
                "FECHAPASEVT": format_number(row["FECHAPASEVT"], 0) if not pd.isna(row["FECHAPASEVT"]) else "",
                "PRECIOPASEVT": format_number(row["PRECIOPASEVT"], 2),
                "ENCUSTODIA": format_number(row["ENCUSTODIA"], 0),
                "FINANCIERA": format_number(row["FINANCIERA"], 0),
                "VALORFINANCIERO": format_number(row["VALORFINANCIERO"], 0)
            }
        except Exception as e:
            print(f"Error en fila {idx} de 'Inversiones': {e}")
            print(row)
            raise
        records.append(record)
    return records

def format_fecha_ddmmaaaa(value):
    """Convierte cualquier valor de fecha a string DDMMYYYY."""
    import pandas as pd
    if pd.isna(value) or value == "":
        return ""
    try:
        if isinstance(value, str):
            # Si ya está en formato DDMMYYYY
            if len(value) == 8 and value.isdigit():
                return value
            # Si es formato YYYY-MM-DD o YYYY-MM-DD HH:MM:SS
            if '-' in value:
                try:
                    dt = pd.to_datetime(value)
                    return dt.strftime("%d%m%Y")
                except Exception:
                    pass
        if isinstance(value, (int, float)):
            # Fecha Excel
            dt = pd.to_datetime("1899-12-30") + pd.to_timedelta(float(value), unit="D")
            return dt.strftime("%d%m%Y")
        if isinstance(value, pd.Timestamp) or isinstance(value, datetime):
            return value.strftime("%d%m%Y")
    except Exception:
        pass
    return str(value)

def process_plazo_fijo(df):
    records = []
    for idx, row in df.iterrows():
        try:
            record = {
                "TIPO": "P",
                "TIPOPF": str(row["TIPOPF"]),
                "BIC": str(row["BIC"]),
                "CDF": str(row["CDF"]),
                "FECHACONSTITUCION": format_fecha_ddmmaaaa(row["FECHACONSTITUCION"]),
                "FECHAVENCIMIENTO": format_fecha_ddmmaaaa(row["FECHAVENCIMIENTO"]),
                "MONEDA": str(row["MONEDA"]),
                "VALORNOMINALORIGEN": format_number(row["VALORNOMINALORIGEN"], 0),
                "VALORNOMINALNACIONAL": format_number(row["VALORNOMINALNACIONAL"], 0),
                "EMISORGRUPOECONOMICO": format_number(row["EMISORGRUPOECONOMICO"], 0),
                "LIBREDISPONIBILIDAD": format_number(row["LIBREDISPONIBILIDAD"], 0),
                "ENCUSTODIA": format_number(row["ENCUSTODIA"], 0),
                "CODIGOAFECTACION": format_number(row["CODIGOAFECTACION"], 0),
                "TIPOTASA": str(row["TIPOTASA"]),
                "TASA": format_number(row["TASA"], 3),
                "TITULODEUDA": format_number(row["TITULODEUDA"], 0),
                "CODIGOTITULO": str(row["CODIGOTITULO"]),
                "VALORCONTABLE": format_number(row["VALORCONTABLE"], 0),
                "FINANCIERA": format_number(row["FINANCIERA"], 0)
            }
        except Exception as e:
            print(f"Error en fila {idx} de 'Plazo-Fijo': {e}")
            print(row)
            raise
        records.append(record)
    return records

def process_cheques(df):
    records = []
    for idx, row in df.iterrows():
        try:
            record = {
                "TIPO": "C",
                "CODIGOSGR": str(row["CODIGOSGR"]),
                "CODIGOCHEQUE": str(row["CODIGOCHEQUE"]),
                "FECHAEMISION": format_fecha_ddmmaaaa(row["FECHAEMISION"]),
                "FECHAVENCIMIENTO": format_fecha_ddmmaaaa(row["FECHAVENCIMIENTO"]),
                "MONEDA": str(row["MONEDA"]),
                "VALORNOMINAL": format_number(row["VALORNOMINAL"], 0),
                "VALORADQUISICION": format_number(row["VALORADQUISICION"], 0),
                "EMISORGRUPOECONOMICO": format_number(row["EMISORGRUPOECONOMICO"], 0),
                "LIBREDISPONIBILIDAD": format_number(row["LIBREDISPONIBILIDAD"], 0),
                "ENCUSTODIA": format_number(row["ENCUSTODIA"], 0),
                "CODIGOAFECTACION": format_number(row["CODIGOAFECTACION"], 0),
                "TIPOTASA": str(row["TIPOTASA"]),
                "TASA": format_number(row["TASA"], 2),
                "VALORCONTABLE": format_number(row["VALORCONTABLE"], 0),
                "FINANCIERA": format_number(row["FINANCIERA"], 0),
                "FECHAADQUISICION": format_fecha_ddmmaaaa(row["FECHAADQUISICION"])
            }
        except Exception as e:
            print(f"Error en fila {idx} de 'Cheques': {e}")
            print(row)
            raise
        records.append(record)
    return records

def main():
    try:
        # Cargar configuración
        config = load_config()
        decimal_separator = config.get('decimal_separator', ',')
        date_format = config.get('date_format', 'DDMMYYYY')
        xls_path = config.get('xls_path')
        company = config.get('company')
        if not all([xls_path, company]):
            raise ValueError("Faltan parámetros obligatorios en la configuración (xls_path, company)")
        if not os.path.isfile(xls_path):
            raise FileNotFoundError(f"No se encuentra el archivo Excel en '{xls_path}'")
        xls = pd.ExcelFile(xls_path)
        df_inv = pd.read_excel(xls, "Stock-Inversiones")
        df_pf = pd.read_excel(xls, "Stock-Plazo-Fijo")
        df_cheq = pd.read_excel(xls, "Stock-CHPD")
        cronograma = df_inv["CRONOGRAMA"][0]
        # Formato Mes-YYYY-MM.json
        cronograma_str = str(cronograma).replace('_', '-')
        output_filename = f"Mes-{cronograma_str}.json"
        output_path = os.path.join("data", output_filename)
        all_records = []
        all_records += process_inversiones(df_inv)
        all_records += process_plazo_fijo(df_pf)
        all_records += process_cheques(df_cheq)
        output = {
            "CODIGOCOMPANIA": company,
            "TIPOENTREGA": "MENSUAL",
            "CRONOGRAMA": cronograma,
            "STOCKS": all_records
        }
        os.makedirs("data", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"Archivo generado: {output_path}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
