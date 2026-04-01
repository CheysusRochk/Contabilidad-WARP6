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
    "Tiene_Factura (Si/No)",
    "Aplica_Retencion (Si/No)",
    "Proyecto"
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
        
        # Check basic columns existence
        has_proyecto_col = df.shape[1] >= 11 or "Proyecto" in df.columns
        
        if len(df.columns) < 10:
            return None, f"El archivo tiene {len(df.columns)} columnas, se esperaban al menos 10. Por favor descargue la NUEVA plantilla."
            
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
                
                # Robust boolean parsing - Factura
                tf_str = str(row.iloc[8]).strip().lower()
                if any(x in tf_str for x in ['si', 'sí', 'yes', 'true', '1', 'con factura']):
                    tiene_factura = True
                else:
                    tiene_factura = False
                
                # Robust boolean parsing - Retencion
                ar_str = str(row.iloc[9]).strip().lower() if pd.notna(row.iloc[9]) else "no"
                if any(x in ar_str for x in ['si', 'sí', 'yes', 'true', '1']):
                    aplica_retencion = True
                else:
                    aplica_retencion = False
                    
                # Parsing Proyecto
                proyecto = "General"
                if has_proyecto_col and len(row) >= 11 and pd.notna(row.iloc[10]):
                    parsed_proy = str(row.iloc[10]).strip()
                    if parsed_proy:
                        proyecto = parsed_proy
                elif "Proyecto" in df.columns and pd.notna(row["Proyecto"]):
                    parsed_proy = str(row["Proyecto"]).strip()
                    if parsed_proy:
                        proyecto = parsed_proy
                
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
                    'tiene_factura': tiene_factura,
                    'aplica_retencion': aplica_retencion,
                    'proyecto': proyecto
                })
                
            except Exception as e:
                errors.append(f"Fila {index+2}: Error procesando datos ({str(e)})")
        
        if errors:
            return None, errors
            
        return pd.DataFrame(normalized_data), None
        
    except Exception as e:
        return None, f"Error crítico leyendo el archivo: {str(e)}"
