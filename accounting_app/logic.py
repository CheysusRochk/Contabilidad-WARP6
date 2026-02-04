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
    if ("pago" in cat_lower and ("impuesto" in cat_lower or "tributo" in cat_lower or "iva" in cat_lower or "it" in cat_lower)):
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
    
    # ========== 1. CÁLCULO DE PAGOS DE IMPUESTOS (Para ajustar Caja y Pasivos) ==========
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
            elif 'retencion' in det or 'iue' in det and '410' in det: 
                retenciones_pagado_acum += monto

    # ========== 2. CÁLCULO DE CAJA FISCAL ==========
    # Ingresos brutos facturados
    ingresos_brutos = ingresos_facturados['monto'].sum()
    
    # Gastos brutos (Lo que sale de caja con factura/retención)
    gastos_caja_fiscal = gastos_deducibles['monto'].sum()
    
    # Caja Fiscal = Aportes Efectivo + Ingresos - Gastos Operativos - PAGOS IMPUESTOS
    total_pagos_impuestos = iva_pagado_acum + it_pagado_acum + retenciones_pagado_acum
    caja_final = aportes_efectivo + ingresos_brutos - gastos_caja_fiscal - total_pagos_impuestos
    
    # ========== 3. ACTIVOS FIJOS ==========
    valor_activos = assets_df['valor_inicial'].sum() if not assets_df.empty else 0
    dep_acumulada = calculate_period_depreciation(assets_df, 12)
    activos_netos = valor_activos - dep_acumulada
    
    # ========== 4. IMPUESTOS (PASIVOS) ==========
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
    
    # Pasivos Tributarios (Ajustado por Pagos ya calculados arriba)
    # Pasivos Tributarios (Ajustado por Pagos ya calculados arriba)
    # IVA
    # 1. Determinar deuda neta antes de pagos
    deuda_iva_teorica = iva_df_total - iva_cf_total 
    
    if deuda_iva_teorica > 0:
        # Toca pagar. Vemos si pagamos suficiente.
        saldo_iva = deuda_iva_teorica - iva_pagado_acum
        if saldo_iva > 0:
            iva_por_pagar = saldo_iva
            iva_saldo_favor = 0
            iva_credito_fiscal_real = 0 # No hay CF, se consumió todo
        else:
            iva_por_pagar = 0
            iva_saldo_favor = abs(saldo_iva) # Pagamos de más
            iva_credito_fiscal_real = 0
    else:
        # Tenemos crédito fiscal (CF > DF)
        iva_por_pagar = 0
        iva_credito_fiscal_real = abs(deuda_iva_teorica)
        iva_saldo_favor = iva_pagado_acum # Todo lo pagado es saldo a favor porque no debíamos nada
        
    # TOTAL ACTIVO IVA (CF + Pagos en Exceso)
    activos_impuestos_iva = iva_credito_fiscal_real + iva_saldo_favor

    # IT
    saldo_it = it_total - it_pagado_acum
    if saldo_it > 0:
        it_por_pagar = saldo_it
        it_saldo_favor = 0
    else:
        it_por_pagar = 0
        it_saldo_favor = abs(saldo_it)
        
    # Retenciones
    saldo_ret = retenciones_liability_total - retenciones_pagado_acum
    if saldo_ret > 0:
        retenciones_por_pagar = saldo_ret
        ret_saldo_favor = 0
    else:
        retenciones_por_pagar = 0
        ret_saldo_favor = abs(saldo_ret)

    # Activos por Impuestos Totales
    total_activos_impuestos = activos_impuestos_iva + it_saldo_favor + ret_saldo_favor

    # Utilidad Neta Fiscal (Se mantiene igual, no depende de pagos)
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
                'iva_credito': total_activos_impuestos, # Incluye CF y Anticipos
                'inventarios': 0, 
                'total': caja_final + total_activos_impuestos
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
    
    # Filter CAPEX 
    capex_categories = ['equipos de computación', 'muebles y enseres', 'maquinaria y equipo', 'vehículos', 'terrenos', 'edificios']
    is_capex_mask = df['categoria'].astype(str).str.lower().isin(capex_categories)

    # 1. Taxes (IVA/IT): Calculate on ALL invoiced expenses to get IVA Credit
    gastos_facturados_all = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 1)]
    
    iva_df_total = 0
    iva_cf_total = 0
    it_total = 0
    
    for _, row in ingresos_facturados.iterrows():
        taxes = calculate_taxes(row['monto'], row['tipo'], True, row['categoria'])
        iva_df_total += taxes['iva_df']
        it_total += taxes['it']
    
    for _, row in gastos_facturados_all.iterrows():
        taxes = calculate_taxes(row['monto'], row['tipo'], True, row['categoria'])
        iva_cf_total += taxes['iva_cf']
    
    # ... (Payment deduction logic remains same) ...

    # ========== 4. UTILIDAD FISCAL (Para IUE) ==========
    # Income
    ingresos_brutos_facturados = ingresos_facturados['monto'].sum()
    ingresos_netos_fiscales = ingresos_brutos_facturados - iva_df_total

    # Expenses: Exclude CAPEX from Deductible EXPENSES (Depreciation handles it)
    gastos_facturados_no_capex = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 1) & (~is_capex_mask)]
    gastos_brutos_facturados = gastos_facturados_no_capex['monto'].sum()
    
    gastos_netos_fiscales = gastos_brutos_facturados * 0.87
    
    # Retenciones are handled in Real Balance or not at all here?
    # Logic.py usually calculates SIN balance purely on invoices.
    # But wait, Retentions ARE deductible for SIN too.
    # The original code here only looked at `gastos_facturados`.
    # To be consistent with Real Balance, we should probably include Retentions here too?
    # The previous code for SIN balance:
    # gastos_facturados = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 1)]
    # ...
    # gastos_netos_fiscales = gastos_brutos_facturados * 0.87
    # It ignored retentions.
    # If the user wants Retentions to be liable, they should probably be here too.
    # But let's stick to the current task: Fix CAPEX.
    # If I change retentions here, I change scope.
    # I will stick to fixing CAPEX for now.
    
    # Correct.

    utilidad_antes_it = ingresos_netos_fiscales - gastos_netos_fiscales - dep_acumulada
    
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
    # Filter: Invoice or Retention
    capex_categories = ['equipos de computación', 'muebles y enseres', 'maquinaria y equipo', 'vehículos', 'terrenos', 'edificios']
    
    # Helper to check if row is CAPEX
    def is_capex(row):
        return str(row['categoria']).lower() in capex_categories

    is_capex_mask = df['categoria'].astype(str).str.lower().isin(capex_categories)
    
    # 1. For Taxes (IVA Credit): Include ALL expenses (CAPEX included)
    expenses_df_all = df[df['tipo'] == 'Gasto']
    
    # 2. For P&L (Deductible Expenses): Exclude CAPEX (Depreciation is handled separately)
    expenses_df_no_capex = df[(df['tipo'] == 'Gasto') & (~is_capex_mask)]

    # Calculate Tax Liabilities and Credits using ALL expenses
    # But for accumulated DEDUCTIBLE AMOUNT, strictly filter
    
    # We iterate over ALL potential tax generating expenses
    if 'aplica_retencion' in df.columns:
        # Candidates for taxes: Invoice OR Retention
        tax_candidates = expenses_df_all[((expenses_df_all['tiene_factura'] == 1) | (expenses_df_all['aplica_retencion'] == 1))]
    else:
        tax_candidates = expenses_df_all[expenses_df_all['tiene_factura'] == 1]

    for _, row in tax_candidates.iterrows():
        ar = row.get('aplica_retencion', 0) == 1
        taxes = calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'] == 1, row['categoria'], aplica_retencion=ar)
        
        # Determine if this row is CAPEX
        row_is_capex = is_capex(row)
        
        # Accumulate Net Expense ONLY if NOT CAPEX
        if not row_is_capex:
            if 'gasto_neto' in taxes:
                 gastos_netos_fiscales += taxes['gasto_neto'] # Gross if retention, Net if invoice
            else:
                 if row['tiene_factura'] == 1:
                     gastos_netos_fiscales += row['monto'] * 0.87
        
        # Accumulate Retention Liability (Always, even if CAPEX - though usually Services)
        if 'retenciones' in taxes:
             retenciones_liability_total += taxes['retenciones']['total']
             
    # Recalculate Non-Deductible for equation: Expenses that are NOT CAPEX and have NO Invoice/Retention
    # (CAPEX without invoice is just Asset without credit, still not P&L expense)
    if 'aplica_retencion' in df.columns:
         gastos_no_deducibles_df = expenses_df_no_capex[
                                     (expenses_df_no_capex['tiene_factura'] == 0) & 
                                     (expenses_df_no_capex['aplica_retencion'].fillna(0) == 0)]
    else:
         gastos_no_deducibles_df = expenses_df_no_capex[expenses_df_no_capex['tiene_factura'] == 0]
    
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
    
    # ========== 6. PATRIMONIO REAL (Bottom-Up Calculation) ==========
    # Start with Fiscal Utility, then subtract non-deductible expenses
    # Non-deductible = Gastos without Invoice AND without Retention
    gastos_sin_factura_total = gastos_no_deducibles_df['monto'].sum()
    
    # Calculate net non-deductible after accounting for tax payments  
    # (Tax payments reduce liabilities, not equity)
    iva_neto_gen = max(0, iva_df_total - iva_cf_total)
    reduccion_iva = min(iva_neto_gen, iva_pagado_acum)
    reduccion_it = min(it_total, it_pagado_acum)
    total_reduccion_pasivo = reduccion_iva + reduccion_it
    
    # Adjust: Subtract tax payments from non-deductibles 
    # (because they reduce liability, not equity)
    gastos_sin_factura_ajustado = max(0, gastos_sin_factura_total - total_reduccion_pasivo)
    
    # Real Results = Fiscal Utility - Non-Deductible Expenses
    resultados_acum_real = utilidad_neta_fiscal - gastos_sin_factura_ajustado
    
    # Real Patrimonio = Capital + Real Results
    patrimonio_real = total_aportes + resultados_acum_real
    
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
            'gastos_sin_factura': gastos_sin_factura_ajustado
        }
    }
    
    # ========== 7. VALIDACIÓN DE ECUACIÓN CONTABLE ==========
    diferencia = total_activos_reales - (total_pasivos_reales + patrimonio_real)
    balance['validacion'] = {
        'activos': total_activos_reales,
        'pasivo_patrimonio': total_pasivos_reales + patrimonio_real,
        'diferencia': diferencia,
        'cuadra': abs(diferencia) < 1.0
    }
    
    return balance
