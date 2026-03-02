import streamlit as st
import pandas as pd
from datetime import date
import database as db
import logic
import reports
import importer

# Configuración de página
st.set_page_config(
    page_title="WARP6 Accounting",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Personalizados
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #0d6efd;
        color: white;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Inicializar Base de Datos
db.init_db()

def main():
    st.sidebar.title("WARP6 Solutions S.R.L.")
    st.sidebar.markdown("---")
    menu = st.sidebar.radio("Navegación", ["Dashboard", "Registro", "Reportes", "Activos Fijos", "Importar Data"])
    
    # sidebar info
    st.sidebar.markdown("---")
    st.sidebar.info("Sistema Contable v1.2\nNormativa: Ley 843 y DS 24051")

    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Registro":
        show_registro()
    elif menu == "Reportes":
        show_reportes()
    elif menu == "Activos Fijos":
        show_activos()
    elif menu == "Importar Data":
        show_importador()

def show_dashboard():
    st.title("📊 Dashboard Ejecutivo")
    
    df = db.get_transactions()
    if df.empty:
        st.info("No hay datos suficientes para mostrar el dashboard.")
        return

    # Filter by period if needed, currently global
    gastos = df[df['tipo'] == 'Gasto'].copy()
    
    # Separar Ingresos Operativos (Ventas) de Aportes de Capital
    ingresos_totales_raw = df[df['tipo'] == 'Ingreso'].copy()
    
    # Identificar Aportes de Capital (No son Ventas)
    is_aporte = ingresos_totales_raw['categoria'].str.lower().str.contains('aporte', na=False) & \
                ingresos_totales_raw['categoria'].str.lower().str.contains('capital', na=False)
                
    ingresos = ingresos_totales_raw[~is_aporte] # Solo ventas reales
    aportes_capital = ingresos_totales_raw[is_aporte]

    # --- KPIs Principales ---
    total_ventas = ingresos['monto'].sum()
    total_aportes = aportes_capital['monto'].sum()
    total_gastos = gastos['monto'].sum()
    
    # Calculo de Crédito Fiscal Perdido (SQLite guarda booleanos como 0/1)
    gastos_sin_factura = gastos[gastos['tiene_factura'] == 0]
    gastos_no_deducibles = gastos_sin_factura['monto'].sum() # Simple approach, improved later
    cf_perdido = gastos_sin_factura['monto'].sum() * 0.13
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ventas Operativas", f"Bs {total_ventas:,.2f}", delta=f"Aportes: {total_aportes:,.2f}" if total_aportes > 0 else None)
    col2.metric("Gastos Totales", f"Bs {total_gastos:,.2f}")
    col3.metric("Gastos NO Deducibles", f"Bs {gastos_no_deducibles:,.2f}", delta="Aumenta tu IUE", delta_color="inverse")
    col4.metric("Crédito Fiscal Perdido", f"Bs {cf_perdido:,.2f}", delta="Dinero perdido", delta_color="inverse")

    st.markdown("---")

    # --- Charts ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Distribución de Gastos por Categoría")
        if not gastos.empty:
            gastos_cat = gastos.groupby('categoria')['monto'].sum().sort_values(ascending=False)
            st.bar_chart(gastos_cat)
        else:
            st.info("Sin gastos registrados")

    with c2:
        st.subheader("Eficiencia Fiscal (Facturas)")
        if not gastos.empty:
            fact_counts = gastos['tiene_factura'].value_counts()
            fact_counts.index = ["Con Factura" if x else "Sin Factura" for x in fact_counts.index]
            st.write("Cantidad de Transacciones")
            st.bar_chart(fact_counts)
            
            # Advice
            pct_sf = (len(gastos_sin_factura) / len(gastos)) * 100
            if pct_sf > 20:
                st.warning(f"⚠️ El {pct_sf:.1f}% de tus gastos son sin factura. Esto incrementará tu IUE anual.")

def show_registro():
    st.title("📝 Registro de Transacciones")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Nueva Transacción")
        with st.form("transaction_form", clear_on_submit=True):
            fecha = st.date_input("Fecha", date.today())
            tipo = st.selectbox("Tipo", ["Ingreso", "Gasto"])
            categoria = st.selectbox("Categoría", [
                "Servicios Técnicos", "Venta Equipos", "Consultoría", # Ingresos
                "Aporte de Capital", # Importante para Balance Apertura
                "Materiales", "Sueldos", "Alquiler", "Servicios Básicos", "Refrigerio", "Transporte", "Impuestos" # Gastos
            ])
            detalle = st.text_input("Detalle / Glosa")
            n_factura = st.text_input("N° Factura (Opcional)")
            nit = st.text_input("NIT / CI")
            monto = st.number_input("Monto (Bs)", min_value=0.0, step=0.1)
            metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Transferencia", "QR", "Cheque"])
            
            tiene_factura = False
            aplica_retencion = False
            
            if tipo == "Gasto":
                tiene_factura = st.checkbox("¿Tiene Factura (Crédito Fiscal)?")
                if not tiene_factura:
                    aplica_retencion = st.checkbox("¿Aplicar Retención (Grossing Up)?", 
                               help="Marca esto si asumes el impuesto del proveedor (13% RC-IVA + 3% IT). El monto ingresado será el líquido pagado.")

            submitted = st.form_submit_button("Guardar Transacción")
            
            if submitted:
                if monto <= 0:
                    st.error("El monto debe ser mayor a 0")
                elif not detalle:
                    st.error("El detalle es obligatorio")
                else:
                    # Validar Bancarización
                    if logic.check_bancarization(monto):
                        st.warning(f"⚠️ ALERTA DE BANCARIZACIÓN: El monto {monto} Bs supera los 50.000 Bs. Se requiere documento de pago bancario obligatorio.")
                        # En un caso real, aquí pediríamos subir el archivo PDF del comprobante
                    
                    db.add_transaction(fecha, tipo, categoria, detalle, n_factura, nit, monto, metodo_pago, tiene_factura, aplica_retencion)
                    st.success("Transacción registrada correctamente")
                    
                    # Mostrar desglose flash
                    tax_info = logic.calculate_taxes(monto, tipo, tiene_factura, categoria, aplica_retencion)
                    if tax_info.get('iva_df', 0) == 0 and tax_info.get('it', 0) == 0 and not tax_info.get('retenciones'):
                         st.info(f"Registro Exento de Impuestos (Monto Total: {monto})")
                    elif aplica_retencion:
                         ret = tax_info['retenciones']
                         bruto = tax_info['monto_bruto']
                         st.info(f"💰 Retención Aplicada (Grossing Up): Gasto Deducible: {bruto:.2f} | A Pagar: {ret['total']:.2f} (RC-IVA: {ret['rc_iva']:.2f} + IT: {ret['it']:.2f})")
                    elif tipo == 'Ingreso':
                        st.info(f"Desglose Automático: IVA DF: {tax_info['iva_df']:.2f} | IT: {tax_info['it']:.2f} | Neto: {tax_info['ingreso_neto']:.2f}")

    with col2:
        st.subheader("Historial Reciente")
        df = db.get_transactions()
        if not df.empty:
            st.dataframe(df.head(10), use_container_width=True)
        else:
            st.info("No hay transacciones registradas aún.")

def show_reportes():
    st.title("📊 Estados Financieros y Reportes")
    
    df = db.get_transactions()
    
    if df.empty:
        st.warning("No hay datos para generar reportes.")
        return
    
    # --- FECHA DE CORTE ---
    st.markdown("### 📅 Fecha de Corte para Reportes")
    col_date, col_info = st.columns([1, 2])
    
    with col_date:
        # Convert fecha to datetime for proper filtering
        df['fecha_dt'] = pd.to_datetime(df['fecha'])
        max_date = df['fecha_dt'].max().date()
        min_date = df['fecha_dt'].min().date()
        
        cutoff_date = st.date_input(
            "Generar reportes hasta:",
            value=max_date,
            min_value=min_date,
            max_value=date.today(),
            help="Selecciona la fecha de corte. Solo se incluirán transacciones hasta esta fecha."
        )
    
    with col_info:
        st.info(f"📊 Generando reportes **al {cutoff_date.strftime('%d/%m/%Y')}**")
        
    # Filter transactions by cutoff date
    df = df[df['fecha_dt'] <= pd.to_datetime(cutoff_date)]
    
    if df.empty:
        st.warning(f"No hay transacciones hasta la fecha {cutoff_date}")
        return
    
    st.markdown("---")

    # --- PESTAÑAS DE REPORTES ---
    tab1, tab2 = st.tabs(["Resumen Financiero", "Detalle de Transacciones"])

    with tab2:
        st.subheader("🔍 Detalle de Registros")
        
        c_ing, c_gas = st.columns(2)
        with c_ing:
            st.write("🔹 **Ingresos y Aportes**")
            df_ing = df[df['tipo'] == 'Ingreso']
            st.dataframe(df_ing, use_container_width=True)
            st.metric("Total Ingresado", f"Bs {df_ing['monto'].sum():,.2f}")
            
        with c_gas:
            st.write("🔸 **Gastos y Salidas**")
            df_gas = df[df['tipo'] == 'Gasto']
            st.dataframe(df_gas, use_container_width=True)
            st.metric("Total Gastado", f"Bs {df_gas['monto'].sum():,.2f}")
            
        st.markdown("---")

    with tab1:
        # Cálculos Generales (Excluyendo Aportes de Capital de los INGRESOS OPERATIVOS)
        
        # Identificar aportes
        is_aporte = df['categoria'].str.lower().str.contains('aporte', na=False) & \
                    df['categoria'].str.lower().str.contains('capital', na=False)
        
        ingresos_operativos = df[(df['tipo'] == 'Ingreso') & (~is_aporte)]
        aportes_capital = df[(df['tipo'] == 'Ingreso') & (is_aporte)]
        
        total_ventas = ingresos_operativos['monto'].sum()
        total_aportes = aportes_capital['monto'].sum()
        total_gastos = df[df['tipo'] == 'Gasto']['monto'].sum()
        
        # Cálculo detallado para estado de resultados (Simplificado)
        breakdown = {
            'total_income': total_ventas,
            'total_gastos': total_gastos,
            'iva_df': 0, 'it_total': 0, 'net_income': 0,
            'iva_cf': 0, 'gastos_netos': 0
        }
        
        # Recalcular impuestos SOLO con ingresos OPERATIVOS (sin aportes) y gastos
        for _, row in ingresos_operativos.iterrows():
            taxes = logic.calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'], row['categoria'])
            breakdown['iva_df'] += taxes.get('iva_df', 0)
            breakdown['it_total'] += taxes.get('it', 0)
            breakdown['net_income'] += taxes.get('ingreso_neto', 0)
        
        # Track Retention Liability globally for dashboard
        retenciones_liability = 0
        
        for _, row in df[df['tipo'] == 'Gasto'].iterrows():
            clas = logic.classify_account(row['categoria'])
            # OMITIR pagos de impuestos del Estado de Resultados
            if clas == 'Excluir P&L (Pago Pasivo)':
                continue
            
            # Use 'aplica_retencion' from row safely
            ar = row.get('aplica_retencion', 0) == 1
            taxes = logic.calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'], row['categoria'], aplica_retencion=ar)
            
            breakdown['iva_cf'] += taxes.get('iva_cf', 0)
            breakdown['gastos_netos'] += taxes.get('gasto_neto', 0)
            
            if 'retenciones' in taxes:
                retenciones_liability += taxes['retenciones']['total']

        # Calcular Depreciación para el periodo (Anual por defecto)
        assets_df = db.get_assets()
        depreciacion_periodo = logic.calculate_period_depreciation(assets_df, 12)

        resultado_operativo = breakdown['net_income'] - breakdown['gastos_netos'] - breakdown['it_total'] - depreciacion_periodo

        if retenciones_liability > 0:
             st.info(f"💰 Se han generado **Bs {retenciones_liability:,.2f}** en Retenciones por Pagar (RC-IVA/IT) que debes declarar.")

        st.markdown("---")

        # --- 1. CALCULATE ALL DATA FIRST ---
        
        # A. Legal Results (Simple - Only Invoiced OR Retention)
        # Identificar aportes de capital
        is_aporte = df['categoria'].str.lower().str.contains('aporte', na=False) & \
                    df['categoria'].str.lower().str.contains('capital', na=False)
        
        df_legal_ingresos = df[(df['tipo'] == 'Ingreso') & (~is_aporte)]
        
        # EXPANDED FILTER: Invoiced OR With Retention
        # Safely handle if column doesn't exist yet (though migration handles it)
        if 'aplica_retencion' in df.columns:
            df_legal_gastos = df[(df['tipo'] == 'Gasto') & 
                                 ((df['tiene_factura'].fillna(0) == 1) | (df['aplica_retencion'].fillna(0) == 1))]
        else:
            df_legal_gastos = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'].fillna(0).astype(int) == 1)]
        
        leg_ingresos = df_legal_ingresos['monto'].sum()
        # Note: leg_gastos sum of 'monto' is CASH value. For retentions, expenses > cash.
        # We will iterate to get real total expense.
        
        leg_breakdown = {
            'total_income': leg_ingresos, 'total_gastos': 0, # Will calc
            'iva_df': 0, 'it_total': 0, 'net_income': 0,
            'iva_cf': 0, 'gastos_netos': 0
        }
        
        for _, row in df_legal_ingresos.iterrows():
            taxes = logic.calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'], row['categoria'])
            leg_breakdown['iva_df'] += taxes['iva_df']
            leg_breakdown['it_total'] += taxes['it']
            leg_breakdown['net_income'] += taxes['ingreso_neto']
            
        for _, row in df_legal_gastos.iterrows():
            clas = logic.classify_account(row['categoria'])
            if clas == 'Excluir P&L (Pago Pasivo)': continue
            
            ar = row.get('aplica_retencion', 0) == 1
            taxes = logic.calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'], row['categoria'], aplica_retencion=ar)
            
            leg_breakdown['iva_cf'] += taxes['iva_cf']
            leg_breakdown['gastos_netos'] += taxes['gasto_neto'] # This includes Grossed Up amount
            
            # For 'total_gastos' display, we prefer the 'Accounting Expense' (Gross)
            if 'monto_bruto' in taxes:
                leg_breakdown['total_gastos'] += taxes['monto_bruto']
            else:
                leg_breakdown['total_gastos'] += row['monto']
            
        assets_df = db.get_assets()
        monthly_dep = logic.calculate_period_depreciation(assets_df, 12)
        leg_resultado = leg_breakdown['net_income'] - leg_breakdown['gastos_netos'] - leg_breakdown['it_total'] - monthly_dep
        
        pdf_er_legal_simple = reports.generate_pdf_financials(leg_ingresos, leg_breakdown['total_gastos'], leg_resultado, leg_breakdown, depreciation=monthly_dep)

        # B. Legal Detailed (Fiscal Strict)
        legal_detailed_data = {
            'ingresos': {'total': 0, 'items': []},
            'costos_ventas': {'total': 0, 'items': []},
            'gastos_personal': {'total': 0, 'items': []},
            'gastos_fijos': {'total': 0, 'items': []},
            'gastos_financieros': {'total': 0, 'items': []},
            'impuestos': {'total': 0, 'items': []},
            'depreciacion': {'total': monthly_dep, 'items': []},
            'kpis': {}
        }
        
        dep_items = []
        for _, asset in assets_df.iterrows():
             annual_dep = asset['valor_inicial'] / asset['vida_util_anios']
             dep_items.append({'fecha': str(asset['fecha_adquisicion']), 'detalle': f"Depreciación: {asset['nombre']}", 'monto': annual_dep})
        legal_detailed_data['depreciacion']['items'] = dep_items

        for _, row in df_legal_ingresos.iterrows():
             if "aporte" not in row['categoria'].lower():
                 legal_detailed_data['ingresos']['total'] += row['monto']
                 legal_detailed_data['ingresos']['items'].append({'fecha': str(row['fecha']), 'detalle': f"{row['detalle']} ({row['categoria']})", 'monto': row['monto']})
        
        # Adjust Ingresos to Net for the Report Table
        iva_df_legal_total = legal_detailed_data['ingresos']['total'] * 0.13
        legal_detailed_data['ingresos']['items'].append({'fecha': '', 'detalle': '(-) IVA Débito Fiscal (13%)', 'monto': -iva_df_legal_total})
        # Note: We don't reduce 'total' here because the report generator sums the items? 
        # Wait, report generator uses 'items' to print rows, but does it recalculate total from items?
        # Reports.py: add_section sums items?
        # Let's check reports.py logic in thought process.
        # Yes, add_section sums items if not provided? No, usually it iterates. 
        # I need to ensure legal_detailed_data['ingresos']['total'] reflects NET if the table header implies NET.
        # BUT the explicit IVA item makes the sum Net.
        legal_detailed_data['ingresos']['total'] -= iva_df_legal_total

        # Accumulators for Deducible Expense (Neto or Gross)
        deducible_costos = 0
        deducible_personal = 0
        deducible_financieros = 0
        deducible_fijos = 0
        deducible_impuestos = 0 

        for _, row in df_legal_gastos.iterrows():
            clas = logic.classify_account(row['categoria'])
            ar = row.get('aplica_retencion', 0) == 1
            
            # Calculate correct expense amount (Gross if retention)
            if ar:
                 # Re-calc handy
                 bruto, _, _ = logic.calculate_grossing_up(row['monto'])
                 expense_amount = bruto
                 deducible_amount = bruto # 100% of Gross is expense
                 detalle_str = f"{row['detalle']} (Retención)"
            else:
                 expense_amount = row['monto']
                 deducible_amount = row['monto'] * 0.87 # 87% Net Cost
                 detalle_str = f"{row['detalle']} (Neto sin IVA)"
            
            # USE DEDUCIBLE AMOUNT FOR DISPLAY TO MATCH MARGINS
            item_dict = {'fecha': str(row['fecha']), 'detalle': detalle_str, 'monto': deducible_amount}
            
            if clas == 'Excluir P&L (Pago Pasivo)': continue
            elif clas == 'Impuestos': 
                 legal_detailed_data['impuestos']['total'] += deducible_amount
                 legal_detailed_data['impuestos']['items'].append(item_dict)
                 deducible_impuestos += deducible_amount 
            elif clas == 'Costo de Ventas': 
                legal_detailed_data['costos_ventas']['total'] += deducible_amount
                legal_detailed_data['costos_ventas']['items'].append(item_dict)
                deducible_costos += deducible_amount
            elif clas == 'Gastos de Personal': 
                legal_detailed_data['gastos_personal']['total'] += deducible_amount
                legal_detailed_data['gastos_personal']['items'].append(item_dict)
                deducible_personal += deducible_amount
            elif clas == 'Gastos Financieros': 
                legal_detailed_data['gastos_financieros']['total'] += deducible_amount
                legal_detailed_data['gastos_financieros']['items'].append(item_dict)
                deducible_financieros += deducible_amount
            else: 
                legal_detailed_data['gastos_fijos']['total'] += deducible_amount
                legal_detailed_data['gastos_fijos']['items'].append(item_dict)
                deducible_fijos += deducible_amount
        
        # IT is calculated on GROSS Income, so we need the original gross info.
        # We modified legal_detailed_data['ingresos']['total'] to be Net.
        # Calculate IT based on Gross (Net / 0.87).
        ingresos_netos_legal = legal_detailed_data['ingresos']['total']
        ingresos_brutos_legal = ingresos_netos_legal / 0.87 
        
        it_legal = ingresos_brutos_legal * 0.03
        legal_detailed_data['impuestos']['total'] += it_legal
        legal_detailed_data['impuestos']['items'].append({'fecha': '-', 'detalle': 'IT Generado por Ventas (3%)', 'monto': it_legal})
        deducible_impuestos += it_legal 
        
        # KPI calculations use the deducible totals now
        # Note: ingresos_netos_legal is already Net.
        
        legal_detailed_data['kpis']['margen_bruto'] = ingresos_netos_legal - deducible_costos
        legal_detailed_data['kpis']['bait'] = (legal_detailed_data['kpis']['margen_bruto'] - deducible_personal - deducible_fijos - monthly_dep)
        legal_detailed_data['kpis']['utilidad_antes_iue'] = (legal_detailed_data['kpis']['bait'] - deducible_financieros - deducible_impuestos)
        legal_detailed_data['kpis']['iue'] = max(0, legal_detailed_data['kpis']['utilidad_antes_iue'] * 0.25)
        legal_detailed_data['kpis']['utilidad_neta'] = legal_detailed_data['kpis']['utilidad_antes_iue'] - legal_detailed_data['kpis']['iue']
        
        pdf_er_legal_detailed = reports.generate_pdf_legal_detailed(legal_detailed_data, "Acumulado Anual")


        # C. Managerial Detailed
        mgr_data = {
            'ingresos': {'total': 0, 'items': []}, 'costos_ventas': {'total': 0, 'items': []},
            'gastos_personal': {'total': 0, 'items': []}, 'gastos_fijos': {'total': 0, 'items': []},
            'gastos_financieros': {'total': 0, 'items': []}, 'impuestos': {'total': 0, 'items': []},
            'depreciacion': {'total': monthly_dep, 'items': dep_items}, 'kpis': {}
        }
        
        for _, row in df[df['tipo'] == 'Ingreso'].iterrows():
             if "aporte" not in row['categoria'].lower():
                 mgr_data['ingresos']['total'] += row['monto']
                 mgr_data['ingresos']['items'].append({'fecha': str(row['fecha']), 'detalle': f"{row['detalle']} ({row['categoria']})", 'monto': row['monto']})
                 
        for _, row in df[df['tipo'] == 'Gasto'].iterrows():
            clas = logic.classify_account(row['categoria'])
            ar = row.get('aplica_retencion', 0) == 1
            
            # For Managerial, we want REAL COST. 
            # If retention, real cost is BRUTO.
            if ar:
                 bruto, _, _ = logic.calculate_grossing_up(row['monto'])
                 expense_amount = bruto
                 detalle_str = f"{row['detalle']} (Costo Real c/ Retención)"
            else:
                 expense_amount = row['monto'] # 100% Cash/Invoice
                 detalle_str = f"{row['detalle']} ({row['categoria']})"
            
            item_dict = {'fecha': str(row['fecha']), 'detalle': detalle_str, 'monto': expense_amount}
            
            if clas == 'Excluir P&L (Pago Pasivo)':
                 # Allow Tax payments for Cash Basis Managerial Report
                 # User wants to see "Pago IVA", "Pago IT" from Excel
                 cat_str = row['categoria'].lower()
                 if "pago" in cat_str and ("impuesto" in cat_str or "iva" in cat_str or "it" in cat_str):
                      mgr_data['impuestos']['total'] += expense_amount
                      mgr_data['impuestos']['items'].append(item_dict)
                      continue
                 else:
                      continue

            elif clas == 'Impuestos': 
                 mgr_data['impuestos']['total'] += expense_amount
                 mgr_data['impuestos']['items'].append(item_dict)
            elif clas == 'Costo de Ventas': 
                mgr_data['costos_ventas']['total'] += expense_amount
                mgr_data['costos_ventas']['items'].append(item_dict)
            elif clas == 'Gastos de Personal': 
                mgr_data['gastos_personal']['total'] += expense_amount
                mgr_data['gastos_personal']['items'].append(item_dict)
            elif clas == 'Gastos Financieros': 
                mgr_data['gastos_financieros']['total'] += expense_amount
                mgr_data['gastos_financieros']['items'].append(item_dict)
            else: 
                mgr_data['gastos_fijos']['total'] += expense_amount
                mgr_data['gastos_fijos']['items'].append(item_dict)
        
        # Taxes: REMOVED Accruals (IVA Neto / IT Calculated) to use CASH BASIS (Actual Payments)
        # iva_a_pagar_mgr = max(0, breakdown['iva_df'] - breakdown['iva_cf'])
        # it_virtual = mgr_data['ingresos']['total'] * 0.03
        
        mgr_data['kpis']['margen_bruto'] = mgr_data['ingresos']['total'] - mgr_data['costos_ventas']['total']
        mgr_data['kpis']['bait'] = mgr_data['kpis']['margen_bruto'] - mgr_data['gastos_personal']['total'] - mgr_data['gastos_fijos']['total'] - mgr_data['depreciacion']['total']
        mgr_data['kpis']['utilidad_antes_iue'] = (mgr_data['kpis']['bait'] - mgr_data['gastos_financieros']['total'] - mgr_data['impuestos']['total'])
        mgr_data['kpis']['iue'] = legal_detailed_data['kpis']['iue']
        mgr_data['kpis']['utilidad_neta'] = mgr_data['kpis']['utilidad_antes_iue'] - mgr_data['kpis']['iue']
        
        pdf_mgr_detailed = reports.generate_pdf_managerial_detailed(mgr_data, "Acumulado Anual")
        
        # D. Balance Sheets
        balance_data = logic.calculate_balance_sheet(df, assets_df, cutoff_date)
        balance_real_data = logic.calculate_balance_sheet_real(df, assets_df, cutoff_date)
        
        pdf_balance_sin = reports.generate_pdf_balance_sin(balance_data, f"Al {cutoff_date.strftime('%d/%m/%Y')}")
        pdf_balance_real = reports.generate_pdf_balance_real(balance_real_data, f"Al {cutoff_date.strftime('%d/%m/%Y')}")
        
        # E. Gerencial Completo
        pdf_gerencial_completo = reports.generate_pdf_gerencial_completo(balance_data, mgr_data, f"Gestión 2025 (Al {cutoff_date})")
        
        # F. Excel RCV
        excel_rcv = reports.generate_excel_rcv(df)

        # --- 2. RENDER SECTIONS ---
        
        # COLUMNS LAYOUT
        st.markdown("### 📂 Descarga de Reportes")
        col_legal, col_gerencial = st.columns(2)
        
        with col_legal:
            st.subheader("🏛️ Reportes Legales (SIN)")
            st.info("Basado estrictamente en facturas.")
            
            # 1. ER Legal
            st.download_button(
                label="📄 Estado de Resultados (Legal)",
                data=pdf_er_legal_simple,
                file_name=f"ER_Legal_Simple_{date.today()}.pdf",
                mime="application/pdf",
                help="Excluye gastos sin factura",
                key="btn_er_legal_simple"
            )
            
            # 2. ER Legal Detallado
            st.download_button(
                label="⚖️ Estado de Resultados Legal Detallado",
                data=pdf_er_legal_detailed,
                file_name=f"ER_Legal_Detallado_{date.today()}.pdf",
                mime="application/pdf",
                help="Formato detallado con items y depreciación",
                key="btn_er_legal_detallado"
            )
            
            # 3. Balance Legal SIN
            st.download_button(
                label="🏛️ Balance General Legal (SIN)",
                data=pdf_balance_sin,
                file_name=f"Balance_General_SIN_{cutoff_date.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                help="Solo transacciones facturadas",
                key="btn_balance_sin"
            )
            
        with col_gerencial:
            st.subheader("📈 Reportes Gerenciales (Reales)")
            st.info("Incluye realidad de caja y gastos sin factura.")
            
            # 1. ER Gerencial Detallado
            st.download_button(
                label="📊 Estado de Resultados Gerencial Detallado",
                data=pdf_mgr_detailed,
                file_name=f"ER_Gerencial_Detallado_{date.today()}.pdf",
                mime="application/pdf",
                help="Incluye desglose de cada transacción, EBITDA, Costo de Ventas y Márgenes.",
                key="btn_er_gerencial_detallado"
            )
            
            # 2. Balance Gerencial
            st.download_button(
                label="💰 Balance General Gerencial (Real)",
                data=pdf_balance_real,
                file_name=f"Balance_General_Real_{cutoff_date.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                help="Refleja caja real y gastos no deducibles",
                key="btn_balance_real"
            )
            
            # 3. Informe Completo
            st.download_button(
                label="📈 Informe Gerencial Completo",
                data=pdf_gerencial_completo,
                file_name=f"Informe_Gerencial_{cutoff_date.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                help="Informe estratégico de 5 páginas",
                key="btn_informe_gerencial_completo"
            )


        st.markdown("---")
        
        # LIBRO DIARIO
        st.subheader("📚 Libros Contables")
        # Generate Libro Diario PDF
        pdf_diario = reports.generate_pdf_libro_diario(df)
        st.download_button(
            label="📒 Descargar Libro Diario (PDF)",
            data=pdf_diario,
            file_name=f"Libro_Diario_{date.today()}.pdf",
            mime="application/pdf",
            key="btn_libro_diario"
        )
        
        st.markdown("---")
        
        # RCV Button (Bottom)
        st.subheader("📥 Exportación de Datos")
        st.download_button(
            label="📥 Descargar RCV (Formato SIAT Excel)",
            data=excel_rcv,
            file_name=f"RCV_WARP6_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="btn_rcv_excel"
        )
        
        st.markdown("---")

        # CAJA NETA FINAL (Moved here as context)
        st.subheader("💰 Posición de Caja Neta Final (Liquidez Real)")
        st.info("Dinero disponible tras pagar todos los gastos e impuestos.")
        
        # Recalculate quick numbers for Box
        ingresos_efectivo = df[(df['tipo'] == 'Ingreso') & 
                               (~df['categoria'].str.lower().str.contains('activo', na=False))]['monto'].sum()
        
        total_outflow = 0
        pagos_impuestos_realizados = 0
        for _, row in df[df['tipo'] == 'Gasto'].iterrows():
             total_outflow += row['monto']
             
             # Rastrear cuánto pagamos de impuestos (para mostrarlo desglosado si se quiere)
             if "impuesto" in row['categoria'].lower() or "it" in row['categoria'].lower():
                 pagos_impuestos_realizados += row['monto']

        caja_operativa_bruta = ingresos_efectivo - total_outflow
        
        # 2. Impuestos LEGALES Por Pagar (Futuros)
        # IUE que se pagará al cierre de gestión (Calculado en el reporte legal)
        iue_a_pagar = legal_detailed_data['kpis']['iue']
        
        # 3. Caja Líquida Final
        caja_final_neta = caja_operativa_bruta - iue_a_pagar
        
        col_caja1, col_caja2, col_caja3 = st.columns(3)
        col_caja1.metric("1. Caja Operativa (Hoy)", f"Bs {caja_operativa_bruta:,.2f}", help="Dinero físico actual (Ingresos - Gastos Totales)")
        col_caja2.metric("2. (-) Reserva para IUE", f"Bs {iue_a_pagar:,.2f}", help="Impuesto a las Utilidades que deberás pagar el próximo año", delta_color="inverse")
        col_caja3.metric("3. (=) CAJA LÍQUIDA REAL", f"Bs {caja_final_neta:,.2f}", delta="Tu ganancia real de bolsillo")
        
        st.markdown("---")
        
        # --- VALIDACIÓN Y COMPARACIÓN ---
        st.markdown("#### ✅ Validación de Ecuación Contable")
        
        col_comp1, col_comp2 = st.columns(2)
        
        with col_comp1:
            st.markdown("**Balance SIN (Solo Facturado)**")
            val = balance_data['validacion']
            st.metric("Total Activos", f"Bs {val['activos']:,.2f}")
            st.metric("Pasivo + Patrimonio", f"Bs {val['pasivo_patrimonio']:,.2f}")
            if val['cuadra']:
                st.success(f"✅ Cuadra (Dif: {val['diferencia']:.2f})")
            else:
                st.error(f"⚠️ Descuadre: Bs {val['diferencia']:,.2f}")
        
        with col_comp2:
            st.markdown("**Balance Real (Gerencial)**")
            val_real = balance_real_data['validacion']
            st.metric("Total Activos", f"Bs {val_real['activos']:,.2f}")
            st.metric("Pasivo + Patrimonio", f"Bs {val_real['pasivo_patrimonio']:,.2f}")
            if val_real['cuadra']:
                st.success(f"✅ Cuadra (Dif: {val_real['diferencia']:.2f})")
            else:
                st.error(f"⚠️ Descuadre: Bs {val_real['diferencia']:,.2f}")
        
        # Explicación de diferencias
        st.info(f"""
        **💡 Diferencia entre balances:**
        - **Caja SIN**: Bs {balance_data['activos']['corriente']['caja']:,.2f} (ignora gastos sin factura)
        - **Caja Real**: Bs {balance_real_data['activos']['corriente']['caja']:,.2f} (incluye todos los gastos)
        - **Gastos No Deducibles**: Bs {balance_real_data['info_adicional']['gastos_sin_factura']:,.2f}
        """)
        
        if not val['cuadra'] or not val_real['cuadra']:
             st.warning("Revise si hay gastos/ingresos inconsistentes o problemas de redondeo.")
             
        # Debug View
        with st.expander("🔍 Ver Desglose Contable Detallado"):
            st.json(balance_data)
        
        gastos_sf = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 0)]
        if not gastos_sf.empty:
            st.warning(f"Tienes {len(gastos_sf)} gastos sin factura que te hacen perder dinero.")
            pdf_shield = reports.generate_pdf_tax_shield(gastos_sf)
            st.download_button(
                label="📉 Reporte de Dinero Perdido (Tax Shield)",
                data=pdf_shield,
                file_name=f"Reporte_Fiscal_Perdida_{date.today()}.pdf",
                mime="application/pdf",
                key="btn_tax_shield"
            )
        else:
            st.success("¡Excelente! Todos tus gastos tienen factura.")
            
        
        
        st.markdown("---")
        
        # --- CALENDARIO FISCAL MENSUAL ---
        st.subheader("📅 Calendario Fiscal Mensual")
        st.markdown("*Desglose mes a mes de impuestos generados y pagados*")
        
        # Usar la nueva lógica centralizada de resúmenes fiscales mensuales
        tax_summary = logic.get_monthly_tax_summary(df)
        
        if not tax_summary:
            st.info("No hay datos suficientes para mostrar el calendario mensual.")
        else:
            monthly_data = []
            for mes, vals in tax_summary.items():
                monthly_data.append({
                    'Mes': mes,
                    'IVA Adeudado': vals['iva_determinado'],
                    'IVA Pagado': vals['iva_pagado'],
                    'IT Adeudado': vals['it_determinado'],
                    'IT Pagado': vals['it_pagado'],
                    'Total Adeudado': vals['total_determinado'],
                    'Total Pagado': vals['total_pagado'],
                    'Diferencia': vals['total_determinado'] - vals['total_pagado']
                })
            
            df_monthly = pd.DataFrame(monthly_data)
            
            # Formatear para mostrar
            df_display = df_monthly.copy()
            for col in df_display.columns:
                if col != 'Mes':
                    df_display[col] = df_display[col].apply(lambda x: f"Bs {x:,.2f}")
            
            st.dataframe(df_display, use_container_width=True)
            
            # Alerta de diferencias
            diferencias = df_monthly[df_monthly['Diferencia'].abs() > 100]
            if not diferencias.empty:
                st.warning(f"⚠️ Hay {len(diferencias)} mes(es) con diferencias significativas entre lo adeudado y lo pagado.")
                with st.expander("Ver detalles de diferencias"):
                    for _, row in diferencias.iterrows():
                        if row['Diferencia'] > 0:
                            st.error(f"**{row['Mes']}**: Falta pagar Bs {row['Diferencia']:,.2f}")
                        else:
                            st.success(f"**{row['Mes']}**: Pago en exceso de Bs {abs(row['Diferencia']):,.2f}")


def show_activos():
    st.title("💻 Activos Fijos y Depreciación (DS 24051)")
    
    st.markdown("""
    > **Nota Normativa:** Equipos de Computación se deprecian en 4 años (25% anual).
    > Para el cálculo exacto, debe ingresar la UFV actual.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Registrar Nuevo Activo")
        with st.form("asset_form"):
            nombre = st.text_input("Nombre del Equipo (ej. Servidor Dell, Escritorio)")
            fecha_adq = st.date_input("Fecha de Compra / Aporte")
            valor = st.number_input("Valor de Compra/Aporte (Bs)", min_value=0.0)
            
            # Selección de Rubro (DS 24051)
            rubro_opciones = {
                "Equipos de Computación": 4,
                "Herramientas en General": 4,
                "Muebles y Enseres": 10,
                "Vehículos Automotores": 5,
                "Maquinaria en General": 8
            }
            rubro = st.selectbox("Rubro / Categoría", list(rubro_opciones.keys()))
            vida_util = st.number_input("Vida Útil (Años)", value=rubro_opciones[rubro], disabled=True)
            
            submit_asset = st.form_submit_button("Registrar Activo")
            
            if submit_asset:
                db.add_asset(nombre, fecha_adq, valor, vida_util, rubro)
                st.success(f"Activo registrado como '{rubro}'.")

    with col2:
        st.subheader("📋 Lista de Activos Fijos")
        assets = db.get_assets()
        
        if not assets.empty:
            # Mostrar tabla con opción de borrar
            for index, row in assets.iterrows():
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**{row['nombre']}** ({row['rubro']}) - Bs {row['valor_inicial']:,.2f}")
                with c2:
                    if st.button("🗑️ Eliminar", key=f"del_{row['id']}"):
                        db.delete_asset(row['id'])
                        st.experimental_rerun()
            
            st.divider()
            
            st.subheader("Calculadora de Depreciación")
            asset_to_calc = st.selectbox("Seleccionar Activo para Cálculo", assets['nombre'])
            sel_asset = assets[assets['nombre'] == asset_to_calc].iloc[0]
            
            st.write(f"**Valor Original:** Bs {sel_asset['valor_inicial']:,.2f}")
            st.write(f"**Fecha Compra:** {sel_asset['fecha_adquisicion']}")
            
            # Simulación UFV
            ufv_inicial = st.number_input("UFV Fecha Compra (Ej. 2.45000)", value=2.45000, format="%.5f")
            ufv_actual = st.number_input("UFV Hoy (Ej. 2.50000)", value=2.50000, format="%.5f")
            
            if st.button("Calcular Actualización y Depreciación"):
                incremento_ufv = ufv_actual / ufv_inicial
                valor_actualizado = sel_asset['valor_inicial'] * incremento_ufv
                ipa = valor_actualizado - sel_asset['valor_inicial'] # Ajuste por Inflación
                
                # Depreciación (Simplificada lineal por dias)
                dias_uso, porcentaje_uso = logic.check_asset_status(sel_asset['fecha_adquisicion'], sel_asset['vida_util_anios'])
                depreciacion_acumulada = (valor_actualizado * (porcentaje_uso / 100))
                valor_neto = valor_actualizado - depreciacion_acumulada
                
                st.metric("Valor Actualizado (AITB)", f"Bs {valor_actualizado:,.2f}", delta=f"IPA: {ipa:,.2f}")
                st.metric("Depreciación Acumulada", f"Bs {depreciacion_acumulada:,.2f}")
                st.metric("Valor Neto en Libros", f"Bs {valor_neto:,.2f}")
                
        else:
            st.info("Registre un activo para calcular su depreciación.")

def show_importador():
    st.title("📤 Importación Masiva de Datos")
    
    st.markdown("""
    Carga tus transacciones desde Excel usando nuestra plantilla estandarizada.
    
    **Instrucciones:**
    1. Descarga la plantilla (¡Actualizada!).
    2. Copia tus datos en las columnas correspondientes.
       - *Tipo*: Debe ser 'Ingreso' o 'Gasto'.
       - *Tiene_Factura*: 'Si' o 'No'.
       - *Aplica_Retencion*: 'Si' si deseas que el sistema calcule el Grossing Up (asumiendo impuestos).
    3. Sube el archivo completado.

    > **ℹ️ Categorías Especiales:**
    > * Si usas **"Aporte de Capital"**, el sistema NO calculará impuestos (IVA/IT).
    > * Si usas **"Pago de Impuestos"**, no buscará crédito fiscal.
    """)
    
    # 1. Download Template
    template_data = importer.generate_template()
    st.download_button(
        label="📥 Descargar Plantilla Excel (v2 - con Retenciones)",
        data=template_data,
        file_name="plantilla_importacion_warp6_v2.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    # 2. Upload
    uploaded_file = st.file_uploader("Subir Archivo Excel Completado", type=["xlsx"])
    
    if uploaded_file:
        df_preview, error = importer.process_import_file(uploaded_file)
        
        if error:
            if isinstance(error, list):
                st.error("Errores encontrados en el archivo:")
                for e in error:
                    st.write(f"- {e}")
            else:
                st.error(error)
        else:
            st.success(f"✅ Archivo procesado correctamente. {len(df_preview)} registros encontrados.")
            st.subheader("Vista Previa")
            st.dataframe(df_preview.head())
            
            replace_existing = st.checkbox("⚠️ Reemplazar transacciones existentes (Mantiene los Activos Fijos intactos)", value=True)

            if st.button("Confirmar e Importar a Base de Datos"):
                count = 0
                progress_bar = st.progress(0)
                
                if replace_existing:
                    db.clear_all_transactions()
                    
                for idx, row in df_preview.iterrows():
                    db.add_transaction(
                        row['fecha'],
                        row['tipo'],
                        row['categoria'],
                        row['detalle'],
                        row['n_factura'],
                        row['nit'],
                        row['monto'],
                        row['metodo_pago'],
                        row['tiene_factura'],
                        row['aplica_retencion']
                    )
                    count += 1
                    progress_bar.progress(count / len(df_preview))
                
                st.balloons()
                st.success(f"¡Éxito! Se importaron {count} transacciones.")
                st.info("Ve al menú 'Registro' o 'Reportes' para ver los datos.")

if __name__ == "__main__":
    main()
