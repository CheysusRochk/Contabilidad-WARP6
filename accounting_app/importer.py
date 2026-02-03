import pandas as pd
import io

TEMPLATE_COLUMNS = [
    "Fecha (DD/MM/AAAA)",
    "Tipo (Ingreso/Gasto)",
    "Categoria",
    "Detalle",
    "N_Factura",
    "NIT",
    "Monto",
    "Metodo_Pago",
    "Tiene_Factura (Si/No)"
]

def generate_template():
    """Generates an empty Excel template for the user."""
    df = pd.DataFrame(columns=TEMPLATE_COLUMNS)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Plantilla_Importacion')
    return output.getvalue()

def process_import_file(uploaded_file):
    """
    Reads the uploaded Excel file, validates structure, and returns a normalized DataFrame.
    """
    try:
        df = pd.read_excel(uploaded_file)
        
        # Check basic columns existence (allowing flexibility in naming if possible, but strict for now)
        # To make it user friendly, we could normalize headers, but let's assume they use the template.
        # We will map "Template Columns" to "DB Columns"
        
        if len(df.columns) != len(TEMPLATE_COLUMNS):
            return None, f"El archivo tiene {len(df.columns)} columnas, se esperaban {len(TEMPLATE_COLUMNS)}. Por favor use la plantilla."
            
        normalized_data = []
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Basic parsing
                fecha = pd.to_datetime(row.iloc[0], dayfirst=True).date()
                tipo = str(row.iloc[1]).strip().capitalize() # Ingreso / Gasto
                categoria = str(row.iloc[2]).strip()
                detalle = str(row.iloc[3]).strip()
                n_factura = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ""
                nit = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else ""
                monto = float(row.iloc[6])
                metodo_pago = str(row.iloc[7]).strip()
                tiene_factura_raw = str(row.iloc[8]).strip().lower()
                
                # Robust boolean parsing
                tf_str = str(row.iloc[8]).strip().lower()
                if any(x in tf_str for x in ['si', 'sí', 'yes', 'true', '1', 'con factura']):
                    tiene_factura = True
                else:
                    tiene_factura = False
                
                if tipo not in ['Ingreso', 'Gasto']:
                    errors.append(f"Fila {index+2}: Tipo '{tipo}' inválido. Use 'Ingreso' o 'Gasto'.")
                    continue
                
                normalized_data.append({
                    'fecha': fecha,
                    'tipo': tipo,
                    'categoria': categoria,
                    'detalle': detalle,
                    'n_factura': n_factura,
                    'nit': nit,
                    'monto': monto,
                    'metodo_pago': metodo_pago,
                    'tiene_factura': tiene_factura
                })
                
            except Exception as e:
                errors.append(f"Fila {index+2}: Error procesando datos ({str(e)})")
        
        if errors:
            return None, errors
            
        return pd.DataFrame(normalized_data), None
        
    except Exception as e:
        return None, f"Error crítico leyendo el archivo: {str(e)}"
