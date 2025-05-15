import pandas as pd
import json
from datetime import datetime
import os

def load_config():
    config_path = os.path.join('extract', 'config_xls.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def format_number(number):
    if pd.isna(number):
        return 0.0
    if isinstance(number, str):
        # Reemplazar coma por punto en números decimales
        return float(number.replace(',', '.'))
    return float(number)

def format_date(date):
    if pd.isna(date):
        return ""
    # Si la fecha es un entero, convertirlo a string
    if isinstance(date, (int, float)):
        date_str = str(int(date))
        if len(date_str) == 8:  # Si ya está en formato DDMMYYYY
            return date_str
        # Si es una fecha en formato numérico de Excel, convertirla
        date = pd.Timestamp.fromordinal(datetime(1900, 1, 1).toordinal() + int(date) - 2)
    # Convertir fecha a string en formato DDMMYYYY
    return date.strftime('%d%m%Y')

def process_compra(df):
    records = []
    for _, row in df.iterrows():
        record = {
            "TIPOOPERACION": "C",
            "TIPOESPECIE": str(row['TIPOESPECIE']),
            "CODIGOESPECIE": str(row['CODIGOESPECIE']),
            "CANTESPECIES": format_number(row['CANTESPECIES']),
            "CODIGOAFECTACION": str(row['CODIGOAFECTACION']),
            "TIPOVALUACION": str(row['TIPOVALUACION']),
            "FECHAMOVIMIENTO": format_date(row['FECHAMOVIMIENTO']),
            "PRECIOCOMPRA": format_number(row['PRECIOCOMPRA']),
            "FECHALIQUIDACION": format_date(row['FECHALIQUIDACION'])
        }
        records.append(record)
    return records

def process_venta(df):
    records = []
    for _, row in df.iterrows():
        record = {
            "TIPOOPERACION": "V",
            "TIPOESPECIE": str(row['TIPOESPECIE']),
            "CODIGOESPECIE": str(row['CODIGOESPECIE']),
            "CANTESPECIES": format_number(row['CANTESPECIES']),
            "CODIGOAFECTACION": str(row['CODIGOAFECTACION']),
            "TIPOVALUACION": str(row['TIPOVALUACION']),
            "FECHAMOVIMIENTO": format_date(row['FECHAMOVIMIENTO']),
            "FECHAPASEVT": format_date(row['FECHAPASEVT']) if 'FECHAPASEVT' in row else "",
            "PRECIOPASEVT": str(row['PRECIOPASEVT']) if 'PRECIOPASEVT' in row else "",
            "FECHALIQUIDACION": format_date(row['FECHALIQUIDACION']),
            "PRECIOVENTA": format_number(row['PRECIOVENTA'])
        }
        records.append(record)
    return records

def process_canje(df):
    records = []
    for _, row in df.iterrows():
        record = {
            "TIPOOPERACION": "J",
            "TIPOESPECIEA": str(row['TIPOESPECIEA']),
            "CODIGOESPECIEA": str(row['CODIGOESPECIEA']),
            "CANTESPECIESA": format_number(row['CANTESPECIESA']),
            "CODIGOAFECTACIONA": str(row['CODIGOAFECTACIONA']),
            "TIPOVALUACIONA": str(row['TIPOVALUACIONA']),
            "FECHAPASEVTA": format_date(row['FECHAPASEVTA']) if 'FECHAPASEVTA' in row else "",
            "PRECIOPASEVTA": str(row['PRECIOPASEVTA']) if 'PRECIOPASEVTA' in row else "",
            "TIPOESPECIEB": str(row['TIPOESPECIEB']),
            "CODIGOESPECIEB": str(row['CODIGOESPECIEB']),
            "CANTESPECIESB": format_number(row['CANTESPECIESB']),
            "CODIGOAFECTACIONB": str(row['CODIGOAFECTACIONB']),
            "TIPOVALUACIONB": str(row['TIPOVALUACIONB']),
            "FECHAPASEVTB": format_date(row['FECHAPASEVTB']) if 'FECHAPASEVTB' in row else "",
            "PRECIOPASEVTB": str(row['PRECIOPASEVTB']) if 'PRECIOPASEVTB' in row else "",
            "FECHAMOVIMIENTO": format_date(row['FECHAMOVIMIENTO']),
            "FECHALIQUIDACION": format_date(row['FECHALIQUIDACION'])
        }
        records.append(record)
    return records

def process_plazo_fijo(df):
    records = []
    for _, row in df.iterrows():
        record = {
            "TIPOOPERACION": "P",
            "TIPOPF": str(row['TIPOPF']),
            "BIC": str(row['BIC']),
            "CDF": str(row['CDF']),
            "FECHACONSTITUCION": format_date(row['FECHACONSTITUCION']),
            "FECHAVENCIMIENTO": format_date(row['FECHAVENCIMIENTO']),
            "MONEDA": str(row['MONEDA']),
            "VALORNOMINALORIGEN": format_number(row['VALORNOMINALORIGEN']),
            "VALORNOMINALNACIONAL": format_number(row['VALORNOMINALNACIONAL']),
            "CODIGOAFECTACION": str(row['CODIGOAFECTACION']),
            "TIPOTASA": str(row['TIPOTASA']),
            "TASA": format_number(row['TASA']),
            "TITULODEUDA": int(row['TITULODEUDA']),
            "CODIGOTITULO": str(row['CODIGOTITULO'] if not pd.isna(row['CODIGOTITULO']) else "")
        }
        records.append(record)
    return records

def main():    # Cargar configuración
    config = load_config()
    print(f"\nConfiguración cargada del archivo config_xls.json:")
    print(f"- Código de compañía: {config['company']}")
    
    # Leer el archivo Excel
    excel_path = os.path.join('data', 'datos_semanales.xlsx')
    
    try:
        print("Leyendo archivo Excel:", excel_path)
        # Leer cada hoja del Excel sin convertir fechas y sin omitir filas
        compra_df = pd.read_excel(excel_path, sheet_name='Compra', parse_dates=False, skiprows=None)
        venta_df = pd.read_excel(excel_path, sheet_name='Venta', parse_dates=False, skiprows=None)
        canje_df = pd.read_excel(excel_path, sheet_name='Canje', parse_dates=False, skiprows=None)
        plazo_fijo_df = pd.read_excel(excel_path, sheet_name='Plazo-Fijo', parse_dates=False, skiprows=None)
        
        # Imprimir información detallada de cada DataFrame
        print("\n=== Detalles de registros leídos ===")
        for name, df in [("Compra", compra_df), ("Venta", venta_df), ("Canje", canje_df), ("Plazo Fijo", plazo_fijo_df)]:
            print(f"\n{name}:")
            print(f"- Número de filas: {len(df)}")
            print(f"- Columnas: {', '.join(df.columns)}")
            print("- Primeros registros:")
            print(df.head())
            print("-" * 80)
        
        # Verificar que los DataFrames no estén vacíos
        if compra_df.empty or venta_df.empty or canje_df.empty or plazo_fijo_df.empty:
            raise ValueError("Una o más hojas del Excel están vacías")
        
        # Obtener información de la cabecera
        codigo_compania = config['company']
        cronograma = str(compra_df['CRONOGRAMA'].iloc[0])
        
        # Procesar cada tipo de operación
        operaciones = []
        
        # Procesar y verificar cada tipo de operación
        compras = process_compra(compra_df)
        print(f"\nOperaciones de compra procesadas: {len(compras)}")
        operaciones.extend(compras)
        
        ventas = process_venta(venta_df)
        print(f"Operaciones de venta procesadas: {len(ventas)}")
        operaciones.extend(ventas)
        
        canjes = process_canje(canje_df)
        print(f"Operaciones de canje procesadas: {len(canjes)}")
        operaciones.extend(canjes)
        
        plazos_fijos = process_plazo_fijo(plazo_fijo_df)
        print(f"Operaciones de plazo fijo procesadas: {len(plazos_fijos)}")
        operaciones.extend(plazos_fijos)
        
        print(f"\nTotal de operaciones a escribir en JSON: {len(operaciones)}")
        
        # Crear el JSON final
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
        
        print(f"\nArchivo JSON generado exitosamente: {output_path}")
        
    except Exception as e:
        print(f"Error al procesar el archivo Excel: {str(e)}")
        raise

if __name__ == "__main__":
    main()
