import sqlite3
import pandas as pd

conn = sqlite3.connect('accounting_app/contabilidad_warp6.db')
df = pd.read_sql_query("SELECT fecha, detalle, tiene_factura, categoria FROM transactions WHERE detalle LIKE '%puerta%' OR detalle LIKE '%solvencia%' OR detalle LIKE '%poderes%' OR detalle LIKE '%legalizacion%'", conn)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)
print(df)
conn.close()
