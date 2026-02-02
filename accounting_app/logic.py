from datetime import datetime

# Constantes Normativa Boliviana
IVA_RATE = 0.13
IT_RATE = 0.03
IUE_RATE = 0.25 # Anual, referencial para el contexto

def calculate_taxes(monto: float, tipo: str, tiene_factura: bool, categoria: str = ""):
    """
    Calcula desglose tributario según normativa boliviana.
    Retorna un diccionario con los valores calculados.
    """
    # CASOS ESPECIALES QUE NO GENERAN IMPUESTOS
    cat_lower = categoria.lower()
    # Detectar variantes: "aporte capital", "aportes a capital", "aporte de capital", etc.
    if ("aporte" in cat_lower and "capital" in cat_lower):
        return {
            'monto_total': monto,
            'iva_df': 0.0, 'it': 0.0, 'ingreso_neto': monto, # Todo entra a caja
            'iva_cf': 0.0, 'gasto_neto': 0.0
        }
    
    # Detectar variantes: "pago impuestos", "pago de impuestos", etc.
    if ("pago" in cat_lower and "impuesto" in cat_lower):
        return {
            'monto_total': monto,
            'iva_df': 0.0, 'it': 0.0, 'ingreso_neto': 0.0,
            'iva_cf': 0.0, 
            'gasto_neto': 0.0 # NO es gasto deducible en Estado Resultados (es pago de pasivo)
                              # El Gasto IT ya se registró autm. al vender.
        }

    if tipo == 'Ingreso':
        # Venta Facturada:
        # IVA Débito Fiscal (13%)
        # IT (3%)
        # Ingreso Neto (87%)
        iva = monto * IVA_RATE
        it = monto * IT_RATE
        neto = monto - iva
        # Nota: El IT es un gasto, pero aquí calculamos los componentes de la transacción
        return {
            'monto_total': monto,
            'iva_df': iva,
            'it': it,
            'ingreso_neto': neto,
            'iva_cf': 0.0,
            'gasto_neto': 0.0
        }
    
    elif tipo == 'Gasto':
        if tiene_factura:
            # Compra Facturada:
            # IVA Crédito Fiscal (13%) - Activo exigible
            # Gasto Neto (87%)
            iva = monto * IVA_RATE
            neto = monto - iva
            return {
                'monto_total': monto,
                'iva_df': 0.0,
                'it': 0.0,
                'ingreso_neto': 0.0,
                'iva_cf': iva,
                'gasto_neto': neto
            }
        else:
            # Compra sin factura (Asumiendo no retenciones para simplificar, o gasto directo)
            # Todo es gasto (no deducible para IUE usualmente si no hay retención, pero contablemente es gasto)
            return {
                'monto_total': monto,
                'iva_df': 0.0,
                'it': 0.0,
                'ingreso_neto': 0.0,
                'iva_cf': 0.0,
                'gasto_neto': monto
            }
    return {}

def calculate_lost_credit(monto: float):
    """Calcula el crédito fiscal perdido (13%) por no tener factura."""
    return monto * IVA_RATE

def check_bancarization(monto: float):
    """
    Verifica si el monto supera los 50.000 Bs para alerta de bancarización.
    """
    return monto >= 50000

def check_asset_status(fecha_adquisicion_str, vida_util_anios):
    """
    Calcula estado básico de depreciación basado en tiempo.
    """
    try:
        fecha_adq = datetime.strptime(fecha_adquisicion_str, '%Y-%m-%d')
        fecha_actual = datetime.now()
        
        # Diferencia en días
        dias_uso = (fecha_actual - fecha_adq).days
        dias_vida_util = vida_util_anios * 365
        
        porcentaje_depreciado = min(100.0, (dias_uso / dias_vida_util) * 100)
        return dias_uso, porcentaje_depreciado
    except Exception:
        return 0, 0

def classify_account(categoria):
    """
    Clasifica la categoría en grupos financieros para reporte Gerencial.
    """
    cat = categoria.lower()
    
    # Costo de Ventas (Variable / Directo)
    if any(x in cat for x in ['material', 'equipo', 'mercaderia', 'costo', 'compra']):
        return 'Costo de Ventas'
    
    # Gastos Financieros
    if any(x in cat for x in ['interes', 'banco', 'comision', 'financiero']):
        return 'Gastos Financieros'
        
    # Gastos de Personal (Inc. AFPs)
    if any(x in cat for x in ['sueldo', 'salario', 'personal', 'afp', 'patronal', 'planila']):
        return 'Gastos de Personal'

    # Impuestos (Gasto Directo)
    if any(x in cat for x in ['impuesto', 'it', 'tasa', 'patente']):
        return 'Impuestos'
        
    return 'Gastos Operativos Fijos'

def calculate_period_depreciation(assets_df, months=12):
    """Calcula depreciación estimada para un periodo (por defecto anual)."""
    total_dep = 0
    if assets_df.empty:
        return 0.0
        
    for _, row in assets_df.iterrows():
        # Simplificación lineal anual: Valor / Vida Util
        annual_dep = row['valor_inicial'] / row['vida_util_anios']
        total_dep += annual_dep
        
    return total_dep if months == 12 else (total_dep / 12) * months
