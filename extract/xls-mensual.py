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

Autor: [Tu Nombre]
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
    try:
        if pd.isna(value):
            return 0
        return round(float(str(value).replace(",", ".")), decimals)
    except:
        return 0

def process_inversiones(df):
    records = []
    for idx, row in df.iterrows():
        try:
            record = {
                "TIPOSTOCK": "I",
                "TIPOESPECIE": str(row["TIPOESPECIE"]),
                "CODIGOESPECIE": str(row["CODIGOESPECIE"]),
                "CANTIDADDEVENGADOESPECIES": format_number(row["CANTIDADDEVENGADOESPECIES"], 6),
                "CANTIDADPERCIBIDOESPECIES": format_number(row["CANTIDADPERCIBIDOESPECIES"], 6),
                "CODIGOAFECTACION": int(row["CODIGOAFECTACION"]),
                "TIPOVALUACION": str(row["TIPOVALUACION"]),
                "CONCOTIZACION": int(row["CONCOTIZACION"]),
                "LIBREDISPONIBILIDAD": int(row["LIBREDISPONIBILIDAD"]),
                "EMISORGRUPOECONOMICO": int(row["EMISORGRUPOECONOMICO"]),
                "EMISORARTRET": int(row["EMISORARTRET"]),
                "PREVISIONDESVALORIZACION": int(row["PREVISIONDESVALORIZACION"]),
                "VALORCONTABLE": int(row["VALORCONTABLE"]),
                "FECHAPASEVT": "" if pd.isna(row["FECHAPASEVT"]) else str(int(row["FECHAPASEVT"])),
                "PRECIOPASEVT": format_number(row["PRECIOPASEVT"], 2),
                "ENCUSTODIA": int(row["ENCUSTODIA"]),
                "FINANCIERA": int(row["FINANCIERA"]),
                "VALORFINANCIERO": int(row["VALORFINANCIERO"])
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
                "TIPOSTOCK": "P",
                "TIPOPF": str(row["TIPOPF"]),
                "BIC": str(row["BIC"]),
                "CDF": str(row["CDF"]),
                "FECHACONSTITUCION": format_fecha_ddmmaaaa(row["FECHACONSTITUCION"]),
                "FECHAVENCIMIENTO": format_fecha_ddmmaaaa(row["FECHAVENCIMIENTO"]),
                "MONEDA": str(row["MONEDA"]),
                "VALORNOMINALORIGEN": int(row["VALORNOMINALORIGEN"]),
                "VALORNOMINALNACIONAL": int(row["VALORNOMINALNACIONAL"]),
                "EMISORGRUPOECONOMICO": int(row["EMISORGRUPOECONOMICO"]),
                "LIBREDISPONIBILIDAD": int(row["LIBREDISPONIBILIDAD"]),
                "ENCUSTODIA": int(row["ENCUSTODIA"]),
                "CODIGOAFECTACION": int(row["CODIGOAFECTACION"]),
                "TIPOTASA": str(row["TIPOTASA"]),
                "TASA": format_number(row["TASA"], 3),
                "TITULODEUDA": int(row["TITULODEUDA"]),
                "CODIGOTITULO": str(row["CODIGOTITULO"]),
                "VALORCONTABLE": int(row["VALORCONTABLE"]),
                "FINANCIERA": int(row["FINANCIERA"])
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
                "TIPOSTOCK": "C",
                "CODIGOSGR": str(row["CODIGOSGR"]),
                "CODIGOCHEQUE": str(row["CODIGOCHEQUE"]),
                "FECHAEMISION": format_fecha_ddmmaaaa(row["FECHAEMISION"]),
                "FECHAVENCIMIENTO": format_fecha_ddmmaaaa(row["FECHAVENCIMIENTO"]),
                "MONEDA": str(row["MONEDA"]),
                "VALORNOMINAL": int(row["VALORNOMINAL"]),
                "VALORADQUISICION": int(row["VALORADQUISICION"]),
                "EMISORGRUPOECONOMICO": int(row["EMISORGRUPOECONOMICO"]),
                "LIBREDISPONIBILIDAD": int(row["LIBREDISPONIBILIDAD"]),
                "ENCUSTODIA": int(row["ENCUSTODIA"]),
                "CODIGOAFECTACION": str(row["CODIGOAFECTACION"]),
                "TIPOTASA": str(row["TIPOTASA"]),
                "TASA": format_number(row["TASA"], 2),
                "VALORCONTABLE": int(row["VALORCONTABLE"]),
                "FINANCIERA": int(row["FINANCIERA"]),
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
