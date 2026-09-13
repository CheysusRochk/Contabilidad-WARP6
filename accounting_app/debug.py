import sqlite3
import pandas as pd
import sys
import os

from logic import calculate_balance_sheet_real, calculate_balance_sheet

conn = sqlite3.connect('../accounting.db')
df = pd.read_sql('SELECT * FROM transactions', conn)
assets_df = pd.read_sql('SELECT * FROM assets', conn)
conn.close()

balance_real = calculate_balance_sheet_real(df, assets_df)
print(f"Real Activos: {balance_real['activos']['corriente']['total'] + balance_real['activos']['no_corriente']['total']}")
print(f"Real Pasivo+Pat: {balance_real['pasivos']['corriente']['total'] + balance_real['patrimonio']['total']}")
print(f"Descuadre Real: {balance_real['validacion']['diferencia']}")

with open('debug_out.txt', 'w') as f:
    f.write(f"Descuadre: {balance_real['validacion']['diferencia']}\n")
    f.write(str(balance_real))
