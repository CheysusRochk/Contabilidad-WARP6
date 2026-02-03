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
            if tipo == "Gasto":
                tiene_factura = st.checkbox("¿Tiene Factura (Crédito Fiscal)?")
            
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
                    
                    db.add_transaction(fecha, tipo, categoria, detalle, n_factura, nit, monto, metodo_pago, tiene_factura)
                    st.success("Transacción registrada correctamente")
                    
                    # Mostrar desglose flash
                    tax_info = logic.calculate_taxes(monto, tipo, tiene_factura, categoria)
                    if tax_info.get('iva_df', 0) == 0 and tax_info.get('it', 0) == 0:
                         st.info(f"Registro Exento de Impuestos (Monto Total: {monto})")
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
        
        for _, row in df[df['tipo'] == 'Gasto'].iterrows():
            clas = logic.classify_account(row['categoria'])
            # OMITIR pagos de impuestos del Estado de Resultados
            if clas == 'Excluir P&L (Pago Pasivo)':
                continue
                
            taxes = logic.calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'], row['categoria'])
            breakdown['iva_cf'] += taxes.get('iva_cf', 0)
            breakdown['gastos_netos'] += taxes.get('gasto_neto', 0)

        # Calcular Depreciación para el periodo (Anual por defecto)
        assets_df = db.get_assets()
        depreciacion_periodo = logic.calculate_period_depreciation(assets_df, 12)

        resultado_operativo = breakdown['net_income'] - breakdown['gastos_netos'] - breakdown['it_total'] - depreciacion_periodo

        # Métricas Clave
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ventas Netas", f"Bs {breakdown['net_income']:,.2f}", help="Ingresos Operativos menos IVA")
        c2.metric("Aportes Capital", f"Bs {total_aportes:,.2f}", help="Dinero inyectado (No paga impuestos)")
        c3.metric("IVA a Pagar (Aprox)", f"Bs {max(0, breakdown['iva_df'] - breakdown['iva_cf']):,.2f}")
        c4.metric("Resultado Operativo", f"Bs {resultado_operativo:,.2f}", delta_color="normal", help="Incluye deducción por Depreciación")

        st.markdown("---")
        
        col_l, col_r = st.columns(2)
        
        with col_l:
            st.subheader("Estado de Resultados (Provisional)")
            st.write(pd.DataFrame({
                "Concepto": ["Ingresos Operativos Netos (87%)", "(-) Gastos Netos Deducibles", "(-) Impuesto IT (3%)", "(-) Depreciación Activos", "= RESULTADO ANTES DE IMPUESTOS (IUE)"],
                "Monto (Bs)": [breakdown['net_income'], -breakdown['gastos_netos'], -breakdown['it_total'], -depreciacion_periodo, resultado_operativo]
            }))

        with col_r:
            st.subheader("Exportar Libros Legales")
            
            # Excel RCV
            excel_data = reports.generate_excel_rcv(df)
            st.download_button(
                label="📥 Descargar RCV (Formato SIAT Excel)",
                data=excel_data,
                file_name=f"RCV_WARP6_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        # --- ESTADO DE RESULTADOS LEGAL (ESTRICTO) ---
        # Filtramos solo lo que tiene factura (o son Ingresos declarados)
        # Ingresos: Todo EXCEPTO Aportes de Capital
        # Gastos: SOLO con factura.
        
        # Identificar aportes de capital
        is_aporte = df['categoria'].str.lower().str.contains('aporte', na=False) & \
                    df['categoria'].str.lower().str.contains('capital', na=False)
        
        df_legal_ingresos = df[(df['tipo'] == 'Ingreso') & (~is_aporte)]  # Excluir aportes
        df_legal_gastos = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 1)]
        
        # Calcular totales para Legal
        leg_ingresos = df_legal_ingresos['monto'].sum()
        leg_gastos = df_legal_gastos['monto'].sum()
        
        # Re-calcular impuestos Ley base a este subset
        leg_breakdown = {
            'total_income': leg_ingresos,
            'total_gastos': leg_gastos,
            'iva_df': 0, 'it_total': 0, 'net_income': 0,
            'iva_cf': 0, 'gastos_netos': 0
        }
        
        # Procesar Ingresos (Legal)
        for _, row in df_legal_ingresos.iterrows():
            taxes = logic.calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'], row['categoria'])
            leg_breakdown['iva_df'] += taxes['iva_df']
            leg_breakdown['it_total'] += taxes['it']
            leg_breakdown['net_income'] += taxes['ingreso_neto']
            
        # Procesar Gastos (Solo Facturados)
        for _, row in df_legal_gastos.iterrows():
            clas = logic.classify_account(row['categoria'])
            # OMITIR pagos de impuestos del Estado de Resultados Legal
            if clas == 'Excluir P&L (Pago Pasivo)':
                continue
                
            taxes = logic.calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'], row['categoria'])
            leg_breakdown['iva_cf'] += taxes['iva_cf']
            leg_breakdown['gastos_netos'] += taxes['gasto_neto']
            
        leg_resultado = leg_breakdown['net_income'] - leg_breakdown['gastos_netos'] - leg_breakdown['it_total']

        pdf_data = reports.generate_pdf_financials(leg_ingresos, leg_gastos, leg_resultado, leg_breakdown)
        st.download_button(
            label="📄 Estado de Resultados (Legal - Solo Facturado)",
            data=pdf_data,
            file_name=f"ER_Legal_Estricto_{date.today()}.pdf",
            mime="application/pdf",
            help="Excluye gastos sin factura (Sueldos en negro, recibos, etc.)",
            key="btn_er_legal_simple"
        )
        
        # --- CÁLCULO GERENCIAL DETALLADO ---
        # Preparar estructura de datos granular
        mgr_data = {
            'ingresos': {'total': 0, 'items': []},
            'costos_ventas': {'total': 0, 'items': []},
            'gastos_personal': {'total': 0, 'items': []},
            'gastos_fijos': {'total': 0, 'items': []},
            'gastos_financieros': {'total': 0, 'items': []},
            'impuestos': {'total': 0, 'items': []},
            'depreciacion': {'total': 0, 'items': []},
            'kpis': {}
        }
        
        # 1. Ingresos Detallados
        for _, row in df[df['tipo'] == 'Ingreso'].iterrows():
             # Excluir 'Aporte capital' si queremos ser puros, logicamente ya lo hacemos en impuestos
             if "aporte" not in row['categoria'].lower():
                 mgr_data['ingresos']['total'] += row['monto']
                 mgr_data['ingresos']['items'].append({
                     'fecha': str(row['fecha']), 'detalle': f"{row['detalle']} ({row['categoria']})", 'monto': row['monto']
                 })
                 
        # 2. Gastos Detallados + Clasificación
        gastos_df_all = df[df['tipo'] == 'Gasto']
        
        for _, row in gastos_df_all.iterrows():
            clas = logic.classify_account(row['categoria'])
            item_dict = {'fecha': str(row['fecha']), 'detalle': f"{row['detalle']} ({row['categoria']})", 'monto': row['monto']}
            
            # Clasificacion
            if clas == 'Excluir P&L (Pago Pasivo)':
                continue # No entra al Estado de Resultados
            elif clas == 'Impuestos': 
                 # Los impuestos directos pagados explicitamente (Tasas, Patentes, IT no virtual)
                 mgr_data['impuestos']['total'] += row['monto']
                 mgr_data['impuestos']['items'].append(item_dict)
            elif clas == 'Costo de Ventas': 
                mgr_data['costos_ventas']['total'] += row['monto']
                mgr_data['costos_ventas']['items'].append(item_dict)
            elif clas == 'Gastos de Personal': 
                mgr_data['gastos_personal']['total'] += row['monto']
                mgr_data['gastos_personal']['items'].append(item_dict)
            elif clas == 'Gastos Financieros': 
                mgr_data['gastos_financieros']['total'] += row['monto']
                mgr_data['gastos_financieros']['items'].append(item_dict)
            else: 
                mgr_data['gastos_fijos']['total'] += row['monto']
                mgr_data['gastos_fijos']['items'].append(item_dict)
        
        # Agregar IT Calculado como Gasto de Impuestos (porque no siempre se registra el gasto)
        # Ojo: Si ya registramos el IT como gasto automatico en DB, se duplicaria.
        # Asumimos que el usuario NO registra el IT manualmente, asi que lo agregamos como item "Virtual"
        # Pero el IT es 3% de Ingresos.
        it_virtual = mgr_data['ingresos']['total'] * 0.03
        mgr_data['impuestos']['total'] += it_virtual
        mgr_data['impuestos']['items'].append({'fecha': '-', 'detalle': 'IT Generado por Ventas (3%)', 'monto': it_virtual})

        # 3. Depreciación
        assets_df = db.get_assets()
        monthly_dep = logic.calculate_period_depreciation(assets_df, 12) # Anual
        mgr_data['depreciacion']['total'] = monthly_dep
        # Detalle de depreciación por activo
        for _, asset in assets_df.iterrows():
             annual_dep = asset['valor_inicial'] / asset['vida_util_anios']
             mgr_data['depreciacion']['items'].append({
                 'fecha': str(asset['fecha_adquisicion']), 
                 'detalle': f"Depreciación: {asset['nombre']}", 
                 'monto': annual_dep
             })
             
        # 4. KPIs
        mgr_data['kpis']['margen_bruto'] = mgr_data['ingresos']['total'] - mgr_data['costos_ventas']['total']
        
        mgr_data['kpis']['bait'] = (
            mgr_data['kpis']['margen_bruto'] 
            - mgr_data['gastos_personal']['total'] 
            - mgr_data['gastos_fijos']['total'] 
            - mgr_data['depreciacion']['total']
        )
        
        mgr_data['kpis']['utilidad_antes_iue'] = (
            mgr_data['kpis']['bait'] 
            - mgr_data['gastos_financieros']['total'] 
            - mgr_data['impuestos']['total']
        )
        
        mgr_data['kpis']['iue'] = max(0, mgr_data['kpis']['utilidad_antes_iue'] * 0.25)
        mgr_data['kpis']['utilidad_neta'] = mgr_data['kpis']['utilidad_antes_iue'] - mgr_data['kpis']['iue']
        
        
        pdf_mgr = reports.generate_pdf_managerial_detailed(mgr_data, "Acumulado Anual")
        st.download_button(
            label="📊 Estado de Resultados (GERENCIAL DETALLADO)",
            data=pdf_mgr,
            file_name=f"ER_Gerencial_Detallado_{date.today()}.pdf",
            mime="application/pdf",
            help="Incluye desglose de cada transacción, EBITDA, Costo de Ventas y Márgenes.",
            key="btn_er_gerencial_detallado"
        )
        
        # --- REPORTE LEGAL DETALLADO (Con factura + Depreciación) ---
        st.markdown("---")
        st.subheader("⚖️ Estado de Resultados Legal (SIN)")
        
        # Usar misma estructura que mgr_data pero FILTRADO solo con factura
        legal_detailed_data = {
            'ingresos': {'total': 0, 'items': []},
            'costos_ventas': {'total': 0, 'items': []},
            'gastos_personal': {'total': 0, 'items': []},
            'gastos_fijos': {'total': 0, 'items': []},
            'gastos_financieros': {'total': 0, 'items': []},
            'impuestos': {'total': 0, 'items': []},
            'depreciacion': {'total': monthly_dep, 'items': mgr_data['depreciacion']['items']},  # Depreciación siempre aplica
            'kpis': {}
        }
        
        # Ingresos facturados (todos son operativos ya)
        for _, row in df_legal_ingresos.iterrows():
             if "aporte" not in row['categoria'].lower():
                 legal_detailed_data['ingresos']['total'] += row['monto']
                 legal_detailed_data['ingresos']['items'].append({
                     'fecha': str(row['fecha']), 'detalle': f"{row['detalle']} ({row['categoria']})", 'monto': row['monto']
                 })
        
        # Gastos SOLO facturados + clasificación
        for _, row in df_legal_gastos.iterrows():
            clas = logic.classify_account(row['categoria'])
            item_dict = {'fecha': str(row['fecha']), 'detalle': f"{row['detalle']} ({row['categoria']})", 'monto': row['monto']}
            
            if clas == 'Excluir P&L (Pago Pasivo)':
                continue
            elif clas == 'Impuestos': 
                 legal_detailed_data['impuestos']['total'] += row['monto']
                 legal_detailed_data['impuestos']['items'].append(item_dict)
            elif clas == 'Costo de Ventas': 
                legal_detailed_data['costos_ventas']['total'] += row['monto']
                legal_detailed_data['costos_ventas']['items'].append(item_dict)
            elif clas == 'Gastos de Personal': 
                legal_detailed_data['gastos_personal']['total'] += row['monto']
                legal_detailed_data['gastos_personal']['items'].append(item_dict)
            elif clas == 'Gastos Financieros': 
                legal_detailed_data['gastos_financieros']['total'] += row['monto']
                legal_detailed_data['gastos_financieros']['items'].append(item_dict)
            else: 
                legal_detailed_data['gastos_fijos']['total'] += row['monto']
                legal_detailed_data['gastos_fijos']['items'].append(item_dict)
        
        # Agregar IT calculado
        it_legal = legal_detailed_data['ingresos']['total'] * 0.03
        legal_detailed_data['impuestos']['total'] += it_legal
        legal_detailed_data['impuestos']['items'].append({'fecha': '-', 'detalle': 'IT Generado por Ventas (3%)', 'monto': it_legal})
        
        # KPIs para Legal - USAR MONTOS NETOS (87%) PARA CÁLCULOS FISCALES
        # Ingresos Netos = Ingresos Brutos - IVA DF
        ingresos_brutos_legal = legal_detailed_data['ingresos']['total']
        iva_df_legal = ingresos_brutos_legal * 0.13
        ingresos_netos_legal = ingresos_brutos_legal - iva_df_legal
        
        # Costos y Gastos Netos = Brutos * 0.87 (si tienen factura)
        costos_netos_legal = legal_detailed_data['costos_ventas']['total'] * 0.87
        gastos_personal_netos = legal_detailed_data['gastos_personal']['total'] * 0.87
        gastos_fijos_netos = legal_detailed_data['gastos_fijos']['total'] * 0.87
        gastos_financieros_netos = legal_detailed_data['gastos_financieros']['total'] * 0.87
        
        # Impuestos pagados (IT, patentes, etc.) - estos ya son netos, no tienen IVA
        impuestos_directos_legal = legal_detailed_data['impuestos']['total']
        
        legal_detailed_data['kpis']['margen_bruto'] = ingresos_netos_legal - costos_netos_legal
        legal_detailed_data['kpis']['bait'] = (legal_detailed_data['kpis']['margen_bruto'] - 
                                                gastos_personal_netos - 
                                                gastos_fijos_netos - 
                                                legal_detailed_data['depreciacion']['total'])
        legal_detailed_data['kpis']['utilidad_antes_iue'] = (legal_detailed_data['kpis']['bait'] - 
                                                              gastos_financieros_netos - 
                                                              impuestos_directos_legal)
        legal_detailed_data['kpis']['iue'] = max(0, legal_detailed_data['kpis']['utilidad_antes_iue'] * 0.25)
        legal_detailed_data['kpis']['utilidad_neta'] = legal_detailed_data['kpis']['utilidad_antes_iue'] - legal_detailed_data['kpis']['iue']
        
        pdf_legal_det = reports.generate_pdf_legal_detailed(legal_detailed_data, "Acumulado Anual")
        st.download_button(
            label="⚖️ Estado de Resultados (LEGAL DETALLADO - Incluye Depreciación)",
            data=pdf_legal_det,
            file_name=f"ER_Legal_Detallado_{date.today()}.pdf",
            mime="application/pdf",
            help="Solo gastos facturados + Depreciación. Cumplimiento normativo.",
            key="btn_er_legal_detallado"
        )

        st.markdown("---")
        
        # --- BALANCE GENERAL (SIN / FORMAL) ---
        st.subheader("📗 Balance General")
        
        # Calcular Balance usando la nueva lógica CONTABLE balanceada
        assets_df = db.get_assets()
        balance_data = logic.calculate_balance_sheet(df, assets_df, cutoff_date)
        
        pdf_balance = reports.generate_pdf_balance_sin(balance_data, f"Al {cutoff_date.strftime('%d/%m/%Y')}")
        
        # Calcular TAMBIÉN el Balance Real (con todos los gastos)
        balance_real_data = logic.calculate_balance_sheet_real(df, assets_df, cutoff_date)
        pdf_balance_real = reports.generate_pdf_balance_real(balance_real_data, f"Al {cutoff_date.strftime('%d/%m/%Y')}")
        
        c_bal1, c_bal2 = st.columns(2)
        with c_bal1:
            st.download_button(
                label="🏛️ Balance General (SIN - Solo Facturado)",
                data=pdf_balance,
                file_name=f"Balance_General_SIN_{cutoff_date.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                help="Formato oficial: Solo transacciones facturadas. Utilidad fiscal alta pero caja 'fantasma'.",
                key="btn_balance_sin"
            )
        
        with c_bal2:
            st.download_button(
                label="💰 Balance General (REAL - Gerencial)",
                data=pdf_balance_real,
                file_name=f"Balance_General_Real_{cutoff_date.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                help="Refleja caja REAL incluyendo gastos no deducibles. Recomendado para gestión interna.",
                key="btn_balance_real"
            )
            
        # --- REPORTE GERENCIAL COMPLETO ---
        pdf_gerencial = reports.generate_pdf_gerencial_completo(balance_data, mgr_data, f"Gestión 2025 (Al {cutoff_date})")
        with c_bal2:
            st.download_button(
                label="📈 Descargar Informe Gerencial Completo",
                data=pdf_gerencial,
                file_name=f"Informe_Gerencial_Estrategico_{cutoff_date.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                help="Informe de 5 páginas con KPIs, márgenes por proyecto y proyecciones.",
                key="btn_informe_gerencial_completo"
            )
        
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

        st.write("📚 **Libros Legales (Normativa)**")
        
        
        st.markdown("---")
        
        # --- PANEL FISCAL COMPLETO ---
        st.subheader("📋 Resumen Fiscal Anual")
        st.markdown("*Métricas acumuladas para planificación tributaria*")
        
        # IT Total Pagado (acumulado)
        it_total_pagado = breakdown['it_total']
        
        # IVA Neto a Pagar (Débito - Crédito)
        iva_neto = max(0, breakdown['iva_df'] - breakdown['iva_cf'])
        
        # IUE Estimado (25% sobre utilidades)
        # Base imponible = Ingresos Netos - Gastos Deducibles (con factura) - IT
        gastos_con_factura = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 1)]
        gastos_deducibles = 0
        for _, row in gastos_con_factura.iterrows():
            taxes = logic.calculate_taxes(row['monto'], row['tipo'], row['tiene_factura'], row['categoria'])
            gastos_deducibles += taxes['gasto_neto']
        
        utilidad_imponible = breakdown['net_income'] - gastos_deducibles - it_total_pagado
        iue_estimado = max(0, utilidad_imponible * 0.25)  # 25% IUE
        
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("💰 IT Total Pagado", f"Bs {it_total_pagado:,.2f}", help="Impuesto a las Transacciones acumulado (3%)")
        t2.metric("🏦 IVA Neto a Pagar", f"Bs {iva_neto:,.2f}", help="IVA Débito - IVA Crédito Fiscal")
        t3.metric("📊 Utilidad Imponible", f"Bs {utilidad_imponible:,.2f}", help="Base para cálculo de IUE")
        t4.metric("🔴 IUE Estimado (25%)", f"Bs {iue_estimado:,.2f}", 
                  delta=f"-{(gastos_deducibles/breakdown['net_income']*100):.1f}% por gastos no deducibles" if breakdown['net_income'] > 0 else "0%",
                  delta_color="inverse",
                  help="Impuesto a las Utilidades proyectado anual")
        
        # Explicación
        with st.expander("ℹ️ Ver Cálculo Detallado de IUE"):
            st.write(f"""
            **Fórmula del IUE:**
            - Ingresos Netos (87%): Bs {breakdown['net_income']:,.2f}
            - (-) Gastos Deducibles (con factura): Bs {gastos_deducibles:,.2f}
            - (-) IT Pagado (3%): Bs {it_total_pagado:,.2f}
            - **= Utilidad Imponible:** Bs {utilidad_imponible:,.2f}
            - **× 25% = IUE a Pagar:** Bs {iue_estimado:,.2f}
            
            ⚠️ **Importante:** Los gastos SIN factura ({breakdown['gastos_netos'] - gastos_deducibles:,.2f} Bs) NO son deducibles y aumentan tu IUE.
            """)

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
    1. Descarga la plantilla.
    2. Copia tus datos en las columnas correspondientes.
       - *Tipo*: Debe ser 'Ingreso' o 'Gasto'.
       - *Tiene_Factura*: 'Si' o 'No'.
    3. Sube el archivo completado.

    > **ℹ️ Categorías Especiales:**
    > * Si usas **"Aporte de Capital"**, el sistema NO calculará impuestos (IVA/IT).
    > * Si usas **"Pago de Impuestos"**, no buscará crédito fiscal.
    """)
    
    # 1. Download Template
    template_data = importer.generate_template()
    st.download_button(
        label="📥 Descargar Plantilla Excel",
        data=template_data,
        file_name="plantilla_importacion_warp6.xlsx",
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
            
            if st.button("Confirmar e Importar a Base de Datos"):
                count = 0
                progress_bar = st.progress(0)
                
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
                        row['tiene_factura']
                    )
                    count += 1
                    progress_bar.progress(count / len(df_preview))
                
                st.balloons()
                st.success(f"¡Éxito! Se importaron {count} transacciones.")
                st.info("Ve al menú 'Registro' o 'Reportes' para ver los datos.")

if __name__ == "__main__":
    main()
