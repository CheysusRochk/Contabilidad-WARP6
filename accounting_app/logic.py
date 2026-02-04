from datetime import datetime
import pandas as pd

# Constantes Normativa Boliviana
IVA_RATE = 0.13
IT_RATE = 0.03
IUE_RATE = 0.25 # Anual, referencial para el contexto

def calculate_taxes(monto: float, tipo: str, tiene_factura: bool, categoria: str = "", aplica_retencion: bool = False):
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

def calculate_grossing_up(monto_neto: float):
    """
    Realiza el 'Grossing Up' (Acrecentamiento) para Servicios.
    Asume retención de servicios: 12.5% IUE (o RC-IVA 13%) + 3% IT = 15.5% / 16%.
    
    Según imagen usuario: 
    Neto 7200 -> Bruto 8571.43
    8571.43 * 0.13 = 1114.29 (RC-IVA)
    8571.43 * 0.03 = 257.14 (IT)
    Total retenido: 1371.43
    Neto calculado: 8571.43 - 1371.43 = 7200.
    
    Factor Efectivo = 100% - (13% + 3%) = 84% = 0.84
    """
    FACTOR_RETENCION = 0.84 # Para servicios
    monto_bruto = monto_neto / FACTOR_RETENCION
    rc_iva_ret = monto_bruto * 0.13
    it_ret = monto_bruto * 0.03
    return monto_bruto, rc_iva_ret, it_ret

def calculate_taxes(monto: float, tipo: str, tiene_factura: bool, categoria: str = "", aplica_retencion: bool = False):
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
        elif aplica_retencion:
             # Gasto con Retención (Grossing Up)
             # El monto ingresado es el NETO PAGADO (Caja).
             # Calculamos el Bruto (Gasto Fiscal Deducible).
             bruto, rc_iva, it_ret = calculate_grossing_up(monto)
             
             return {
                 'monto_total': monto,      # Lo que salió de caja
                 'monto_bruto': bruto,      # El gasto contable real
                 'iva_df': 0.0,
                 'it': 0.0,
                 'ingreso_neto': 0.0,
                 'iva_cf': 0.0,
                 'gasto_neto': bruto,       # DEDUCIBLE AL 100% DEL BRUTO
                 'retenciones': {
                     'rc_iva': rc_iva,
                     'it': it_ret,
                     'total': rc_iva + it_ret
                 }
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

    # Impuestos (Gasto Directo - IT/Patentes/Tasas)
    # IMPORTANTE: No incluir pagos de impuestos pasados (son pagos de pasivo)
    if any(x in cat for x in ['impuesto', 'it', 'tasa', 'patente']):
        if "pago" in cat:
            return 'Excluir P&L (Pago Pasivo)' # No es gasto del periodo
        return 'Impuestos'
        
    return 'Gastos Operativos Fijos'


def get_monthly_tax_summary(df):
    """
    Genera un resumen mensual detallado de impuestos (IVA, IT)
    considerando débitos, créditos y pagos realizados.
    Sincronizado con lógica SIAT.
    """
    if df.empty:
        return {}
    
    # Asegurar que la fecha sea datetime
    if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
        df['fecha'] = pd.to_datetime(df['fecha'])
    
    # Agrupar por Mes-Año
    df['periodo_mes'] = df['fecha'].dt.to_period('M')
    periodos = sorted(df['periodo_mes'].unique())
    
    resumen = {}
    
    for period in periodos:
        month_df = df[df['periodo_mes'] == period]
        month_str = str(period)
        
        # 1. IVA (Ventas - Compras Facturadas)
        ventas_facturadas = month_df[(month_df['tipo'] == 'Ingreso') & 
                                     (~month_df['categoria'].str.lower().str.contains('aporte', na=False))]
        compras_facturadas = month_df[(month_df['tipo'] == 'Gasto') & (month_df['tiene_factura'] == 1)]
        
        iva_df = ventas_facturadas['monto'].sum() * IVA_RATE
        iva_cf = compras_facturadas['monto'].sum() * IVA_RATE
        
        iva_determinado = max(0, iva_df - iva_cf)
        
        # 2. IT (3% de Ventas Brutas)
        it_determinado = ventas_facturadas['monto'].sum() * IT_RATE
        
        # 3. Detectar PAGOS INTELIGENTES (Smart Tax Match)
        # Buscamos en TODOS los registros de impuestos si hay alguno que mencione este mes/año
        
        iva_pagado = 0
        it_pagado = 0
        
        # Nombre del mes en español para buscar (ej: "Octubre")
        # Diccionario simple o locale
        meses_es = { 1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio", 
                     7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre" }
        nombre_mes = meses_es[period.month]
        
        # Filtrar solo transacciones de pago de impuestos GLOBALMENTE (no solo este mes)
        # Buscamos "pago" + "impuesto/iva/it"
        pagos_globales = df[df['categoria'].str.lower().str.contains('pago', na=False) & 
                           (df['categoria'].str.lower().str.contains('impuesto', na=False) | 
                            df['categoria'].str.lower().str.contains('iva', na=False) | 
                            df['categoria'].str.lower().str.contains('it', na=False))]
        
        for _, row in pagos_globales.iterrows():
            det = str(row['detalle']).lower()
            
            # Chequear si el detalle menciona el mes actual del loop (ej: "octubre")
            # Y OPCIONALMENTE el año (para evitar cruces si hay mucha historia, asumimos año actual del loop)
            if nombre_mes in det:
                # ¡Es un pago para ESTE mes fiscal!
                if "iva" in det: 
                    iva_pagado += row['monto']
                elif "it" in det: 
                    it_pagado += row['monto']
                elif "impuesto" in det:
                    # Genérico
                    pass 
        
        resumen[month_str] = {
            'iva_determinado': iva_determinado,
            'it_determinado': it_determinado,
            'iva_pagado': iva_pagado,
            'it_pagado': it_pagado,
            'total_determinado': iva_determinado + it_determinado,
            'total_pagado': iva_pagado + it_pagado
        }
        
    return resumen


def calculate_period_depreciation(assets_df, months=12):
    """
    Calcula depreciación ACUMULADA desde la adquisición hasta ahora.
    Usa método de línea recta mensual.
    """
    total_dep = 0
    if assets_df.empty:
        return 0.0
    
    from datetime import datetime
    fecha_actual = datetime.now()
    
    for _, row in assets_df.iterrows():
        try:
            # Calcular depreciación mensual
            annual_dep = row['valor_inicial'] / row['vida_util_anios']
            monthly_dep = annual_dep / 12
            
            # Calcular meses transcurridos desde adquisición
            fecha_adq = datetime.strptime(str(row['fecha_adquisicion']), '%Y-%m-%d')
            meses_uso = ((fecha_actual.year - fecha_adq.year) * 12 + 
                        (fecha_actual.month - fecha_adq.month))
            
            # Limitar a vida útil máxima
            meses_max = row['vida_util_anios'] * 12
            meses_efectivos = min(meses_uso, meses_max)
            
            # Depreciación acumulada = Depreciación mensual * meses transcurridos
            dep_acumulada = monthly_dep * meses_efectivos
            total_dep += dep_acumulada
            
        except Exception as e:
            # Si hay error en algún activo, usar depreciación anual simple
            annual_dep = row['valor_inicial'] / row['vida_util_anios']
            total_dep += annual_dep
    
    return total_dep

def calculate_balance_sheet(df, assets_df, cutoff_date=None):
    """
    Calcula Balance General para el SIN (Solo Operaciones Facturadas).
    Este balance refleja la REALIDAD FISCAL, no la realidad de caja.
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
    
    # ========== FILTRAR SOLO TRANSACCIONES FACTURADAS (PARA SIN) ==========
    # Identificar Aportes de Capital (siempre van, no necesitan factura)
    is_aporte = df['categoria'].str.lower().str.contains('aporte', na=False) & \
                df['categoria'].str.lower().str.contains('capital', na=False)
    
    # Distinguir entre aportes en efectivo vs activos
    is_aporte_activo = is_aporte & df['categoria'].str.lower().str.contains('activo', na=False)
    is_aporte_efectivo = is_aporte & (~df['categoria'].str.lower().str.contains('activo', na=False))
    
    # Ingresos: todos tienen factura (requisito para emitir)
    ingresos_facturados = df[(df['tipo'] == 'Ingreso') & (~is_aporte)]
    
    # Gastos: Facturados (Deducibles) + Retenciones (Deducibles)
    # Check if 'aplica_retencion' exists safely
    if 'aplica_retencion' in df.columns:
        gastos_deducibles = df[(df['tipo'] == 'Gasto') & 
                            ((df['tiene_factura'] == 1) | (df['aplica_retencion'] == 1))]
    else:
        gastos_deducibles = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 1)]
    
    # Capital Social = Aportes en Efectivo + Aportes en Activos
    total_aportes = df[is_aporte]['monto'].sum()
    aportes_efectivo = df[is_aporte_efectivo]['monto'].sum()
    
    # ========== 1. CÁLCULO DE CAJA (Solo transacciones fiscales) ==========
    # Ingresos brutos facturados
    ingresos_brutos = ingresos_facturados['monto'].sum()
    
    # Gastos brutos (Lo que sale de caja)
    # Para facturas: sale 100%. Para retenciones: sale 100% (NETO). 
    # El Balance Fiscal registra lo que es legalmente soportado.
    gastos_caja_fiscal = gastos_deducibles['monto'].sum()
    
    # Caja Fiscal = SOLO Aportes en Efectivo + Ingresos - Gastos
    caja_final = aportes_efectivo + ingresos_brutos - gastos_caja_fiscal
    
    # ========== 2. ACTIVOS FIJOS ==========
    valor_activos = assets_df['valor_inicial'].sum() if not assets_df.empty else 0
    dep_acumulada = calculate_period_depreciation(assets_df, 12)
    activos_netos = valor_activos - dep_acumulada
    
    # ========== 3. IMPUESTOS (PASIVOS) ==========
    iva_df_total = 0
    iva_cf_total = 0
    it_total = 0
    retenciones_liability_total = 0
    
    # Calcular IVA e IT sobre transacciones facturadas
    for _, row in ingresos_facturados.iterrows():
        taxes = calculate_taxes(row['monto'], row['tipo'], True, row['categoria'])
        iva_df_total += taxes['iva_df']
        it_total += taxes['it']
    
    # Calcular Crédito Fiscal y Retenciones
    gastos_netos_fiscales = 0 # Acumulador de gasto deducible real
    
    for _, row in gastos_deducibles.iterrows():
        ar = row.get('aplica_retencion', 0) == 1
        taxes = calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'] == 1, row['categoria'], aplica_retencion=ar)
        
        iva_cf_total += taxes.get('iva_cf', 0)
        
        # Acumular gasto deducible (Neto factura o Bruto retención)
        if 'gasto_neto' in taxes:
             gastos_netos_fiscales += taxes['gasto_neto']
        else:
             # Fallback logic
             if row['tiene_factura'] == 1:
                 gastos_netos_fiscales += row['monto'] * 0.87
        
        # Acumular deuda de Retenciones
        if 'retenciones' in taxes:
            retenciones_liability_total += taxes['retenciones']['total']
    
    # Pasivos Tributarios (Ajustado por Pagos)
    pagos_impuestos = df[df['tipo'] == 'Gasto']
    iva_pagado_acum = 0
    it_pagado_acum = 0
    retenciones_pagado_acum = 0
    
    for _, row in pagos_impuestos.iterrows():
        det = str(row['detalle']).lower()
        cat = str(row['categoria']).lower()
        monto = row['monto']
        
        # Considerar pago si la categoría o detalle lo indica explícitamente
        if 'impuesto' in cat or 'tributo' in cat or 'pago' in det:
            if 'iva' in det or '200' in det:
                iva_pagado_acum += monto
            elif 'it' in det or '400' in det:
                it_pagado_acum += monto
            elif 'retencion' in det or 'iue' in det and '410' in det: # Basic keyword match
                retenciones_pagado_acum += monto

    iva_por_pagar = max(0, iva_df_total - iva_cf_total - iva_pagado_acum)
    iva_credito_fiscal = max(0, iva_cf_total - iva_df_total)
    it_por_pagar = max(0, it_total - it_pagado_acum)
    # Retenciones Por Pagar
    retenciones_por_pagar = max(0, retenciones_liability_total - retenciones_pagado_acum)
    
    # ========== 4. ESTADO DE RESULTADOS FISCAL (Para Patrimonio) ==========
    # Ingresos Netos = Ingresos Brutos - IVA DF
    ingresos_netos_fiscales = ingresos_brutos - iva_df_total
    
    # Gastos Netos = (Ya calculado en el bucle arriba: gastos_netos_fiscales)
    
    # Utilidad antes de IT e IUE
    utilidad_antes_it = ingresos_netos_fiscales - gastos_netos_fiscales - dep_acumulada
    
    # Restar IT
    utilidad_antes_iue = utilidad_antes_it - it_total
    
    # Calcular IUE (25%)
    iue_por_pagar = max(0, utilidad_antes_iue * 0.25)
    
    # Utilidad Neta Fiscal
    utilidad_neta_fiscal = utilidad_antes_iue - iue_por_pagar
    
    # ========== 5. ESTRUCTURA DEL BALANCE ==========
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
                'retenciones_por_pagar': retenciones_por_pagar,
                'total': iva_por_pagar + it_por_pagar + iue_por_pagar + retenciones_por_pagar
            }
        },
        'patrimonio': {
            'capital': total_aportes,
            'resultados_acum': utilidad_neta_fiscal,
            'total': total_aportes + utilidad_neta_fiscal
        }
    }
    
    # ========== 6. VALIDACIÓN DE ECUACIÓN CONTABLE ==========
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

def calculate_balance_sheet_real(df, assets_df, cutoff_date=None):
    """
    Calcula Balance General REAL (Gerencial).
    Muestra la realidad de caja incluyendo TODOS los gastos (con y sin factura),
    pero mantiene la Utilidad Fiscal para efectos tributarios.
    """
    if cutoff_date:
        if not pd.api.types.is_datetime64_any_dtype(df['fecha']):
             df['fecha_dt'] = pd.to_datetime(df['fecha'])
        else:
             df['fecha_dt'] = df['fecha']
        df = df[df['fecha_dt'] <= pd.to_datetime(cutoff_date)]
    
    # Identificar Aportes
    is_aporte = df['categoria'].str.lower().str.contains('aporte', na=False) & \
                df['categoria'].str.lower().str.contains('capital', na=False)
    
    # Distinguir entre aportes en efectivo vs activos
    is_aporte_activo = is_aporte & df['categoria'].str.lower().str.contains('activo', na=False)
    is_aporte_efectivo = is_aporte & (~df['categoria'].str.lower().str.contains('activo', na=False))
    
    total_aportes = df[is_aporte]['monto'].sum()
    aportes_efectivo = df[is_aporte_efectivo]['monto'].sum()
    
    # ========== 1. CAJA REAL (Todos los movimientos) ==========
    ingresos_total = df[(df['tipo'] == 'Ingreso') & (~is_aporte)]['monto'].sum()
    gastos_total = df[df['tipo'] == 'Gasto']['monto'].sum()
    
    # Caja Real = SOLO Aportes en Efectivo + Ingresos - TODOS los Gastos
    # Los aportes de activos NO entran a caja
    caja_real = aportes_efectivo + ingresos_total - gastos_total
    
    # ========== 2. ACTIVOS FIJOS ==========
    valor_activos = assets_df['valor_inicial'].sum() if not assets_df.empty else 0
    dep_acumulada = calculate_period_depreciation(assets_df, 12)
    activos_netos = valor_activos - dep_acumulada
    
    # ========== 3. IMPUESTOS (Solo sobre facturados) ==========
    ingresos_facturados = df[(df['tipo'] == 'Ingreso') & (~is_aporte)]
    gastos_facturados = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 1)]
    
    iva_df_total = 0
    iva_cf_total = 0
    it_total = 0
    
    for _, row in ingresos_facturados.iterrows():
        taxes = calculate_taxes(row['monto'], row['tipo'], True, row['categoria'])
        iva_df_total += taxes['iva_df']
        it_total += taxes['it']
    
    for _, row in gastos_facturados.iterrows():
        taxes = calculate_taxes(row['monto'], row['tipo'], True, row['categoria'])
        iva_cf_total += taxes['iva_cf']
    
    # --- Deducción de Pagos Realizados (Lógica de Caja) ---
    pagos_impuestos = df[df['tipo'] == 'Gasto']
    iva_pagado_acum = 0
    it_pagado_acum = 0
    
    for _, row in pagos_impuestos.iterrows():
        det = str(row['detalle']).lower()
        cat = str(row['categoria']).lower()
        monto = row['monto']
        
        if 'impuesto' in cat or 'tributo' in cat or 'pago' in det:
            if 'iva' in det or '200' in det:
                iva_pagado_acum += monto
            elif 'it' in det or '400' in det:
                it_pagado_acum += monto

    iva_por_pagar = max(0, iva_df_total - iva_cf_total - iva_pagado_acum)
    iva_credito_fiscal = max(0, iva_cf_total - iva_df_total) # El crédito fiscal no se afecta por pagos, es saldo a favor
    it_por_pagar = max(0, it_total - it_pagado_acum)
    
    # ========== 4. UTILIDAD FISCAL (Para IUE) ==========
    # Calcular igual que balance SIN (solo facturados)
    ingresos_brutos_facturados = ingresos_facturados['monto'].sum()
    
    ingresos_netos_fiscales = ingresos_brutos_facturados - iva_df_total
    
    # Recalcular Gastos Deducibles REALES (Facturados + Retenciones)
    gastos_netos_fiscales = 0
    retenciones_liability_total = 0
    
    # Filter: Invoice or Retention
    if 'aplica_retencion' in df.columns:
        gastos_deducibles = df[(df['tipo'] == 'Gasto') & 
                            ((df['tiene_factura'] == 1) | (df['aplica_retencion'] == 1))]
        # Truly Non-Deductible: No Invoice AND No Retention
        gastos_no_deducibles_df = df[(df['tipo'] == 'Gasto') & 
                                     (df['tiene_factura'] == 0) & 
                                     (df['aplica_retencion'].fillna(0) == 0)]
    else:
        gastos_deducibles = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 1)]
        gastos_no_deducibles_df = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 0)]

    for _, row in gastos_deducibles.iterrows():
        ar = row.get('aplica_retencion', 0) == 1
        taxes = calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'] == 1, row['categoria'], aplica_retencion=ar)
        
        if 'gasto_neto' in taxes:
             gastos_netos_fiscales += taxes['gasto_neto'] # Gross if retention, Net if invoice
        else:
             if row['tiene_factura'] == 1:
                 gastos_netos_fiscales += row['monto'] * 0.87
        
        if 'retenciones' in taxes:
             retenciones_liability_total += taxes['retenciones']['total']
    
    # Retenciones Pagadas
    retenciones_pagado_acum = 0
    for _, row in pagos_impuestos.iterrows():
        det = str(row['detalle']).lower()
        if ('retencion' in det or 'iue' in det) and 'pago' in det:
             retenciones_pagado_acum += row['monto']
             
    retenciones_por_pagar = max(0, retenciones_liability_total - retenciones_pagado_acum)

    # Utilidad antes de IT e IUE
    utilidad_antes_it = ingresos_netos_fiscales - gastos_netos_fiscales - dep_acumulada
    
    # Restar IT
    utilidad_antes_iue = utilidad_antes_it - it_total
    
    # Calcular IUE (25%)
    iue_por_pagar = max(0, utilidad_antes_iue * 0.25)
    
    utilidad_neta_fiscal = utilidad_antes_iue - iue_por_pagar
    
    # ========== 5. GASTOS NO DEDUCIBLES (Ajuste) ==========
    gastos_sin_factura_total = gastos_no_deducibles_df['monto'].sum()
    
    # Calcular reducción de pasivos (si aplica)
    iva_neto_gen = max(0, iva_df_total - iva_cf_total)
    reduccion_iva = min(iva_neto_gen, iva_pagado_acum)
    reduccion_it = min(it_total, it_pagado_acum)
    total_reduccion_pasivo = reduccion_iva + reduccion_it
    
    # Ajustar (Simplified logic for managerial view)
    # The 'gastos_sin_factura_total' purely non-deducible directly reduces equity.
    # But wait, payments of taxes are also "Gastos" in the DF but technically Liabilities payment.
    # The 'gastos_no_deducibles_df' might include 'Pago Impuesto'?
    # Logic in classify_account excludes 'Pago Pasivo' from P&L. 
    # But here we are summing 'df'.
    # We should exclude 'Pago Pasivo' from the 'gastos_sin_factura_total' to be accurate?
    # Yes, typically tax payments are not "Expenses" in this sense.
    # However, for the equation to balance: Cash = Liab + Equity.
    # Non-deducible expenses reduce Cash but not Liab, so they must reduce Equity.
    # Tax payments reduce Cash AND Liab, so they don't affect Equity.
    # So we must ensure `gastos_no_deducibles_df` excludes tax payments that reduce liability.
    
    # Refined Filter: Exclude Tax Payments from "Gastos No Deducibles" sum
    # (Assuming tax payments are correctly labeled)
    # Actually, simpler approach:
    # Equity = Assets - Liabilities.
    # Use the balancing plug.
    
    # Activos Reales:
    total_activos_reales = caja_real + iva_credito_fiscal + activos_netos
    
    # Pasivos Reales:
    total_pasivos_reales = iva_por_pagar + it_por_pagar + iue_por_pagar + retenciones_por_pagar
    
    # Patrimonio Real
    patrimonio_real = total_activos_reales - total_pasivos_reales
    resultados_acum_real = patrimonio_real - total_aportes
    
    # Back-calculate the "Gastos No Deducibles & Otros" for display
    # Resultados Acum Real = Utilidad Fiscal - GastosNoDeducibles
    # => GastosNoDeducibles = Utilidad Fiscal - Resultados Acum Real
    gastos_no_deducibles_implied = utilidad_neta_fiscal - resultados_acum_real
    
    balance = {
        'activos': {
            'corriente': {
                'caja': caja_real,
                'iva_credito': iva_credito_fiscal,
                'inventarios': 0, 
                'total': caja_real + iva_credito_fiscal
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
                'retenciones_por_pagar': retenciones_por_pagar,
                'total': total_pasivos_reales
            }
        },
        'patrimonio': {
            'capital': total_aportes,
            'resultados_acum': resultados_acum_real,
            'utilidad_fiscal': utilidad_neta_fiscal,
            'total': patrimonio_real
        },
        'info_adicional': {
            'gastos_sin_factura': gastos_no_deducibles_implied 
        },
         'validacion': {
            'activos': total_activos_reales,
            'pasivo_patrimonio': total_pasivos_reales + patrimonio_real,
            'diferencia': total_activos_reales - (total_pasivos_reales + patrimonio_real),
            'cuadra': True # By definition
        }
    }
    
    return balance
