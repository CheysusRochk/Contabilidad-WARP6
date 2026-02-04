import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

def generate_excel_rcv(df):
    """Genera archivo Excel con formato RCV (Registro Compras/Ventas)."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transacciones')
    return output.getvalue()

def _add_header(elements, title, subtitle="WARP6 SOLUTIONS S.R.L."):
    styles = getSampleStyleSheet()
    # Logo placeholder or Title
    elements.append(Paragraph(subtitle, styles['Heading2']))
    elements.append(Paragraph("NIT: 000000000", styles['Normal'])) # Placeholder NIT
    elements.append(Paragraph("La Paz - Bolivia", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    elements.append(Paragraph(title, styles['Heading1']))
    elements.append(Spacer(1, 0.2*inch))

def _add_signatures(elements):
    """Agrega pie de firmas."""
    elements.append(Spacer(1, 0.8*inch))
    data = [
        ["_________________________", "_________________________"],
        ["Contador General", "Representante Legal"],
        ["Mat. Prof. Nº ......", "C.I. ............"]
    ]
    t = Table(data, colWidths=[3.5*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    elements.append(t)

def generate_pdf_libro_diario(df):
    """Genera PDF del Libro Diario Detallado."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    _add_header(elements, f"LIBRO DIARIO (Al {datetime.now().strftime('%d/%m/%Y')})")
    
    # We use a finer table structure:
    # Fecha | Cod | Detalle / Glosa | Debe | Haber
    data = [["Fecha", "Detalle / Asiento", "Debe (Bs)", "Haber (Bs)"]]
    
    total_debe = 0
    total_haber = 0
    num_asiento = 1
    
    # Sort by Date
    df = df.sort_values(by="fecha")
    
    for _, row in df.iterrows():
        # Generar Asiento Contable Simplificado
        fecha = str(row['fecha'])
        glosa = row['detalle']
        monto = row['monto']
        categoria = row['categoria']
        
        # Header Asiento
        data.append([f"{fecha}", f"--- Asiento Nº {num_asiento} ---", "", ""])
        
        if row['tipo'] == 'Ingreso':
            # Caja (Debe)
            data.append(["", Paragraph(f"<b>1.1.1 Caja/Bancos</b>", getSampleStyleSheet()['Normal']), f"{monto:,.2f}", ""])
            # Ingreso (Haber)
            data.append(["", Paragraph(f"4.1.1 {categoria}", getSampleStyleSheet()['Normal']), "", f"{monto:,.2f}"])
            
        else: # Gasto
            # Gasto (Debe)
            data.append(["", Paragraph(f"5.1.1 {categoria}", getSampleStyleSheet()['Normal']), f"{monto:,.2f}", ""])
            # Caja (Haber)
            data.append(["", Paragraph(f"<b>1.1.1 Caja/Bancos</b>", getSampleStyleSheet()['Normal']), "", f"{monto:,.2f}"])
            
        # Glosa row
        data.append(["", Paragraph(f"<i>Glosa: {glosa}</i>", getSampleStyleSheet()['Italic']), "", ""])

        total_debe += monto
        total_haber += monto
        num_asiento += 1

    # Totales
    data.append([Benefit_Spacer:= "", "", "", ""]) # Spacer
    data.append(["TOTALES", "", f"{total_debe:,.2f}", f"{total_haber:,.2f}"])

    t = Table(data, colWidths=[1.0*inch, 3.5*inch, 1.25*inch, 1.25*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue), # Header bg
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('ALIGN', (2,0), (-1,-1), 'RIGHT'), 
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey), # Fila Totales
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    
    elements.append(t)
    _add_signatures(elements)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def generate_pdf_balance_general(assets_df, cash_balance, equity_total, result_acum):
    """Genera Balance General en PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    _add_header(elements, f"BALANCE GENERAL (Al {datetime.now().strftime('%d/%m/%Y')})")
    styles = getSampleStyleSheet()
    
    # --- ACTIVO ---
    elements.append(Paragraph("ACTIVO", styles['Heading2']))
    
    # Activo Corriente
    elements.append(Paragraph("ACTIVO CORRIENTE", styles['Heading3']))
    
    data_corriente = [
        ["Disponibilidades", ""],
        ["   Caja M/N", f"{cash_balance:,.2f}"],
        ["TOTAL ACTIVO CORRIENTE", f"{cash_balance:,.2f}"]
    ]
    t_corr = Table(data_corriente, colWidths=[4*inch, 2*inch])
    t_corr.setStyle(TableStyle([
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('LINEABOVE', (0,-1), (-1,-1), 0.5, colors.black)
    ]))
    elements.append(t_corr)
    
    # Activo No Corriente
    elements.append(Paragraph("ACTIVO NO CORRIENTE", styles['Heading3']))
    data_fixed = [["Bienes de Uso", "Valor Histórico"]]
    
    total_fixed_assets = 0
    if not assets_df.empty:
        for _, asset in assets_df.iterrows():
            val = asset['valor_inicial'] 
            data_fixed.append([f"   {asset['nombre']}", f"{val:,.2f}"])
            total_fixed_assets += val
    
    data_fixed.append(["TOTAL ACTIVO NO CORRIENTE", f"{total_fixed_assets:,.2f}"])
    
    t_fixed = Table(data_fixed, colWidths=[4*inch, 2*inch])
    t_fixed.setStyle(TableStyle([
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('LINEABOVE', (0,-1), (-1,-1), 0.5, colors.black)
    ]))
    elements.append(t_fixed)
    elements.append(Spacer(1, 0.2*inch))
    
    # Total Activo
    total_activo = cash_balance + total_fixed_assets
    elements.append(Paragraph(f"TOTAL ACTIVO: Bs {total_activo:,.2f}", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # --- PASIVO Y PATRIMONIO ---
    elements.append(Paragraph("PASIVO Y PATRIMONIO", styles['Heading2']))
    
    data_pat = [
        ["PATRIMONIO", ""],
        ["   Capital Social", f"{equity_total:,.2f}"],
        ["   Resultados Acumulados", f"{result_acum:,.2f}"],
        ["TOTAL PATRIMONIO", f"{equity_total + result_acum:,.2f}"],
        ["TOTAL PASIVO Y PATRIMONIO", f"{equity_total + result_acum:,.2f}"] # Asumiendo Pasivo 0
    ]
    
    t_pat = Table(data_pat, colWidths=[4*inch, 2*inch])
    t_pat.setStyle(TableStyle([
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,-2), (-1,-1), 'Helvetica-Bold'), # Total Patrimonio Header
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Total Final
        ('BACKGROUND', (0,-1), (-1,-1), colors.lightgrey),
        ('BOX', (0,-1), (-1,-1), 1, colors.black),
    ]))
    elements.append(t_pat)
    
    _add_signatures(elements)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_excel_rcv(df_transactions):
    """
    Genera un archivo Excel con formato básico para RCV (Registro de Compras y Ventas).
    Se adapta a las columnas del SIAT de forma simplificada.
    """
    output = BytesIO()
    
    # Filtrar Ventas y Compras
    ventas = df_transactions[df_transactions['tipo'] == 'Ingreso'].copy()
    compras = df_transactions[df_transactions['tipo'] == 'Gasto'].copy()
    
    # Formato Ventas SIAT (Simplificado)
    # N° | Fecha | N° Factura | NIT | Razón Social | Importe Total | ICE | Exentos | Tasa Cero | Subtotal | Descuentos | Importe Base DF | Debito Fiscal
    reporte_ventas = pd.DataFrame()
    reporte_ventas['Fecha'] = ventas['fecha']
    reporte_ventas['N° Factura'] = ventas['n_factura']
    reporte_ventas['NIT Cliente'] = ventas['nit']
    reporte_ventas['Razón Social/Detalle'] = ventas['detalle']
    reporte_ventas['Importe Total'] = ventas['monto']
    reporte_ventas['Débito Fiscal IVA'] = ventas['monto'] * 0.13
    
    # Formato Compras SIAT (Simplificado)
    reporte_compras = pd.DataFrame()
    reporte_compras['Fecha'] = al_compras = compras['fecha']
    reporte_compras['N° Factura'] = compras['n_factura']
    reporte_compras['NIT Proveedor'] = compras['nit']
    reporte_compras['Detalle'] = compras['detalle']
    reporte_compras['Importe Total'] = compras['monto']
    # Solo si tiene factura hay crédito fiscal
    reporte_compras['Crédito Fiscal IVA'] = compras.apply(lambda x: x['monto'] * 0.13 if x['tiene_factura'] else 0, axis=1)

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        reporte_ventas.to_excel(writer, sheet_name='Ventas', index=False)
        reporte_compras.to_excel(writer, sheet_name='Compras', index=False)
        
    return output.getvalue()

def generate_pdf_financials(ingresos_totales, gastos_totales, resultado, breakdown, depreciation=0):
    """
    Genera Estado de Resultados en PDF.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph("WARP6 SOLUTIONS S.R.L.", styles['Title']))
    elements.append(Paragraph("Estado de Resultados (Provisional)", styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    data = [
        ["Concepto", "Monto (Bs)"],
        ["(+) Ingresos Operativos Brutos", f"{breakdown['total_income']:.2f}"],
        ["(-) Débito Fiscal IVA (13%)", f"{breakdown['iva_df']:.2f}"],
        ["(=) Ingresos Netos", f"{breakdown['net_income']:.2f}"],
        ["", ""],
        ["(-) Gastos Operativos Totales", f"{breakdown['total_gastos']:.2f}"],
        ["(+) Crédito Fiscal IVA (13%)", f"{breakdown['iva_cf']:.2f}"],
        ["(-) Impuesto a las Transacciones (3%)", f"{breakdown['it_total']:.2f}"],
        ["(=) Gastos Netos Deducibles", f"{breakdown['gastos_netos']:.2f}"],
        ["(-) Depreciación Activos", f"{depreciation:.2f}"],
        ["", ""],
        ["RESULTADO ANTES DE IMPUESTOS (IUE)", f"{resultado:.2f}"]
    ]
    
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 24))
    elements.append(Paragraph("Nota: Este reporte es referencial y debe ser validado por un contador profesional.", styles['Italic']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_pdf_managerial_detailed(financial_data, period_name="Anual"):
    """
    Genera Estado de Resultados GERENCIAL con DESGLOSE DETALLADO.
    financial_data: Dict estructurado:
    {
        'ingresos': {'total': X, 'items': [{'fecha':, 'detalle':, 'monto':}]},
        'costos_ventas': {'total': X, 'items': []},
        'gastos_personal': ...,
        'gastos_fijos': ...,
        'depreciacion': {'total': X, 'items': []},
        'gastos_financieros': ...,
        'impuestos': ...,
        'kpis': {'margen_bruto': X, 'bait': X, 'utilidad_neta': X, ...}
    }
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_category = ParagraphStyle('Category', parent=styles['Heading3'], textColor=colors.navy)
    style_item = ParagraphStyle('Item', parent=styles['Normal'], fontSize=8)
    
    # Header
    elements.append(Paragraph("WARP6 SOLUTIONS S.R.L.", styles['Title']))
    elements.append(Paragraph(f"ESTADO DE RESULTADOS GERENCIAL DETALLADO ({period_name})", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    # Table Data Accumulator
    # Format: [Description, Date, Detail, Amount]
    # We will build one main table or separate tables? One main table is better for alignment.
    
    data = [["CONCEPTO / DETALLE", "FECHA", "GLOSA", "MONTO (Bs)"]]
    
    def add_section(title, key, is_deduction=True):
        section_data = financial_data.get(key, {'total':0, 'items':[]})
        total = section_data['total']
        
        # Header Row
        sign = "(-)" if is_deduction else "(+)"
        data.append([f"{sign} {title}", "", "", f"{total:,.2f}"])
        
        # Details
        for item in section_data.get('items', []):
            data.append([
                "", 
                item.get('fecha', ''), 
                Paragraph(item.get('detalle', ''), style_item), 
                f"{item.get('monto', 0):,.2f}"
            ])
        
        return total

    # 1. INGRESOS
    total_ingresos = add_section("INGRESOS POR VENTAS", "ingresos", is_deduction=False)
    
    # 2. COSTO DE VENTAS
    total_costos = add_section("COSTO DE VENTAS (Materiales/Insumos)", "costos_ventas")
    
    # KPI: MARGEN BRUTO
    mb = financial_data['kpis'].get('margen_bruto', 0)
    pct_mb = (mb / total_ingresos * 100) if total_ingresos else 0
    data.append([f"(=) MARGEN BRUTO ({pct_mb:.1f}%)", "", "", f"{mb:,.2f}"])
    data.append(["", "", "", ""]) # Spacer Row

    # 3. GASTOS OPERATIVOS
    add_section("GASTOS DE PERSONAL (Sueldos/AFPs)", "gastos_personal")
    add_section("GASTOS OPERATIVOS FIJOS (Alquiler/Servicios)", "gastos_fijos")
    add_section("DEPRECIACIÓN Y AMORTIZACIÓN", "depreciacion")
    
    # KPI: BAIT
    bait = financial_data['kpis'].get('bait', 0)
    pct_bait = (bait / total_ingresos * 100) if total_ingresos else 0
    data.append([f"(=) BAIT / UTILIDAD OPERATIVA ({pct_bait:.1f}%)", "", "", f"{bait:,.2f}"])
    data.append(["", "", "", ""])

    # 4. FINANCIERO Y TRIBUTARIO
    add_section("GASTOS FINANCIEROS (Intereses)", "gastos_financieros")
    add_section("IMPUESTOS DIRECTOS (IT/ITF)", "impuestos")
    
    # Utilidad Antes IUE
    uai = financial_data['kpis'].get('utilidad_antes_iue', 0)
    data.append([f"(=) UTILIDAD ANTES DE IUE", "", "", f"{uai:,.2f}"])
    
    # 5. IUE (Legal/Fiscal)
    iue = financial_data['kpis'].get('iue', 0)
    data.append([f"(-) IUE POR PAGAR (Legal/Fiscal)", "", "", f"{iue:,.2f}"])
    
    # KPI: NETO
    un = financial_data['kpis'].get('utilidad_neta', 0)
    pct_un = (un / total_ingresos * 100) if total_ingresos else 0
    data.append([f"(=) UTILIDAD NETA DEL PERIODO ({pct_un:.1f}%)", "", "", f"{un:,.2f}"])

    # Build Table
    t = Table(data, colWidths=[2.5*inch, 1*inch, 2.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('TVALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        
        # Style for Section Headers (Rows that start with (+) or (-))
        # Note: This is hard to target dynamically in simple reportlab without iterating.
        # We will iterate data to find indices.
    ]))
    
    # Dynamic Styling
    row_styles = []
    for i, row in enumerate(data):
        if str(row[0]).startswith("(+)") or str(row[0]).startswith("(-)"):
            # Section Header
            row_styles.append(('FONTNAME', (0,i), (-1,i), 'Helvetica-Bold'))
            row_styles.append(('BACKGROUND', (0,i), (-1,i), colors.aliceblue))
            row_styles.append(('TEXTCOLOR', (0,i), (-1,i), colors.black))
        elif str(row[0]).startswith("(=)"):
            # Totals
            row_styles.append(('FONTNAME', (0,i), (-1,i), 'Helvetica-Bold'))
            row_styles.append(('BACKGROUND', (0,i), (-1,i), colors.lightgrey if "NETA" not in str(row[0]) else colors.lightgreen))
            row_styles.append(('LINEABOVE', (0,i), (-1,i), 1, colors.black))
        elif i > 0 and row[0] == "":
            # Detail items
            row_styles.append(('TEXTCOLOR', (0,i), (-1,i), colors.darkslategrey))
            row_styles.append(('FONTSIZE', (0,i), (-1,i), 8))
            
    t.setStyle(TableStyle(row_styles))
    
    elements.append(t)
    _add_signatures(elements)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_pdf_tax_shield(df_gastos_sf):
    """
    Genera reporte de Ahorro Fiscal Perdido (Gastos sin factura).
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    _add_header(elements, "ANÁLISIS DE AHORRO FISCAL PERDIDO", "Auditoría Interna")
    
    total_gasto_sf = df_gastos_sf['monto'].sum()
    iva_perdido = total_gasto_sf * 0.13
    # IUE perdido: El gasto es NO deducible, por lo tanto pagas 25% sobre ese monto que NO pudiste restar.
    # Es decir, tu utilidad imponible es mayor por este monto.
    iue_perdido = total_gasto_sf * 0.25 
    total_quemado = iva_perdido + iue_perdido
    
    elements.append(Paragraph(f"Al realizar compras sin factura, su empresa está perdiendo la oportunidad de deducir impuestos. A continuación el detalle del impacto de los <b>Bs {total_gasto_sf:,.2f}</b> gastados sin respaldo legal.", styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    data = [
        ["Concepto", "Impacto Económico (Pérdida)"],
        ["Crédito Fiscal IVA Perdido (13%)", f"Bs {iva_perdido:,.2f}"],
        ["IUE Adicional a Pagar (25%)", f"Bs {iue_perdido:,.2f}"],
        ["TOTAL DINERO PERDIDO", f"Bs {total_quemado:,.2f}"]
    ]
    
    t = Table(data, colWidths=[4*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.firebrick),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.darkred),
        ('GRID', (0,0), (-1,-1), 1, colors.white),
    ]))
    elements.append(t)
    
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("<b>Recomendación:</b> Exija factura en todas sus compras de materiales y servicios. El costo adicional de la factura suele ser inferior al 38% (13% IVA + 25% IUE) que pierde al no tenerla.", styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_pdf_legal_detailed(financial_data, period_name="Anual"):
    """Estado de Resultados LEGAL DETALLADO (Solo Facturado + Depreciación)."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    style_item = ParagraphStyle('Item', parent=styles['Normal'], fontSize=8)
    
    elements.append(Paragraph("WARP6 SOLUTIONS S.R.L.", styles['Title']))
    elements.append(Paragraph(f"ESTADO DE RESULTADOS LEGAL DETALLADO ({period_name})", styles['Heading2']))
    elements.append(Paragraph("Solo Operaciones Facturadas", styles['Italic']))
    elements.append(Spacer(1, 0.2*inch))
    
    data = [["CONCEPTO / DETALLE", "FECHA", "GLOSA", "MONTO (Bs)"]]
    
    def add_section(title, key, is_deduction=True):
        section_data = financial_data.get(key, {'total':0, 'items':[]})
        total = section_data['total']
        sign = "(-)" if is_deduction else "(+)"
        data.append([f"{sign} {title}", "", "", f"{total:,.2f}"])
        for item in section_data.get('items', []):
            data.append(["", item.get('fecha', ''), Paragraph(item.get('detalle', ''), style_item), f"{item.get('monto', 0):,.2f}"])
        return total

    total_ingresos = add_section("INGRESOS FACTURADOS", "ingresos", is_deduction=False)
    add_section("COSTO DE VENTAS (Facturados)", "costos_ventas")
    mb = financial_data['kpis'].get('margen_bruto', 0)
    data.append([f"(=) MARGEN BRUTO ({(mb/total_ingresos*100) if total_ingresos else 0:.1f}%)", "", "", f"{mb:,.2f}"])
    data.append(["", "", "", ""])

    add_section("GASTOS DE PERSONAL DEDUCIBLES", "gastos_personal")
    add_section("GASTOS OPERATIVOS DEDUCIBLES", "gastos_fijos")
    add_section("DEPRECIACIÓN (Deducible)", "depreciacion")
    bait = financial_data['kpis'].get('bait', 0)
    data.append([f"(=) UTILIDAD OPERATIVA", "", "", f"{bait:,.2f}"])
    data.append(["", "", "", ""])

    add_section("GASTOS FINANCIEROS", "gastos_financieros")
    add_section("IMPUESTOS DIRECTOS", "impuestos")
    uai = financial_data['kpis'].get('utilidad_antes_iue', 0)
    data.append([f"(=) UTILIDAD ANTES DE IUE", "", "", f"{uai:,.2f}"])
    iue = financial_data['kpis'].get('iue', 0)
    data.append([f"(-) IUE ESTIMADO (25%)", "", "", f"{iue:,.2f}"])
    un = financial_data['kpis'].get('utilidad_neta', 0)
    data.append([f"(=) UTILIDAD NETA FISCAL", "", "", f"{un:,.2f}"])

    t = Table(data, colWidths=[2.5*inch, 1*inch, 2.5*inch, 1.5*inch])
    t.setStyle(TableStyle([('TVALIGN', (0,0), (-1,-1), 'TOP'), ('BACKGROUND', (0,0), (-1,0), colors.darkgreen), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')]))
    
    row_styles = []
    for i, row in enumerate(data):
        if str(row[0]).startswith("(+)") or str(row[0]).startswith("(-)"):
            row_styles.extend([('FONTNAME', (0,i), (-1,i), 'Helvetica-Bold'), ('BACKGROUND', (0,i), (-1,i), colors.lightcyan)])
        elif str(row[0]).startswith("(=)"):
            row_styles.extend([('FONTNAME', (0,i), (-1,i), 'Helvetica-Bold'), ('BACKGROUND', (0,i), (-1,i), colors.palegreen if "NETA" in str(row[0]) else colors.lightgrey), ('LINEABOVE', (0,i), (-1,i), 1, colors.black)])
        elif i > 0 and row[0] == "":
            row_styles.extend([('TEXTCOLOR', (0,i), (-1,i), colors.darkslategrey), ('FONTSIZE', (0,i), (-1,i), 8)])
    t.setStyle(TableStyle(row_styles))
    
    elements.append(t)
    _add_signatures(elements)
    doc.build(elements)
    buffer.seek(0)
    return buffer



def generate_pdf_balance_sin(balance_data, period_name="Anual"):
    """
    Genera Balance General en Formato Oficial SIN.
    Recibe estructura calculada por logic.calculate_balance_sheet
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Header
    elements.append(Paragraph("WARP6 SOLUTIONS S.R.L.", styles['Title']))
    elements.append(Paragraph(f"BALANCE GENERAL ({period_name})", styles['Heading2']))
    elements.append(Paragraph("(Expresado en Bolivianos)", styles['Italic']))
    elements.append(Spacer(1, 0.2*inch))
    
    data = []
    data.append(["ACTIVO", "", ""])
    
    # ACTIVO CORRIENTE
    act = balance_data['activos']
    data.append(["ACTIVO CORRIENTE", "", ""])
    data.append(["   1. Disponibilidades (Caja/Bancos)", f"{act['corriente']['caja']:,.2f}", ""])
    data.append(["   2. Crédito Fiscal IVA", f"{act['corriente']['iva_credito']:,.2f}", ""])
    data.append(["   3. Inventarios", f"{act['corriente']['inventarios']:,.2f}", ""])
    data.append(["   TOTAL ACTIVO CORRIENTE", "", f"{act['corriente']['total']:,.2f}"])
    data.append(["", "", ""])
    
    # ACTIVO NO CORRIENTE
    data.append(["ACTIVO NO CORRIENTE", "", ""])
    data.append(["   1. Activos Fijos Brutos", f"{act['no_corriente']['fijos_bruto']:,.2f}", ""])
    data.append(["   2. (-) Depreciación Acumulada", f"({act['no_corriente']['dep_acum']:,.2f})", ""])
    data.append(["   TOTAL ACTIVO NO CORRIENTE", "", f"{act['no_corriente']['total']:,.2f}"])
    data.append(["", "", ""])
    
    # TOTAL ACTIVO
    total_activo = balance_data['validacion']['activos']
    data.append(["TOTAL ACTIVO", "", f"{total_activo:,.2f}"])
    
    # PASIVO
    pas = balance_data['pasivos']
    data.append(["PASIVO", "", ""])
    data.append(["PASIVO CORRIENTE", "", ""])
    data.append(["   1. Débito Fiscal IVA por Pagar", f"{pas['corriente']['iva_por_pagar']:,.2f}", ""])
    data.append(["   2. Impues. Transacciones (IT) por Pagar", f"{pas['corriente']['it_por_pagar']:,.2f}", ""])
    data.append(["   3. IUE por Pagar", f"{pas['corriente']['iue_por_pagar']:,.2f}", ""])
    # Safely get retenciones if logic updated, default 0
    ret_pay = pas['corriente'].get('retenciones_por_pagar', 0)
    data.append(["   4. Retenciones (RC-IVA/IT) por Pagar", f"{ret_pay:,.2f}", ""])
    
    data.append(["   TOTAL PASIVO", "", f"{pas['corriente']['total']:,.2f}"])
    data.append(["", "", ""])
    
    # PATRIMONIO
    pat = balance_data['patrimonio']
    data.append(["PATRIMONIO", "", ""])
    data.append(["   1. Capital Social", f"{pat['capital']:,.2f}", ""])
    data.append(["   2. Resultados Acumulados", f"{pat['resultados_acum']:,.2f}", ""])
    data.append(["   TOTAL PATRIMONIO", "", f"{pat['total']:,.2f}"])
    data.append(["", "", ""])
    
    # TOTAL PASIVO Y PATRIMONIO
    total_pp = balance_data['validacion']['pasivo_patrimonio']
    data.append(["TOTAL PASIVO Y PATRIMONIO", "", f"{total_pp:,.2f}"])

    t = Table(data, colWidths=[3.5*inch, 1.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'), # ACTIVO Title
        ('FONTNAME', (0,10), (0,10), 'Helvetica-Bold'), # TOTAL ACTIVO
        ('LINEABOVE', (2,10), (2,10), 1, colors.black),
        
        ('FONTNAME', (0,11), (0,11), 'Helvetica-Bold'), # PASIVO Title
        ('FONTNAME', (0,21), (0,21), 'Helvetica-Bold'), # PATRIMONIO Title (Shifted down by 1 row)
        
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # TOTAL P+P
        ('LINEABOVE', (2,-1), (2,-1), 1, colors.black),
        
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 0.5*inch))
    
    # Notas
    elements.append(Paragraph("<b>Notas a los Estados Financieros:</b>", styles['Normal']))
    elements.append(Paragraph("1. El efectivo y equivalentes representan la liquidez disponible tras operaciones.", styles['Normal']))
    elements.append(Paragraph("2. Los inventarios se valoran al costo (método PEPS o promedio).", styles['Normal']))
    elements.append(Paragraph("3. El Capital Social refleja los aportes de los socios registrados.", styles['Normal']))
    
    _add_signatures(elements)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_pdf_gerencial_completo(balance_data, breakdown_mgr, period_name="anual"):
    """
    Reporte Gerencial Completo (5 Secciones).
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title Page
    elements.append(Paragraph("INFORME DE GESTIÓN GERENCIAL", styles['Title']))
    elements.append(Paragraph("WARP6 SOLUTIONS S.R.L.", styles['Heading2']))
    elements.append(Paragraph(f"Período: {period_name}", styles['Normal']))
    elements.append(Spacer(1, 0.5*inch))
    
    # 1. RESUMEN EJECUTIVO
    elements.append(Paragraph("1. RESUMEN EJECUTIVO", styles['Heading2']))
    
    ventas = breakdown_mgr['ingresos']['total']
    utilidad = breakdown_mgr['kpis']['utilidad_neta']
    margen_neto = (utilidad / ventas * 100) if ventas > 0 else 0
    margen_bruto_pct = (breakdown_mgr['kpis']['margen_bruto'] / ventas * 100) if ventas > 0 else 0
    
    tek = f"""
    Durante el período {period_name}, la empresa generó ingresos totales por <b>Bs {ventas:,.2f}</b>, 
    logrando una utilidad neta de <b>Bs {utilidad:,.2f}</b>, lo que representa un margen neto del <b>{margen_neto:.1f}%</b>.
    El margen bruto se situó en <b>{margen_bruto_pct:.1f}%</b>.
    """
    elements.append(Paragraph(tek, styles['Normal']))
    elements.append(Spacer(1, 0.2*inch))
    
    # KPI Table
    kpi_data = [
        ["Indicador", "Valor"],
        ["Ingresos Totales", f"Bs {ventas:,.2f}"],
        ["Utilidad Neta", f"Bs {utilidad:,.2f}"],
        ["Rentabilidad (ROS)", f"{margen_neto:.1f}%"],
        ["Caja Disponible", f"Bs {balance_data['activos']['corriente']['caja']:,.2f}"]
    ]
    t = Table(kpi_data, colWidths=[3*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.navy),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))
    elements.append(t)
    elements.append(PageBreak())
    
    # 2. ESTADO DE RESULTADOS DETALLADO
    elements.append(Paragraph("2. ESTADO DE RESULTADOS OPERATIVO", styles['Heading2']))
    # Reutilizamos lógica de tabla detallada simplificada
    det_data = [["Concepto", "Monto (Bs)"]]
    det_data.append(["Ingresos Totales", f"{ventas:,.2f}"])
    det_data.append(["(-) Costos Directos", f"{breakdown_mgr['costos_ventas']['total']:,.2f}"])
    det_data.append(["(=) MARGEN BRUTO", f"{breakdown_mgr['kpis']['margen_bruto']:,.2f}"])
    det_data.append(["(-) Gastos de Personal", f"{breakdown_mgr['gastos_personal']['total']:,.2f}"])
    det_data.append(["(-) Gastos Operativos", f"{breakdown_mgr['gastos_fijos']['total']:,.2f}"])
    det_data.append(["(-) Depreciación", f"{breakdown_mgr['depreciacion']['total']:,.2f}"])
    det_data.append(["(=) UTILIDAD OPERATIVA (EBIT)", f"{breakdown_mgr['kpis']['bait']:,.2f}"])
    t2 = Table(det_data)
    t2.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(t2)
    elements.append(Spacer(1, 0.3*inch))
    
    # 3. ANÁLISIS POR PROYECTO (Simulado con 'Detalle')
    elements.append(Paragraph("3. ANÁLISIS DE VENTAS (Top Clientes/Proyectos)", styles['Heading2']))
    # Extract entries from breakdown
    items = breakdown_mgr['ingresos']['items']
    # Group by detail (naive approach) - Just list top 10
    items_sorted = sorted(items, key=lambda x: x['monto'], reverse=True)[:10]
    
    proj_data = [["Fecha", "Cliente/Detalle", "Monto"]]
    for i in items_sorted:
        proj_data.append([i['fecha'], Paragraph(i['detalle'][:50], styles['Normal']), f"{i['monto']:,.2f}"])
        
    t3 = Table(proj_data, colWidths=[1.5*inch, 3*inch, 1.5*inch])
    t3.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.darkgreen), ('TEXTCOLOR', (0,0), (-1,0), colors.white)]))
    elements.append(t3)
    elements.append(Spacer(1, 0.3*inch))
    
    # 4. CONTROL DE GASTOS
    elements.append(Paragraph("4. DESGLOSE DE GASTOS", styles['Heading2']))
    elements.append(Paragraph("Distribución de egresos operativos:", styles['Normal']))
    
    g_personal = breakdown_mgr['gastos_personal']['total']
    g_fijos = breakdown_mgr['gastos_fijos']['total']
    g_costos = breakdown_mgr['costos_ventas']['total']
    
    gastos_data = [
        ["Categoría", "Monto", "% Total Gastos"],
        ["Personal", f"{g_personal:,.2f}", f"{(g_personal/(g_personal+g_fijos+g_costos)*100):.1f}%" if (g_personal+g_fijos+g_costos)>0 else "0%"],
        ["Operativos/Fijos", f"{g_fijos:,.2f}", f"{(g_fijos/(g_personal+g_fijos+g_costos)*100):.1f}%" if (g_personal+g_fijos+g_costos)>0 else "0%"],
        ["Costos Directos", f"{g_costos:,.2f}", f"{(g_costos/(g_personal+g_fijos+g_costos)*100):.1f}%" if (g_personal+g_fijos+g_costos)>0 else "0%"]
    ]
    t4 = Table(gastos_data)
    t4.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
    elements.append(t4)
    
    # 5. PROYECCIONES
    elements.append(Paragraph("5. PROYECCIONES Y RECOMENDACIONES", styles['Heading2']))
    elements.append(Paragraph("• <b>Optimización Fiscal:</b> Revise el nivel de gastos deducibles. Se recomienda exigir factura en compras de material.", styles['Normal']))
    elements.append(Paragraph("• <b>Flujo de Caja:</b> Mantener un fondo de maniobra equivalente a 3 meses de gastos fijos.", styles['Normal']))
    elements.append(Paragraph("• <b>Crecimiento:</b> Se proyecta un crecimiento orgánico del 10% si se mantiene el margen actual.", styles['Normal']))
    
    _add_signatures(elements)
    doc.build(elements)
    buffer.seek(0)
    return buffer
    _add_signatures(elements)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_pdf_balance_real(balance_data, period_name="Anual"):
    """
    Genera Balance General REAL/GERENCIAL.
    Muestra la caja real y los gastos no deducibles como ajuste.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Header
    elements.append(Paragraph("WARP6 SOLUTIONS S.R.L.", styles['Title']))
    elements.append(Paragraph(f"BALANCE GENERAL GERENCIAL ({period_name})", styles['Heading2']))
    elements.append(Paragraph("(Expresado en Bolivianos - Refleja Realidad de Caja)", styles['Italic']))
    elements.append(Spacer(1, 0.2*inch))
    
    data = []
    data.append(["ACTIVO", "", ""])
    
    # ACTIVO CORRIENTE
    act = balance_data['activos']
    data.append(["ACTIVO CORRIENTE", "", ""])
    data.append(["   1. Disponibilidades (Caja/Bancos REAL)", f"{act['corriente']['caja']:,.2f}", ""])
    data.append(["   2. Crédito Fiscal IVA", f"{act['corriente']['iva_credito']:,.2f}", ""])
    data.append(["   3. Inventarios", f"{act['corriente']['inventarios']:,.2f}", ""])
    data.append(["   TOTAL ACTIVO CORRIENTE", "", f"{act['corriente']['total']:,.2f}"])
    data.append(["", "", ""])
    
    # ACTIVO NO CORRIENTE
    data.append(["ACTIVO NO CORRIENTE", "", ""])
    data.append(["   1. Activos Fijos Brutos", f"{act['no_corriente']['fijos_bruto']:,.2f}", ""])
    data.append(["   2. (-) Depreciación Acumulada", f"({act['no_corriente']['dep_acum']:,.2f})", ""])
    data.append(["   TOTAL ACTIVO NO CORRIENTE", "", f"{act['no_corriente']['total']:,.2f}"])
    data.append(["", "", ""])
    
    # TOTAL ACTIVO
    total_activo = balance_data['validacion']['activos']
    data.append(["TOTAL ACTIVO", "", f"{total_activo:,.2f}"])
    
    # PASIVO
    pas = balance_data['pasivos']
    data.append(["PASIVO", "", ""])
    data.append(["PASIVO CORRIENTE", "", ""])
    data.append(["   1. Débito Fiscal IVA por Pagar", f"{pas['corriente']['iva_por_pagar']:,.2f}", ""])
    data.append(["   2. Impues. Transacciones (IT) por Pagar", f"{pas['corriente']['it_por_pagar']:,.2f}", ""])
    data.append(["   3. IUE por Pagar (25% s/Utilidad Fiscal)", f"{pas['corriente']['iue_por_pagar']:,.2f}", ""])
    ret_pay = pas['corriente'].get('retenciones_por_pagar', 0)
    data.append(["   4. Retenciones (RC-IVA/IT) por Pagar", f"{ret_pay:,.2f}", ""])
    data.append(["   TOTAL PASIVO", "", f"{pas['corriente']['total']:,.2f}"])
    data.append(["", "", ""])
    
    # PATRIMONIO
    pat = balance_data['patrimonio']
    data.append(["PATRIMONIO", "", ""])
    data.append(["   1. Capital Social", f"{pat['capital']:,.2f}", ""])
    data.append(["   2. Utilidad Neta Fiscal (Declarada)", f"{pat['utilidad_fiscal']:,.2f}", ""])
    data.append(["   3. (-) Gastos No Deducibles (sin factura)", f"({balance_data['info_adicional']['gastos_sin_factura']:,.2f})", ""])
    data.append(["   RESULTADOS ACUMULADOS REALES", "", f"{pat['resultados_acum']:,.2f}"])
    data.append(["   TOTAL PATRIMONIO", "", f"{pat['total']:,.2f}"])
    data.append(["", "", ""])
    
    # TOTAL PASIVO Y PATRIMONIO
    total_pp = balance_data['validacion']['pasivo_patrimonio']
    data.append(["TOTAL PASIVO Y PATRIMONIO", "", f"{total_pp:,.2f}"])

    t = Table(data, colWidths=[3.5*inch, 1.5*inch, 1.5*inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ('FONTNAME', (0,13), (0,13), 'Helvetica-Bold'),
        ('LINEABOVE', (2,13), (2,13), 1, colors.black),
        ('FONTNAME', (0,14), (0,14), 'Helvetica-Bold'),
        ('FONTNAME', (0,23), (0,23), 'Helvetica-Bold'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('LINEABOVE', (2,-1), (2,-1), 1, colors.black),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
        ('TEXTCOLOR', (0,26), (-1,26), colors.red),
    ]))
    
    elements.append(t)
    elements.append(Spacer(1, 0.3*inch))
    
    # Notas Explicativas
    elements.append(Paragraph("<b>Notas Importantes:</b>", styles['Heading3']))
    elements.append(Paragraph(f"1. <b>Caja Real</b>: Refleja el saldo bancario real después de TODOS los movimientos (con y sin factura).", styles['Normal']))
    elements.append(Paragraph(f"2. <b>Utilidad Fiscal</b>: Bs {balance_data['patrimonio']['utilidad_fiscal']:,.2f} - Base para cálculo de IUE (25%). Se calcula solo con gastos facturados.", styles['Normal']))
    elements.append(Paragraph(f"3. <b>Gastos No Deducibles</b>: Bs {balance_data['info_adicional']['gastos_sin_factura']:,.2f} - Gastos sin factura que redujeron la caja pero NO son deducibles para impuestos.", styles['Normal']))
    elements.append(Paragraph("4. <b>Recomendación</b>: Exigir facturas en todas las compras futuras para maximizar deducciones fiscales.", styles['Normal']))
    
    _add_signatures(elements)
    doc.build(elements)
    buffer.seek(0)
    return buffer
