import streamlit as st
import pandas as pd
import os
import hmac
from datetime import date
import database as db
import logic
import reports
import importer
import time
import altair as alt

# Configuración de página
st.set_page_config(
    page_title="WARP6 Accounting",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS Personalizados - Diseño Kombai
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
    @import url('https://cdn.jsdelivr.net/npm/@tabler/icons-webfont/tabler-icons.min.css');

    .main, .stApp {
        background-color: #F4F8FC !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
        color: #17324D !important;
    }

    .mono {
        font-family: 'IBM Plex Mono', monospace !important;
        font-variant-numeric: tabular-nums !important;
    }

    /* Kombai Alert Box */
    .w6-alert-box {
        display: flex;
        align-items: center;
        gap: 16px;
        background-color: #FFF1F0;
        border: 1px solid #EAC5C2;
        border-radius: 10px;
        padding: 14px 20px;
        margin-bottom: 22px;
    }
    .w6-alert-title {
        color: #8F2E28;
        font-weight: 600;
        font-size: 14px;
    }
    .w6-alert-sub {
        color: #9A5B55;
        font-size: 12.5px;
        margin-top: 2px;
    }

    /* Kombai KPIs Grid */
    .w6-kpi-grid {
        display: grid;
        grid-template-columns: 1.8fr 1fr 1fr 1fr;
        background: #FFFFFF;
        border: 1px solid #D7E2EC;
        border-radius: 10px;
        overflow: hidden;
        margin-bottom: 22px;
        box-shadow: 0 1px 3px rgba(23, 50, 77, 0.02);
    }
    @media (max-width: 950px) {
        .w6-kpi-grid {
            grid-template-columns: 1fr;
        }
    }
    .w6-kpi-col {
        padding: 18px 22px;
        border-right: 1px solid #E5EDF4;
        position: relative;
    }
    .w6-kpi-col:last-child {
        border-right: none;
    }
    .w6-kpi-label {
        font-size: 13px;
        font-weight: 500;
        color: #52677C;
    }
    .w6-kpi-val-main {
        font-size: 27px;
        font-weight: 600;
        color: #17324D;
        margin: 4px 0 2px 0;
        font-family: 'IBM Plex Mono', monospace;
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.02em;
    }
    .w6-kpi-val {
        font-size: 23px;
        font-weight: 600;
        color: #17324D;
        margin: 4px 0 2px 0;
        font-family: 'IBM Plex Mono', monospace;
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.02em;
    }
    .w6-kpi-sub {
        font-size: 12px;
        color: #52677C;
    }

    /* Kombai Exception Cards */
    .w6-exc-card {
        background: #FFFFFF;
        border: 1px solid #D7E2EC;
        border-radius: 10px;
        padding: 18px 22px;
        box-shadow: 0 1px 3px rgba(23, 50, 77, 0.02);
        height: 100%;
    }
    .w6-exc-header {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 14px;
        font-weight: 600;
        color: #17324D;
    }
    .w6-exc-dot-amber {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #B86B13;
        display: inline-block;
    }
    .w6-exc-dot-red {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #B5423C;
        display: inline-block;
    }
    .w6-exc-val-amber {
        font-size: 24px;
        font-weight: 600;
        color: #B86B13;
        margin: 4px 0 2px 0;
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: -0.02em;
    }
    .w6-exc-val-red {
        font-size: 24px;
        font-weight: 600;
        color: #B5423C;
        margin: 4px 0 2px 0;
        font-family: 'IBM Plex Mono', monospace;
        letter-spacing: -0.02em;
    }

    /* Kombai Table */
    .w6-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        background: #FFFFFF;
    }
    .w6-table th {
        padding: 12px 16px;
        font-weight: 500;
        color: #52677C;
        border-bottom: 1px solid #D7E2EC;
        background: #F8FAFC;
        font-size: 12px;
    }
    .w6-table td {
        padding: 11px 16px;
        border-bottom: 1px solid #E5EDF4;
        color: #17324D;
    }
    .w6-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 500;
    }
    .w6-badge-green {
        color: #16735A;
        background: rgba(22, 115, 90, 0.09);
    }
    .w6-badge-blue {
        color: #2B68E8;
        background: rgba(43, 104, 232, 0.08);
    }
    .w6-badge-red {
        color: #B5423C;
        background: #FFF1F0;
        font-weight: 600;
    }

    /* Section titles */
    .w6-section-title {
        font-size: 15px;
        font-weight: 600;
        color: #17324D;
        margin: 18px 0 10px 0;
    }

    /* General buttons */
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        height: 2.8em;
        background-color: #2B68E8;
        color: white;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

def fmt_bs(val):
    """Formatea importes numéricos al estilo contable (ej. 184.500,00)."""
    if val is None or pd.isna(val):
        return "0,00"
    return f"{float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Inicializar Base de Datos
db.init_db()

def check_password():
    timeout_minutes = 15 # 15 minutos de inactividad

    # Obtener credencial segura desde variables de entorno o secrets de Streamlit
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_password:
        try:
            if "ADMIN_PASSWORD" in st.secrets:
                admin_password = str(st.secrets["ADMIN_PASSWORD"])
        except Exception:
            pass
    if not admin_password:
        # Fallback de contingencia retrocompatible
        admin_password = "WARP6SOL"

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
        st.session_state["last_action_time"] = 0
        st.session_state["login_attempts"] = 0
        st.session_state["lockout_time"] = 0

    # Verificar si la sesión está temporalmente bloqueada por fuerza bruta
    current_time = time.time()
    if st.session_state.get("lockout_time", 0) > current_time:
        remaining = int(st.session_state["lockout_time"] - current_time)
        st.error(f"⛔ Demasiados intentos fallidos. Acceso bloqueado temporalmente por {remaining} segundos.")
        return False

    if st.session_state["authenticated"]:
        if time.time() - st.session_state["last_action_time"] > timeout_minutes * 60:
            st.session_state["authenticated"] = False
            st.error("⚠️ Sesión expirada por inactividad. Por favor, inicia sesión de nuevo.")
        else:
            st.session_state["last_action_time"] = time.time()
            return True

    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<h2 style='text-align: center;'>🔒 Acceso Seguro - WARP6</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Por favor ingresa la contraseña de administrador para continuar.</p>", unsafe_allow_html=True)
        pwd = st.text_input("Contraseña", type="password", label_visibility="collapsed", placeholder="Contraseña de Administrador")
        if st.button("Iniciar Sesión"):
            if pwd and hmac.compare_digest(str(pwd), str(admin_password)):
                st.session_state["authenticated"] = True
                st.session_state["last_action_time"] = time.time()
                st.session_state["login_attempts"] = 0
                st.session_state["lockout_time"] = 0
                try:
                    st.rerun()
                except AttributeError:
                    st.experimental_rerun()
            else:
                st.session_state["login_attempts"] = st.session_state.get("login_attempts", 0) + 1
                time.sleep(1) # Penalización de tiempo contra ataques automatizados
                if st.session_state["login_attempts"] >= 5:
                    st.session_state["lockout_time"] = time.time() + 300 # 5 minutos de bloqueo
                    st.error("❌ Has superado el límite de 5 intentos fallidos. Sistema bloqueado temporalmente por 5 minutos.")
                else:
                    restantes = 5 - st.session_state["login_attempts"]
                    st.error(f"❌ Contraseña incorrecta. Intentos restantes antes del bloqueo: {restantes}")
            
    return False

def main():
    if not check_password():
        return

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
    # Encabezado estilo Kombai
    st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
        <h1 style="font-size: 22px; font-weight: 700; color: #17324D; margin: 0;">Inicio</h1>
    </div>
    """, unsafe_allow_html=True)
    
    df = db.get_transactions()
    if df.empty:
        st.info("No hay datos suficientes para mostrar el dashboard.")
        return

    # --- FILTROS DE DASHBOARD ---
    df['fecha_dt'] = pd.to_datetime(df['fecha'])
    
    # Pre-seleccionar este año fiscal por defecto
    current_year = date.today().year
    min_date_val = date(current_year, 1, 1) if not df.empty else date.today()
    max_date_val = df['fecha_dt'].max().date() if not pd.isna(df['fecha_dt'].max()) else date.today()
    min_date_val = min(min_date_val, max_date_val)
    
    if 'proyecto' not in df.columns:
        df['proyecto'] = 'General'
        
    proyectos_disponibles = df['proyecto'].dropna().unique().tolist()
    proyectos_disponibles.insert(0, "Todos")

    # Contenedor de controles de filtrado
    col_d1, col_d2, col_d3 = st.columns([1.5, 1.2, 1.3])
    with col_d1:
        date_range = st.date_input(
            "📅 Rango de Fechas:",
            value=(min_date_val, max_date_val),
            min_value=df['fecha_dt'].min().date() if not pd.isna(df['fecha_dt'].min()) else date.today(),
            max_value=max(max_date_val, date.today()),
            key="dash_date_range"
        )
    with col_d2:
        proyecto_seleccionado = st.selectbox("🏗️ Filtrar por Proyecto", options=proyectos_disponibles, index=0, key="dash_proj_sel")
        
    with col_d3:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        excluir_externos = st.checkbox("💼 Excluir gastos externos", value=False, help="Ignora facturas ajenas en los KPIs y gráficas del Dashboard", key="dash_excl_ext")
        
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0]
        
    df = df[(df['fecha_dt'] >= pd.to_datetime(start_date)) & (df['fecha_dt'] <= pd.to_datetime(end_date))]
    
    if proyecto_seleccionado != "Todos":
        df = df[df['proyecto'] == proyecto_seleccionado]
    
    if df.empty:
        st.info("No hay datos para los filtros seleccionados.")
        return

    if excluir_externos:
        mask_exc = (df['tipo'] == 'Gasto') & df['categoria'].str.lower().str.contains('externo', na=False)
        df = df[~mask_exc]

    gastos = df[df['tipo'] == 'Gasto'].copy()
    
    # Separar Ingresos Operativos (Ventas) de Aportes de Capital
    ingresos_totales_raw = df[df['tipo'] == 'Ingreso'].copy()
    
    # Identificar Aportes de Capital (No son Ventas)
    is_aporte = ingresos_totales_raw['categoria'].str.lower().str.contains('aporte', na=False) & \
                ingresos_totales_raw['categoria'].str.lower().str.contains('capital', na=False)
                
    ingresos = ingresos_totales_raw[~is_aporte] # Solo ventas reales
    aportes_capital = ingresos_totales_raw[is_aporte]

    # --- Cálculos Base para KPIs ---
    total_ventas = ingresos['monto'].sum()
    total_aportes = aportes_capital['monto'].sum()
    total_gastos = gastos['monto'].sum()
    
    # Calculo de Crédito Fiscal Perdido (excluir pagos de impuestos ya que nunca dan factura)
    is_tax_payment = gastos['categoria'].str.lower().str.contains('impuesto|tributo', na=False, regex=True)
    gastos_sin_factura = gastos[(gastos['tiene_factura'] == 0) & (~is_tax_payment)]
    gastos_no_deducibles = gastos_sin_factura['monto'].sum()
    cf_perdido = gastos_sin_factura['monto'].sum() * 0.13
    
    # Cálculos Tributarios Directos
    iva_df_total = total_ventas * logic.IVA_RATE
    
    # IT Pagado real (buscando transacciones de pago)
    it_pagado_total = 0
    for _, row in gastos.iterrows():
        det = str(row['detalle']).lower()
        cat = str(row['categoria']).lower()
        if ('pago' in det or 'impuesto' in cat or 'tributo' in cat) and ('it' in det or '400' in det):
            it_pagado_total += row['monto']

    # Resumen fiscal mensual para alerta y calendario
    tax_summary = logic.get_monthly_tax_summary(df.copy())
    
    # --- ALERTA FISCAL (Estilo Kombai) ---
    if tax_summary:
        monthly_data_check = []
        for mes_k, vals_k in tax_summary.items():
            dif_k = vals_k['total_determinado'] - vals_k['total_pagado']
            monthly_data_check.append({'Mes': mes_k, 'Diferencia': dif_k})
        df_debts = pd.DataFrame(monthly_data_check)
        deudores = df_debts[df_debts['Diferencia'] > 100]
        if not deudores.empty:
            mes_peor = deudores.sort_values('Diferencia', ascending=False).iloc[0]
            st.markdown(f"""
            <div class="w6-alert-box">
                <i class="ti ti-triangle-alert" style="font-size: 22px; color: #B5423C; flex-shrink: 0;"></i>
                <div style="flex: 1; min-width: 0;">
                    <div class="w6-alert-title">
                        Pendiente fiscal en {mes_peor['Mes']}: 
                        <span class="mono" style="font-weight: 600;">Bs {fmt_bs(mes_peor['Diferencia'])}</span>
                    </div>
                    <div class="w6-alert-sub">
                        IVA e IT determinados superan los pagos registrados. Se recomienda regularizar antes del cierre mensual.
                    </div>
                </div>
                <div style="color: #B5423C; font-weight: 600; font-size: 13px; white-space: nowrap;">
                    Ver calendario fiscal abajo ↓
                </div>
            </div>
            """, unsafe_allow_html=True)

    # --- RESUMEN OPERATIVO Y FISCAL (KPIs Kombai) ---
    st.markdown('<div class="w6-section-title">Resumen operativo y fiscal</div>', unsafe_allow_html=True)
    
    aportes_html = f'Aportes registrados: <span class="mono" style="font-weight: 600; color: #2B68E8;">Bs {fmt_bs(total_aportes)}</span>' if total_aportes > 0 else 'Total facturado del período'
    
    st.markdown(f"""
    <div class="w6-kpi-grid">
        <div class="w6-kpi-col" style="grid-column: span 1.5; padding-bottom: 28px;">
            <div class="w6-kpi-label">Ventas</div>
            <div class="w6-kpi-val-main">Bs {fmt_bs(total_ventas)}</div>
            <div class="w6-kpi-sub">{aportes_html}</div>
            <svg preserveAspectRatio="none" viewBox="0 0 460 44" style="position: absolute; bottom: 0; left: 0; right: 0; width: 100%; height: 38px; pointer-events: none;">
                <path d="M0,38 L42,34 L84,36 L126,29 L168,31 L210,24 L252,26 L294,19 L336,21 L378,13 L420,15 L460,6 L460,44 L0,44 Z" fill="rgba(43,104,232,0.06)"></path>
                <path d="M0,38 L42,34 L84,36 L126,29 L168,31 L210,24 L252,26 L294,19 L336,21 L378,13 L420,15 L460,6" fill="none" stroke="rgba(43,104,232,0.35)" stroke-width="1.5"></path>
            </svg>
        </div>
        <div class="w6-kpi-col">
            <div class="w6-kpi-label">Gastos</div>
            <div class="w6-kpi-val">Bs {fmt_bs(total_gastos)}</div>
            <div class="w6-kpi-sub">{len(gastos)} movimientos</div>
        </div>
        <div class="w6-kpi-col">
            <div class="w6-kpi-label">IVA generado (13%)</div>
            <div class="w6-kpi-val">Bs {fmt_bs(iva_df_total)}</div>
            <div class="w6-kpi-sub">Débito fiscal del período</div>
        </div>
        <div class="w6-kpi-col">
            <div class="w6-kpi-label">IT pagado</div>
            <div class="w6-kpi-val">Bs {fmt_bs(it_pagado_total)}</div>
            <div class="w6-kpi-sub" style="color: #16735A; display: flex; align-items: center; gap: 4px; font-weight: 500;">
                <i class="ti ti-badge-check text-[13px]"></i> Form. 400 registrado
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- ZONA DE EXCEPCIÓN ---
    col_exc1, col_exc2 = st.columns(2)
    with col_exc1:
        st.markdown(f"""
        <div class="w6-exc-card">
            <div class="w6-exc-header">
                <span class="w6-exc-dot-amber"></span>
                Gastos sin factura
            </div>
            <div class="w6-exc-val-amber">Bs {fmt_bs(gastos_no_deducibles)}</div>
            <div class="w6-kpi-sub">{len(gastos_sin_factura)} movimientos afectados · No reducen la base imponible</div>
        </div>
        """, unsafe_allow_html=True)

    with col_exc2:
        st.markdown(f"""
        <div class="w6-exc-card">
            <div class="w6-exc-header">
                <span class="w6-exc-dot-red"></span>
                Crédito fiscal perdido
            </div>
            <div class="w6-exc-val-red">Bs {fmt_bs(cf_perdido)}</div>
            <div class="w6-kpi-sub">13% sobre compras sin respaldo · IVA no aprovechable</div>
        </div>
        """, unsafe_allow_html=True)

    # --- GRÁFICOS ---
    st.markdown('<div class="w6-section-title" style="margin-top: 24px;">Análisis gráfico</div>', unsafe_allow_html=True)
    cg1, cg2 = st.columns([5, 7])

    with cg1:
        st.markdown('<div style="font-size: 13.5px; font-weight: 600; color: #17324D; margin-bottom: 8px;">Gastos por categoría</div>', unsafe_allow_html=True)
        if not gastos.empty:
            gastos_cat = gastos.groupby('categoria')['monto'].sum().reset_index()
            gastos_cat = gastos_cat.sort_values(by='monto', ascending=False).head(7)
            chart_cat = alt.Chart(gastos_cat).mark_bar(cornerRadius=2, size=16).encode(
                x=alt.X('monto:Q', title='Monto (Bs)', axis=alt.Axis(format=',.0f', gridColor='#EDF2F7', labelColor='#52677C')),
                y=alt.Y('categoria:N', sort='-x', title=None, axis=alt.Axis(labelColor='#17324D', labelFontSize=12)),
                color=alt.Color('monto:Q', scale=alt.Scale(range=['#6A95F0', '#2B68E8']), legend=None),
                tooltip=[alt.Tooltip('categoria:N', title='Categoría'), alt.Tooltip('monto:Q', title='Monto (Bs)', format=',.2f')]
            ).properties(height=280).configure_view(strokeWidth=0)
            st.altair_chart(chart_cat, use_container_width=True)
        else:
            st.info("Sin gastos registrados")

    with cg2:
        st.markdown('<div style="font-size: 13.5px; font-weight: 600; color: #17324D; margin-bottom: 8px;">Ingresos y gastos por mes</div>', unsafe_allow_html=True)
        if not df.empty:
            df_time = df.copy()
            df_time['periodo_sort'] = df_time['fecha_dt'].dt.to_period('M')
            df_time['periodo'] = df_time['fecha_dt'].dt.strftime('%b %Y')
            time_grouped = df_time.groupby(['periodo_sort', 'periodo', 'tipo'])['monto'].sum().reset_index()
            time_grouped = time_grouped.sort_values(by='periodo_sort')
            chart_time = alt.Chart(time_grouped).mark_area(
                opacity=0.18,
                line={'strokeWidth': 2},
                point=alt.OverlayMarkDef(filled=True, size=35)
            ).encode(
                x=alt.X('periodo:N', sort=alt.SortField('periodo_sort'), title=None, axis=alt.Axis(labelColor='#52677C', grid=False)),
                y=alt.Y('monto:Q', title='Bs', axis=alt.Axis(format=',.0f', gridColor='#EDF2F7', labelColor='#52677C')),
                color=alt.Color('tipo:N', scale=alt.Scale(domain=['Ingreso', 'Gasto'], range=['#2B68E8', '#64748B']), title=None),
                tooltip=[alt.Tooltip('periodo:N', title='Mes'), alt.Tooltip('tipo:N', title='Tipo'), alt.Tooltip('monto:Q', title='Monto (Bs)', format=',.2f')]
            ).properties(height=280).configure_view(strokeWidth=0).configure_legend(orient='top', labelColor='#52677C')
            st.altair_chart(chart_time, use_container_width=True)
        else:
            st.info("Sin datos para graficar")

    # --- CALENDARIO FISCAL MENSUAL ---
    st.markdown("""
    <div style="margin-top: 24px; margin-bottom: 12px;">
        <div class="w6-section-title" style="margin-bottom: 2px;">Calendario fiscal</div>
        <div style="font-size: 12.5px; color: #52677C;">Impuesto determinado y pagos registrados por mes.</div>
    </div>
    """, unsafe_allow_html=True)

    if not tax_summary:
        st.info("No hay datos suficientes para generar el calendario fiscal.")
    else:
        table_rows = []
        for mes, vals in tax_summary.items():
            iva_det = vals['iva_determinado']
            iva_pag = vals['iva_pagado']
            it_det = vals['it_determinado']
            it_pag = vals['it_pagado']
            tot_det = vals['total_determinado']
            tot_pag = vals['total_pagado']
            dif = tot_det - tot_pag
            
            if dif > 10:
                status_pill = '<span class="w6-badge w6-badge-red"><span style="width:6px;height:6px;border-radius:50%;background:#B5423C;display:inline-block;"></span> Pendiente</span>'
                row_bg = 'background-color: #FFF1F0;'
                dif_style = 'color: #B5423C; font-weight: 600;'
            elif dif < -10:
                status_pill = '<span class="w6-badge w6-badge-blue"><span style="width:6px;height:6px;border-radius:50%;background:#2B68E8;display:inline-block;"></span> Pago en exceso</span>'
                row_bg = ''
                dif_style = 'color: #2B68E8;'
            else:
                status_pill = '<span class="w6-badge w6-badge-green"><span style="width:6px;height:6px;border-radius:50%;background:#16735A;display:inline-block;"></span> Al día</span>'
                row_bg = ''
                dif_style = 'color: #52677C;'
                
            table_rows.append(f"""
            <tr style="{row_bg}">
                <td style="font-weight: 500; color: #17324D;">{mes}</td>
                <td class="mono" style="text-align: right;">{fmt_bs(iva_det)}</td>
                <td class="mono" style="text-align: right;">{fmt_bs(iva_pag)}</td>
                <td class="mono" style="text-align: right;">{fmt_bs(it_det)}</td>
                <td class="mono" style="text-align: right;">{fmt_bs(it_pag)}</td>
                <td class="mono" style="text-align: right; {dif_style}">{fmt_bs(dif)}</td>
                <td style="padding-left: 20px;">{status_pill}</td>
            </tr>
            """)
            
        table_html = f"""
        <div style="border: 1px solid #D7E2EC; border-radius: 10px; overflow-x: auto; background: #FFFFFF; box-shadow: 0 1px 3px rgba(23, 50, 77, 0.02);">
            <table class="w6-table" style="width: 100%; border-collapse: collapse; font-size: 13px;">
                <thead>
                    <tr style="border-bottom: 1px solid #D7E2EC; color: #52677C; background: #F8FAFC;">
                        <th style="text-align: left; padding: 12px 16px; font-weight: 500;">Mes</th>
                        <th style="text-align: right; padding: 12px 16px; font-weight: 500;">IVA adeudado</th>
                        <th style="text-align: right; padding: 12px 16px; font-weight: 500;">IVA pagado</th>
                        <th style="text-align: right; padding: 12px 16px; font-weight: 500;">IT adeudado</th>
                        <th style="text-align: right; padding: 12px 16px; font-weight: 500;">IT pagado</th>
                        <th style="text-align: right; padding: 12px 16px; font-weight: 500;">Diferencia</th>
                        <th style="text-align: left; padding: 12px 16px; padding-left: 20px; font-weight: 500;">Estado</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>
        <div style="font-size: 12px; color: #52677C; margin-top: 8px;">
            Importes en bolivianos (Bs). Diferencia = determinado − pagado.
        </div>
        """
        st.markdown(table_html, unsafe_allow_html=True)
        
    st.markdown("""
    <div style="padding-top: 24px; font-size: 12px; color: #52677C;">
        Sistema Contable v1.2 · WARP6 Solutions S.R.L.
    </div>
    """, unsafe_allow_html=True)

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
        
        date_range = st.date_input(
            "Rango de Fechas para Reportes:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max(max_date, date.today()),
            help="Selecciona la fecha de inicio y fin para los reportes. Deja ambos campos iguales para un solo día."
        )
    
    with col_info:
        if len(date_range) == 2:
            start_date, end_date = date_range
            st.info(f"📊 Generando reportes **del {start_date.strftime('%d/%m/%Y')} al {end_date.strftime('%d/%m/%Y')}**")
        else:
            # If user hasn't selected the second date yet, use the first one for both
            start_date = date_range[0]
            end_date = date_range[0]
            st.info(f"📊 Seleccionando fecha de fin...")
            
    # Filter transactions by date range
    df_unfiltered = df.copy()
    df = df[(df['fecha_dt'] >= pd.to_datetime(start_date)) & (df['fecha_dt'] <= pd.to_datetime(end_date))]
    # Keep historical transactions up to end_date for Balance Sheet & Cash
    df_historical = df_unfiltered[df_unfiltered['fecha_dt'] <= pd.to_datetime(end_date)]
    
    if df.empty and df_historical.empty:
        st.warning(f"No hay transacciones registradas hasta la fecha seleccionada.")
        return
    
    st.markdown("---")

    # --- UFV Y AITB ---
    st.markdown("### 📈 Ajuste por Inflación (AITB)")
    st.info("Ingresa las UFVs para calcular el Ajuste por Inflación y Tenencia de Bienes de los Activos Fijos y Patrimonio.")
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        ufv_inicial = st.number_input("UFV Inicial (Ej. 1 de Enero)", min_value=1.0, value=2.50000, step=0.00001, format="%.5f")
    with col_u2:
        ufv_final = st.number_input("UFV Final (Fecha de Cierre)", min_value=1.0, value=2.50000, step=0.00001, format="%.5f")
        
    ufv_ratio = ufv_final / ufv_inicial if ufv_inicial > 0 else 1.0

    st.markdown("---")
    
    # --- FILTRO GERENCIAL ---
    st.markdown("### 💼 Filtro Gerencial de Favores")
    excluir_externos = st.checkbox("Excluir 'Gastos Externos/Favores' del Análisis Gerencial", value=False, help="Ignora facturas ajenas para mostrar tu rentabilidad y liquidez real. El 13% generado por estas facturas se mostrará como Ahorro Fiscal.")
    
    st.markdown("---")

    # --- PESTAÑAS DE REPORTES ---
    tab1, tab2 = st.tabs(["Resumen Financiero", "Analítica Avanzada (Excel Superpoderes)"])

    with tab2:
        st.subheader("🔍 Explorador Dinámico de Transacciones")
        st.info("Utiliza los filtros de abajo para segmentar tus datos exactamente como necesitas. El total sumará solo las filas visibles.")
        
        df_exp = df.copy()
        if 'proyecto' not in df_exp.columns:
            df_exp['proyecto'] = 'General'
            
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            proy_list = ["Todos"] + df_exp['proyecto'].dropna().unique().tolist()
            sel_proy = st.selectbox("🏗️ Filtrar por Proyecto", proy_list, key="rep_proy")
            
        with col_f2:
            sel_tipo = st.selectbox("🔄 Filtrar por Tipo", ["Todos", "Ingreso", "Gasto"], key="rep_tipo")
            
        with col_f3:
            factura_filt = st.radio("📄 Filtro de Factura", ["Ambos", "Solo Con Factura", "Solo Sin Factura"])

        if sel_proy != "Todos":
            df_exp = df_exp[df_exp['proyecto'] == sel_proy]
        if sel_tipo != "Todos":
            df_exp = df_exp[df_exp['tipo'] == sel_tipo]
        if factura_filt == "Solo Con Factura":
            df_exp = df_exp[df_exp['tiene_factura'] == 1]
        elif factura_filt == "Solo Sin Factura":
            df_exp = df_exp[df_exp['tiene_factura'] == 0]
            
        cat_list = ["Todas"] + df_exp['categoria'].dropna().unique().tolist()
        sel_cat = st.selectbox("🏷️ Filtrar por Categoría", cat_list, help="Las categorías disponibles se actualizan según el proyecto elegido.")
        if sel_cat != "Todas":
            df_exp = df_exp[df_exp['categoria'] == sel_cat]
            
        st.markdown("---")
        
        st.metric(f"💰 SUMA TOTAL FILTRADA ({len(df_exp)} registros)", f"Bs {df_exp['monto'].sum():,.2f}")
        
        cols_to_show = ['fecha', 'proyecto', 'tipo', 'categoria', 'detalle', 'monto', 'n_factura', 'metodo_pago', 'tiene_factura', 'aplica_retencion']
        cols_avail = [c for c in cols_to_show if c in df_exp.columns]
        
        # Format some display properties gracefully
        display_df = df_exp[cols_avail].copy()
        if 'fecha' in display_df.columns:
            display_df['fecha'] = pd.to_datetime(display_df['fecha']).dt.strftime('%d/%m/%Y')
        if 'tiene_factura' in display_df.columns:
            display_df['tiene_factura'] = display_df['tiene_factura'].apply(lambda x: 'Sí' if x == 1 else 'No')
        if 'aplica_retencion' in display_df.columns:
            display_df['aplica_retencion'] = display_df['aplica_retencion'].apply(lambda x: 'Sí' if x == 1 else 'No')
            
        st.dataframe(display_df, use_container_width=True)

        st.markdown("---")
        
        # --- MINI ESTADO DE RESULTADOS POR PROYECTO/FILTRO ---
        st.subheader("📊 Análisis de Rentabilidad Real (P&L del Filtro Activo)")
        st.caption("Calcula si estas transacciones filtradas generaron ganancias o pérdidas, descontando automáticamente el IVA (DF/CF) y el IT correspondientes a la ley boliviana, simulando el comportamiento contable exacto.")
        
        mini_ingresos_raw = df_exp[df_exp['tipo'] == 'Ingreso'].copy()
        is_aporte_exp = mini_ingresos_raw['categoria'].str.lower().str.contains('aporte', na=False) & \
                        mini_ingresos_raw['categoria'].str.lower().str.contains('capital', na=False)
        mini_ingresos = mini_ingresos_raw[~is_aporte_exp]
        
        mini_gastos = df_exp[df_exp['tipo'] == 'Gasto'].copy()
        
        brk = {
            'ingreso_bruto': mini_ingresos['monto'].sum(),
            'gasto_bruto': mini_gastos['monto'].sum(),
            'iva_df': 0, 'it': 0, 'ingreso_neto': 0,
            'iva_cf': 0, 'gasto_neto': 0
        }
        
        for _, r in mini_ingresos.iterrows():
            tx = logic.calculate_taxes(r['monto'], r['tipo'], r['tiene_factura'] == 1, str(r['categoria']))
            brk['iva_df'] += tx.get('iva_df', 0)
            brk['it'] += tx.get('it', 0)
            brk['ingreso_neto'] += tx.get('ingreso_neto', 0)
            
        for _, r in mini_gastos.iterrows():
            clas = logic.classify_account(str(r['categoria']))
            if clas == 'Excluir P&L (Pago Pasivo)' or 'impuesto' in str(r['categoria']).lower() or 'tributo' in str(r['categoria']).lower(): 
                continue
            ar = r.get('aplica_retencion', 0) == 1
            tx = logic.calculate_taxes(r['monto'], r['tipo'], r['tiene_factura'] == 1, str(r['categoria']), aplica_retencion=ar)
            brk['iva_cf'] += tx.get('iva_cf', 0)
            brk['gasto_neto'] += tx.get('gasto_neto', 0)
            
        utilidad_filtro = brk['ingreso_neto'] - brk['gasto_neto'] - brk['it']
        
        c_pnl1, c_pnl2, c_pnl3, c_pnl4 = st.columns(4)
        c_pnl1.metric("Ingresos Netos (Sin IVA DF)", f"Bs {brk['ingreso_neto']:,.2f}", help="Ventas reales quitando el 13% que se va al fisco.")
        c_pnl2.metric("Costos Netos (Descontando CF/Ret)", f"Bs {brk['gasto_neto']:,.2f}", help="Costo real de los materiales/servicios descontando el IVA a tu favor.")
        c_pnl3.metric("Impuestos (IT pagado)", f"Bs {brk['it']:,.2f}", help="El 3% de Impuesto a las Transacciones.")
        c_pnl4.metric("💰 UTILIDAD REAL DEL FILTRO", f"Bs {utilidad_filtro:,.2f}", 
                  delta="Ganancia/Aporte neto" if utilidad_filtro >= 0 else "Pérdida/Fuga de capital", 
                  delta_color="normal" if utilidad_filtro >= 0 else "inverse")
        
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
        depreciacion_periodo = logic.calculate_period_depreciation(assets_df, 12, ufv_ratio)

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
        monthly_dep = logic.calculate_period_depreciation(assets_df, 12, ufv_ratio)
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
            'otros_ingresos': {'total': 0, 'items': []},
            'otros_gastos': {'total': 0, 'items': []},
            'kpis': {}
        }
        
        dep_items = []
        for _, asset in assets_df.iterrows():
             valor_actualizado = asset['valor_inicial'] * ufv_ratio
             annual_dep = valor_actualizado / asset['vida_util_anios']
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
        
        # AITB Calculation
        valor_activos_historico = assets_df['valor_inicial'].sum() if not assets_df.empty else 0
        aitb_activos = valor_activos_historico * (ufv_ratio - 1)
        is_aporte_local = df['categoria'].str.lower().str.contains('aporte', na=False) & \
                    df['categoria'].str.lower().str.contains('capital', na=False)
        total_aportes_historico = df[is_aporte_local]['monto'].sum()
        aitb_capital = total_aportes_historico * (ufv_ratio - 1)
        aitb_neto = aitb_activos - aitb_capital
        
        if aitb_neto > 0:
            legal_detailed_data['otros_ingresos']['total'] += aitb_neto
            legal_detailed_data['otros_ingresos']['items'].append({'fecha': '-', 'detalle': 'Ajuste por Inflación y Tenencia de Bienes (AITB)', 'monto': aitb_neto})
        elif aitb_neto < 0:
            legal_detailed_data['otros_gastos']['total'] += abs(aitb_neto)
            legal_detailed_data['otros_gastos']['items'].append({'fecha': '-', 'detalle': 'Ajuste por Inflación y Tenencia de Bienes (AITB)', 'monto': abs(aitb_neto)})
            
        uai = (legal_detailed_data['kpis']['bait'] - deducible_financieros - deducible_impuestos) + aitb_neto
        legal_detailed_data['kpis']['utilidad_antes_iue'] = uai
        legal_detailed_data['kpis']['iue'] = max(0, legal_detailed_data['kpis']['utilidad_antes_iue'] * 0.25)
        legal_detailed_data['kpis']['utilidad_neta'] = legal_detailed_data['kpis']['utilidad_antes_iue'] - legal_detailed_data['kpis']['iue']
        
        if legal_detailed_data['kpis']['utilidad_neta'] > 0:
            legal_detailed_data['kpis']['reserva_legal'] = legal_detailed_data['kpis']['utilidad_neta'] * 0.05
        else:
            legal_detailed_data['kpis']['reserva_legal'] = 0.0
        legal_detailed_data['kpis']['utilidad_liquida'] = legal_detailed_data['kpis']['utilidad_neta'] - legal_detailed_data['kpis']['reserva_legal']
        
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
                 # Allow Tax payments for Cash Basis Managerial Report (like monthly IVA/IT)
                 cat_str = row['categoria'].lower()
                 det_str = row['detalle'].lower()
                 
                 # NEVER include IUE payments in P&L, it's a liability payment from the previous year
                 if "iue" in cat_str or "iue" in det_str:
                     continue
                     
                 if "pago" in cat_str and ("impuesto" in cat_str or "iva" in cat_str or "it" in cat_str):
                      mgr_data['impuestos']['total'] += expense_amount
                      mgr_data['impuestos']['items'].append(item_dict)
                      continue
                 else:
                      continue

            # Omitir Gastos Externos si el filtro está activado
            if excluir_externos and 'externo' in row['categoria'].lower():
                 if row['tiene_factura'] == 1:
                      taxes = logic.calculate_taxes(row['monto'], row['tipo'], True, row['categoria'])
                      iva_ahorro = taxes.get('iva_cf', 0)
                      if iva_ahorro > 0:
                           mgr_data['ingresos']['total'] += iva_ahorro
                           mgr_data['ingresos']['items'].append({'fecha': str(row['fecha']), 'detalle': f"Ahorro Fiscal 13% por Favor ({row['detalle']})", 'monto': iva_ahorro})
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
        
        if mgr_data['kpis']['utilidad_neta'] > 0:
            mgr_data['kpis']['reserva_legal'] = mgr_data['kpis']['utilidad_neta'] * 0.05
        else:
            mgr_data['kpis']['reserva_legal'] = 0.0
        mgr_data['kpis']['utilidad_liquida'] = mgr_data['kpis']['utilidad_neta'] - mgr_data['kpis']['reserva_legal']
        
        pdf_mgr_detailed = reports.generate_pdf_managerial_detailed(mgr_data, "Acumulado Anual")
        
        # D. Balance Sheets
        balance_data = logic.calculate_balance_sheet(df_historical, assets_df, date_range=None, ufv_ratio=ufv_ratio)
        balance_real_data = logic.calculate_balance_sheet_real(df_historical, assets_df, date_range=None, ufv_ratio=ufv_ratio, excluir_externos=excluir_externos)
        
        date_str = f"Al {end_date.strftime('%d/%m/%Y')}"
        pdf_balance_sin = reports.generate_pdf_balance_sin(balance_data, date_str)
        pdf_balance_real = reports.generate_pdf_balance_real(balance_real_data, date_str)
        
        # E. Gerencial Completo
        pdf_gerencial_completo = reports.generate_pdf_gerencial_completo(balance_data, mgr_data, date_str)
        
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
                file_name=f"Balance_General_SIN_{end_date.strftime('%Y%m%d')}.pdf",
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
                file_name=f"Balance_General_Real_{end_date.strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                help="Refleja caja real y gastos no deducibles",
                key="btn_balance_real"
            )
            
            # 3. Informe Completo
            st.download_button(
                label="📈 Informe Gerencial Completo",
                data=pdf_gerencial_completo,
                file_name=f"Informe_Gerencial_{end_date.strftime('%Y%m%d')}.pdf",
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
        ingresos_efectivo = df_historical[(df_historical['tipo'] == 'Ingreso') & 
                               (~df_historical['categoria'].str.lower().str.contains('activo', na=False))]['monto'].sum()
        
        total_outflow = 0
        pagos_impuestos_realizados = 0
        for _, row in df_historical[df_historical['tipo'] == 'Gasto'].iterrows():
             if excluir_externos and 'externo' in str(row['categoria']).lower():
                 continue
                 
             total_outflow += row['monto']
             
             if "impuesto" in row['categoria'].lower() or "it" in row['categoria'].lower():
                 pagos_impuestos_realizados += row['monto']

        caja_operativa_bruta = ingresos_efectivo - total_outflow
        
        # 2. Impuestos LEGALES Por Pagar (Acumulados Históricamente)
        # IUE total pendiente de pago registrado en el pasivo del Balance
        iue_a_pagar = balance_data['pasivos']['corriente']['iue_por_pagar']
        
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
        
        # Usar la nueva lógica centralizada de resúmenes fiscales mensuales (desde el inicio para arrastrar saldo)
        tax_summary = logic.get_monthly_tax_summary(df_historical)
        
        if not tax_summary:
            st.info("No hay datos suficientes para mostrar el calendario mensual.")
        else:
            monthly_data = []
            for mes, vals in tax_summary.items():
                monthly_data.append({
                    'Mes': mes,
                    'Saldo Favor IVA': vals['saldo_favor_iva'],
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
                        st.rerun()
            
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
    
    # --- BOTÓN DE LIMPIAR BASE DE DATOS ---
    st.markdown("---")
    st.markdown("### 🗑️ Limpiar Base de Datos de Transacciones")
    st.caption("Usa este botón si quieres borrar todas las transacciones antes de importar una plantilla actualizada. **Los Activos Fijos NO se borran.**")
    
    col_clear1, col_clear2 = st.columns([1, 2])
    with col_clear1:
        # Checkbox de confirmación para evitar borrado accidental
        confirmar_borrado = st.checkbox("✅ Confirmo que quiero borrar todas las transacciones", key="confirm_clear_db")
    
    with col_clear2:
        if confirmar_borrado:
            if st.button("🗑️ Borrar Todas las Transacciones", type="primary", key="btn_clear_db"):
                db.clear_all_transactions()
                st.success("✅ ¡Base de datos de transacciones limpiada! (Se guardó un respaldo automático en /backups). Los Activos Fijos se mantienen intactos.")
                st.balloons()
        else:
            st.button("🗑️ Borrar Todas las Transacciones", disabled=True, key="btn_clear_db_disabled", help="Marca la casilla de confirmación primero")
    
    st.markdown("---")
    
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
                        row['aplica_retencion'],
                        row.get('proyecto', 'General')
                    )
                    count += 1
                    progress_bar.progress(count / len(df_preview))
                
                st.balloons()
                st.success(f"¡Éxito! Se importaron {count} transacciones.")
                st.info("Ve al menú 'Registro' o 'Reportes' para ver los datos.")

if __name__ == "__main__":
    main()
