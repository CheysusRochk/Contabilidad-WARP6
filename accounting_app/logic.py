from datetime import datetime
import pandas as pd

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

def calculate_balance_sheet(df, assets_df, cutoff_date=None):
    """
    Calcula todos los componentes del Balance General asegurando que cuadre.
    Activo = Pasivo + Patrimonio
    """
    if cutoff_date:
        # Convertir a datetime para filtrar
        if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
             df['fecha_dt'] = pd.to_datetime(df['fecha'])
        else:
             df['fecha_dt'] = df['fecha']
        
        # Filtro hasta la fecha de corte
        df = df[df['fecha_dt'] <= pd.to_datetime(cutoff_date)]
    
    # 1. Calcular Flujos de Efectivo (Caja)
    # Caja = Aportes + Ingresos(Brutos) - Gastos(Brutos)
    
    # Identificar Aportes
    is_aporte = df['categoria'].str.lower().str.contains('aporte', na=False) & \
                df['categoria'].str.lower().str.contains('capital', na=False)
    
    total_aportes = df[is_aporte]['monto'].sum()
    
    # Ingresos Operativos (Entrada de dinero) - Excluye aportes
    ingresos = df[(df['tipo'] == 'Ingreso') & (~is_aporte)]['monto'].sum()
    
    # Gastos Totales (Salida de dinero)
    gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
    
    caja_final = total_aportes + ingresos - gastos
    
    # 2. Activos No Corrientes (Netos)
    valor_activos = assets_df['valor_inicial'].sum() if not assets_df.empty else 0
    dep_acumulada = calculate_period_depreciation(assets_df, 12) # Simplificación Anual
    activos_netos = valor_activos - dep_acumulada
    
    # 3. Impuestos (Pasivos)
    iva_df_total = 0
    iva_cf_total = 0
    it_total = 0
    
    # Iterar para calcular impuestos acumulados
    for _, row in df.iterrows():
        taxes = calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'], row['categoria'])
        if row['tipo'] == 'Ingreso':
             if "aporte" not in row['categoria'].lower():
                iva_df_total += taxes['iva_df']
                it_total += taxes['it']
        elif row['tipo'] == 'Gasto' and row['tiene_factura']:
            iva_cf_total += taxes['iva_cf']

    # Pasivos Tributarios
    iva_por_pagar = max(0, iva_df_total - iva_cf_total)
    iva_credito_fiscal = max(0, iva_cf_total - iva_df_total) # Activo Corriente
    
    it_por_pagar = it_total 
    
    # 4. Estado de Resultados (Para Patrimonio)
    # DEBE COINCIDIR CON EL ESTADO DE RESULTADOS PROVISIONAL
    
    # Ingresos Netos (87% para facturados)
    ingresos_netos = ingresos - iva_df_total
    
    # Gastos Netos (87% para facturados, 100% para no facturados)
    gastos_con_factura_netos = 0
    gastos_sin_factura_total = 0
    
    for _, row in df[df['tipo'] == 'Gasto'].iterrows():
        if row['tiene_factura']:
            gastos_con_factura_netos += row['monto'] * 0.87  # Gasto neto (sin IVA)
        else:
            gastos_sin_factura_total += row['monto']  # Gasto no deducible
    
    # Total de gastos netos para el estado de resultados
    gastos_netos_totales = gastos_con_factura_netos + gastos_sin_factura_total
    
    # Utilidad Operativa (antes de IT e IUE)
    # Formula: Ingresos Netos - Gastos Netos - Depreciación - IT
    utilidad_operativa = ingresos_netos - gastos_netos_totales - dep_acumulada - it_total
    
    # Para IUE, los gastos sin factura NO son deducibles
    # Base Imponible = Ingresos Netos - Gastos Deducibles - Depreciación - IT
    # Gastos Deducibles = solo los que tienen factura
    utilidad_imponible = ingresos_netos - gastos_con_factura_netos - dep_acumulada - it_total
    
    if utilidad_imponible < 0:
        utilidad_imponible = 0
    
    iue_por_pagar = utilidad_imponible * 0.25
    utilidad_neta = utilidad_operativa - iue_por_pagar
    
    # 5. Estructura Final
    balance = {
        'activos': {
            'corriente': {
                'caja': caja_final,
                'iva_credito': iva_credito_fiscal,
                'inventarios': 0, 
                'total': caja_final + iva_credito_fiscal
            },
            'no_corriente': {
                'fijos_bruto': valor_activos,
                'dep_acum': dep_acumulada,
                'fijos_neto': activos_netos,
                'total': activos_netos
            }
        },
        'pasivos': {
            'corriente': {
                'iva_por_pagar': iva_por_pagar,
                'it_por_pagar': it_por_pagar,
                'iue_por_pagar': iue_por_pagar,
                'total': iva_por_pagar + it_por_pagar + iue_por_pagar
            }
        },
        'patrimonio': {
            'capital': total_aportes,
            'resultados_acum': utilidad_neta,
            'total': total_aportes + utilidad_neta
        }
    }
    
    # Ajuste de Cuadratura
    total_activos = balance['activos']['corriente']['total'] + balance['activos']['no_corriente']['total']
    total_pasivos = balance['pasivos']['corriente']['total']
    total_patrimonio = balance['patrimonio']['total']
    
    diferencia = total_activos - (total_pasivos + total_patrimonio)
    balance['validacion'] = {
        'activos': total_activos,
        'pasivo_patrimonio': total_pasivos + total_patrimonio,
        'diferencia': diferencia,
        'cuadra': abs(diferencia) < 1.0
    }
    
    return balance
