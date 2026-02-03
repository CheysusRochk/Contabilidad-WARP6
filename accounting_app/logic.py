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
        
        # 3. Detectar PAGOS realizados en este mes o que se refieren a este mes
        # Nota: Los impuestos se suelen pagar al mes SIGUIENTE.
        # Buscamos pagos en TODOS los datos cuyo detalle mencione este mes
        pagos_mes = df[df['detalle'].str.contains(month_str, case=False, na=False) | 
                       df['detalle'].str.contains(period.strftime('%B'), case=False, na=False)]
        
        iva_pagado = 0
        it_pagado = 0
        
        for _, row in month_df.iterrows():
            det = str(row['detalle']).lower()
            cat = str(row['categoria']).lower()
            if "pago" in det or "pago" in cat:
                if "iva" in det: iva_pagado += row['monto']
                elif "it" in det: it_pagado += row['monto']
                elif "impuesto" in det:
                    # Si dice "impuestos" sin especificar, asumimos que puede ser el IT del 3% o repartido.
                    # El usuario suele pagar juntos. Si no se puede distinguir, el calendario mostrará diferencia.
                    pass 

        # Si el usuario puso una sola línea de "pago impuestos", intentamos reconciliar por monto
        # pero es mejor informar la diferencia.
        
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
    
    # Gastos: SOLO los que tienen factura (deducibles)
    gastos_facturados = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 1)]
    
    # Capital Social = Aportes en Efectivo + Aportes en Activos
    total_aportes = df[is_aporte]['monto'].sum()
    aportes_efectivo = df[is_aporte_efectivo]['monto'].sum()
    
    # ========== 1. CÁLCULO DE CAJA (Solo transacciones fiscales) ==========
    # Ingresos brutos facturados
    ingresos_brutos = ingresos_facturados['monto'].sum()
    
    # Gastos brutos facturados
    gastos_brutos_fiscales = gastos_facturados['monto'].sum()
    
    # Caja Fiscal = SOLO Aportes en Efectivo + Ingresos - Gastos (solo facturados)
    # Los aportes de activos NO entran a caja
    caja_final = aportes_efectivo + ingresos_brutos - gastos_brutos_fiscales
    
    # ========== 2. ACTIVOS FIJOS ==========
    valor_activos = assets_df['valor_inicial'].sum() if not assets_df.empty else 0
    dep_acumulada = calculate_period_depreciation(assets_df, 12)
    activos_netos = valor_activos - dep_acumulada
    
    # ========== 3. IMPUESTOS (PASIVOS) ==========
    iva_df_total = 0
    iva_cf_total = 0
    it_total = 0
    
    # Calcular IVA e IT sobre transacciones facturadas
    for _, row in ingresos_facturados.iterrows():
        taxes = calculate_taxes(row['monto'], row['tipo'], True, row['categoria'])
        iva_df_total += taxes['iva_df']
        it_total += taxes['it']
    
    for _, row in gastos_facturados.iterrows():
        taxes = calculate_taxes(row['monto'], row['tipo'], True, row['categoria'])
        iva_cf_total += taxes['iva_cf']
    
    # Pasivos Tributarios
    iva_por_pagar = max(0, iva_df_total - iva_cf_total)
    iva_credito_fiscal = max(0, iva_cf_total - iva_df_total)
    it_por_pagar = it_total
    
    # ========== 4. ESTADO DE RESULTADOS FISCAL (Para Patrimonio) ==========
    # Ingresos Netos = Ingresos Brutos - IVA DF
    ingresos_netos_fiscales = ingresos_brutos - iva_df_total
    
    # Gastos Netos = Gastos Facturados * 0.87
    gastos_netos_fiscales = gastos_brutos_fiscales * 0.87
    
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
                'total': iva_por_pagar + it_por_pagar + iue_por_pagar
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
    
    iva_por_pagar = max(0, iva_df_total - iva_cf_total)
    iva_credito_fiscal = max(0, iva_cf_total - iva_df_total)
    it_por_pagar = it_total
    
    # ========== 4. UTILIDAD FISCAL (Para IUE) ==========
    # Calcular igual que balance SIN (solo facturados)
    ingresos_brutos_facturados = ingresos_facturados['monto'].sum()
    gastos_brutos_facturados = gastos_facturados['monto'].sum()
    
    ingresos_netos_fiscales = ingresos_brutos_facturados - iva_df_total
    gastos_netos_fiscales = gastos_brutos_facturados * 0.87
    
    utilidad_antes_it = ingresos_netos_fiscales - gastos_netos_fiscales - dep_acumulada
    utilidad_antes_iue = utilidad_antes_it - it_total
    iue_por_pagar = max(0, utilidad_antes_iue * 0.25)
    utilidad_neta_fiscal = utilidad_antes_iue - iue_por_pagar
    
    # ========== 5. GASTOS NO DEDUCIBLES (Ajuste) ==========
    # Gastos sin factura que reducen la caja pero no la utilidad fiscal
    gastos_sin_factura = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 0)]['monto'].sum()
    
    # ========== 6. ESTRUCTURA DEL BALANCE REAL ==========
    balance = {
        'activos': {
            'corriente': {
                'caja': caja_real,  # Caja REAL
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
                'total': iva_por_pagar + it_por_pagar + iue_por_pagar
            }
        },
        'patrimonio': {
            'capital': total_aportes,
            'utilidad_fiscal': utilidad_neta_fiscal,  # Utilidad LEGAL (para impuestos)
            'gastos_no_deducibles': -gastos_sin_factura,  # Ajuste negativo
            'resultados_acum': utilidad_neta_fiscal - gastos_sin_factura,  # Resultado Real
            'total': total_aportes + utilidad_neta_fiscal - gastos_sin_factura
        },
        'info_adicional': {
            'gastos_sin_factura': gastos_sin_factura,
            'utilidad_fiscal_declarada': utilidad_neta_fiscal
        }
    }
    
    # Validación
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
