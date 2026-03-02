import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('accounting_app/contabilidad_warp6.db')

# Query October transactions
query = """
SELECT fecha, tipo, categoria, detalle, monto, tiene_factura 
FROM transactions 
WHERE fecha BETWEEN '2025-10-01' AND '2025-10-31'
ORDER BY fecha ASC
"""

df = pd.read_sql_query(query, conn)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

print("--- TRANSACCIONES OCTUBRE 2025 ---")
print(df)

print("\n--- ANALISIS FISCAL OCTUBRE ---")
total_ingresos = df[(df['tipo'] == 'Ingreso') & 
                   (~df['categoria'].str.lower().str.contains('aporte'))]['monto'].sum()

total_gastos_facturados = df[(df['tipo'] == 'Gasto') & (df['tiene_factura'] == 1)]['monto'].sum()

iva_df = total_ingresos * 0.13
iva_cf = total_gastos_facturados * 0.13
iva_pagar = iva_df - iva_cf

print(f"Total Ingresos (Ventas): {total_ingresos}")
print(f"IVA DF (13%): {iva_df}")
print(f"Total Gastos Facturados: {total_gastos_facturados}")
print(f"IVA CF (13%): {iva_cf}")
print(f"IVA Calculado a Pagar: {iva_pagar}")

target_cf_gap = 224.90
missing_invoice_amount = target_cf_gap / 0.13
print(f"\nDiferencia reportada: {target_cf_gap}")
print(f"Monto de factura faltante (aprox): {missing_invoice_amount}")
# --- BUSCANDO CANDIDATOS (Gastos ~1730 Bs) ---
print(df)

conn.close()
