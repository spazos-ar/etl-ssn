import pandas as pd
import json
from datetime import datetime
import os
import re
from collections import defaultdict

def load_config():
    config_path = os.path.join('extract', 'config_xls.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def convert_excel_date(excel_number):
    """Convierte un número de Excel a datetime.
    
    Args:
        excel_number: Número que representa una fecha en Excel.
        
    Returns:
        datetime: Objeto datetime si la conversión es exitosa, None en caso contrario.
        
    El número de Excel representa días desde el 1/1/1900, con algunas peculiaridades:
    - Excel considera erróneamente que 1900 fue un año bisiesto
    - Los números decimales representan fracciones de día
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

def format_number(number, decimal_separator='.'):
    if pd.isna(number):
        return 0.0
    try:
        # Si es un número, convertirlo directamente
        if isinstance(number, (int, float)):
            return float(number)
        
        # Si es string, asegurar que usamos punto como separador decimal para float()
        if isinstance(number, str):
            # Limpiar el string de espacios
            number = number.strip()
            
            # Detectar el separador decimal usado en el número
            has_comma = ',' in number
            has_point = '.' in number
            
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
    """Formatea una fecha al formato especificado.
    
    Args:
        date: Valor a formatear. Puede ser:
            - datetime/Timestamp
            - número de Excel
            - string en formato DDMMYYYY/YYYYMMDD
            - None/NaT/NaN
        date_format: Formato deseado ('DDMMYYYY', 'YYYYMMDD', 'MMDDYYYY')
        
    Returns:
        str: Fecha formateada o string vacío si la entrada es inválida
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
    records = []
    for _, row in df.iterrows():
        record = {
            "TIPOOPERACION": "C",
            "TIPOESPECIE": str(row['TIPOESPECIE']),
            "CODIGOESPECIE": str(row['CODIGOESPECIE']),
            "CANTESPECIES": format_number(row['CANTESPECIES'], decimal_separator),
            "CODIGOAFECTACION": str(row['CODIGOAFECTACION']),
            "TIPOVALUACION": str(row['TIPOVALUACION']),
            "FECHAMOVIMIENTO": format_date(row['FECHAMOVIMIENTO'], date_format),
            "PRECIOCOMPRA": format_number(row['PRECIOCOMPRA'], decimal_separator),
            "FECHALIQUIDACION": format_date(row['FECHALIQUIDACION'], date_format),
            "__CRONOGRAMA": str(row['CRONOGRAMA'])  # Campo auxiliar para agrupar por semana
        }
        records.append(record)
    return records

def process_venta(df, decimal_separator='.', date_format='DDMMYYYY'):
    records = []
    for _, row in df.iterrows():
        record = {
            "TIPOOPERACION": "V",
            "TIPOESPECIE": str(row['TIPOESPECIE']),
            "CODIGOESPECIE": str(row['CODIGOESPECIE']),
            "CANTESPECIES": format_number(row['CANTESPECIES'], decimal_separator),
            "CODIGOAFECTACION": str(row['CODIGOAFECTACION']),
            "TIPOVALUACION": str(row['TIPOVALUACION']),
            "FECHAMOVIMIENTO": format_date(row['FECHAMOVIMIENTO'], date_format),
            "FECHAPASEVT": format_date(row['FECHAPASEVT'], date_format) if 'FECHAPASEVT' in row else "",
            "PRECIOPASEVT": str(row['PRECIOPASEVT']) if 'PRECIOPASEVT' in row else "",
            "FECHALIQUIDACION": format_date(row['FECHALIQUIDACION'], date_format),
            "PRECIOVENTA": format_number(row['PRECIOVENTA'], decimal_separator),
            "__CRONOGRAMA": str(row['CRONOGRAMA'])  # Campo auxiliar para agrupar por semana
        }
        records.append(record)
    return records

def process_canje(df, decimal_separator='.', date_format='DDMMYYYY'):
    records = []
    for _, row in df.iterrows():
        record = {
            "TIPOOPERACION": "J",
            "TIPOESPECIEA": str(row['TIPOESPECIEA']),
            "CODIGOESPECIEA": str(row['CODIGOESPECIEA']),
            "CANTESPECIESA": format_number(row['CANTESPECIESA'], decimal_separator),
            "CODIGOAFECTACIONA": str(row['CODIGOAFECTACIONA']),
            "TIPOVALUACIONA": str(row['TIPOVALUACIONA']),
            "FECHAPASEVTA": format_date(row['FECHAPASEVTA'], date_format) if 'FECHAPASEVTA' in row else "",
            "PRECIOPASEVTA": str(row['PRECIOPASEVTA']) if 'PRECIOPASEVTA' in row else "",
            "TIPOESPECIEB": str(row['TIPOESPECIEB']),
            "CODIGOESPECIEB": str(row['CODIGOESPECIEB']),
            "CANTESPECIESB": format_number(row['CANTESPECIESB'], decimal_separator),
            "CODIGOAFECTACIONB": str(row['CODIGOAFECTACIONB']),
            "TIPOVALUACIONB": str(row['TIPOVALUACIONB']),
            "FECHAPASEVTB": format_date(row['FECHAPASEVTB'], date_format) if 'FECHAPASEVTB' in row else "",
            "PRECIOPASEVTB": str(row['PRECIOPASEVTB']) if 'PRECIOPASEVTB' in row else "",
            "FECHAMOVIMIENTO": format_date(row['FECHAMOVIMIENTO'], date_format),
            "FECHALIQUIDACION": format_date(row['FECHALIQUIDACION'], date_format),
            "__CRONOGRAMA": str(row['CRONOGRAMA'])  # Campo auxiliar para agrupar por semana
        }
        records.append(record)
    return records

def process_plazo_fijo(df, decimal_separator='.', date_format='DDMMYYYY'):
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
    """Agrupa las operaciones por semana y elimina el campo auxiliar __CRONOGRAMA."""
    operaciones_por_semana = defaultdict(list)
    
    for op in operaciones:
        cronograma = op.pop('__CRONOGRAMA', None)  # Eliminar campo auxiliar y obtener valor
        if cronograma:
            operaciones_por_semana[cronograma].append(op)
    
    return dict(operaciones_por_semana)

def guardar_json_por_semana(codigo_compania, operaciones_por_semana):
    """Guarda un archivo JSON por cada semana encontrada."""
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

def main():
    try:
        # Cargar configuración
        config = load_config()
        
        # Obtener configuración de formato
        decimal_separator = config.get('decimal_separator', '.')
        date_format = config.get('date_format', 'DDMMYYYY')
        
        print(f"\nUsando configuración:")
        print(f"- Código de compañía: {config['company']}")
        print(f"- Separador decimal: {decimal_separator}")
        print(f"- Formato de fecha: {date_format}")
        
        # Leer el archivo Excel
        excel_path = os.path.join('data', 'datos_semanales.xlsx')
        print(f"\nLeyendo archivo Excel: {excel_path}")
        
        # Leer cada hoja del Excel sin convertir fechas y sin omitir filas
        compra_df = pd.read_excel(excel_path, sheet_name='Compra', parse_dates=False, skiprows=None)
        venta_df = pd.read_excel(excel_path, sheet_name='Venta', parse_dates=False, skiprows=None)
        canje_df = pd.read_excel(excel_path, sheet_name='Canje', parse_dates=False, skiprows=None)
        plazo_fijo_df = pd.read_excel(excel_path, sheet_name='Plazo-Fijo', parse_dates=False, skiprows=None)
        
        # Verificar que los DataFrames no estén vacíos
        if compra_df.empty or venta_df.empty or canje_df.empty or plazo_fijo_df.empty:
            raise ValueError("Una o más hojas del Excel están vacías")
        
        # Imprimir información de registros leídos
        print(f"\nRegistros leídos:")
        print(f"- Compra: {len(compra_df)} registros")
        print(f"- Venta: {len(venta_df)} registros")
        print(f"- Canje: {len(canje_df)} registros")
        print(f"- Plazo Fijo: {len(plazo_fijo_df)} registros")
        
        # Obtener información de la compañía
        codigo_compania = config['company']
        
        # Procesar cada tipo de operación
        operaciones = []
        
        # Procesar y verificar cada tipo de operación con los formatos configurados
        compras = process_compra(compra_df, decimal_separator, date_format)
        print(f"\nOperaciones procesadas:")
        print(f"- Compra: {len(compras)} operaciones")
        # Verificar formato de fechas en la primera operación de cada tipo
        if compras:
            fecha = compras[0]['FECHAMOVIMIENTO']
            if not validate_date_format(fecha, date_format):
                raise ValueError(f"Fecha '{fecha}' no está en el formato configurado {date_format}")
            print(f"  Ejemplo fecha: {fecha}")
        operaciones.extend(compras)
        
        ventas = process_venta(venta_df, decimal_separator, date_format)
        print(f"- Venta: {len(ventas)} operaciones")
        if ventas:
            fecha = ventas[0]['FECHAMOVIMIENTO']
            if not validate_date_format(fecha, date_format):
                raise ValueError(f"Fecha '{fecha}' no está en el formato configurado {date_format}")
            print(f"  Ejemplo fecha: {fecha}")
        operaciones.extend(ventas)
        
        canjes = process_canje(canje_df, decimal_separator, date_format)
        print(f"- Canje: {len(canjes)} operaciones")
        if canjes:
            fecha = canjes[0]['FECHAMOVIMIENTO']
            if not validate_date_format(fecha, date_format):
                raise ValueError(f"Fecha '{fecha}' no está en el formato configurado {date_format}")
            print(f"  Ejemplo fecha: {fecha}")
        operaciones.extend(canjes)
        
        plazos_fijos = process_plazo_fijo(plazo_fijo_df, decimal_separator, date_format)
        print(f"- Plazo Fijo: {len(plazos_fijos)} operaciones")
        if plazos_fijos:
            fecha = plazos_fijos[0]['FECHACONSTITUCION']
            if not validate_date_format(fecha, date_format):
                raise ValueError(f"Fecha '{fecha}' no está en el formato configurado {date_format}")
            print(f"  Ejemplo fecha: {fecha}")
        operaciones.extend(plazos_fijos)
        
        print(f"\nTotal de operaciones procesadas: {len(operaciones)}")
        
        # Agrupar operaciones por semana
        operaciones_por_semana = agrupar_por_semana(operaciones)
        
        # Guardar un archivo JSON por cada semana
        archivos_generados = guardar_json_por_semana(codigo_compania, operaciones_por_semana)
        
        # Mostrar resumen de archivos generados
        print("\nArchivos JSON generados:")
        for archivo, total_operaciones in archivos_generados:
            print(f"- {archivo}: {total_operaciones} operaciones")
        
    except ValueError as e:
        print("\nError de formato en el archivo Excel:")
        print(str(e))
        return
    except Exception as e:
        print(f"\nError inesperado al procesar el archivo Excel:")
        print(str(e))
        raise

if __name__ == "__main__":
    main()
