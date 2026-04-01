import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "contabilidad_warp6.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Tabla de Transacciones
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            tipo TEXT NOT NULL, -- 'Ingreso', 'Gasto'
            categoria TEXT NOT NULL,
            detalle TEXT NOT NULL,
            n_factura TEXT,
            nit TEXT,
            monto REAL NOT NULL,
            metodo_pago TEXT,
            tiene_factura BOOLEAN DEFAULT 0,
            aplica_retencion BOOLEAN DEFAULT 0
        )
    ''')
    
    # MIGRATION CHECK: Add aplica_retencion if not exists
    try:
        c.execute("SELECT aplica_retencion FROM transactions LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE transactions ADD COLUMN aplica_retencion BOOLEAN DEFAULT 0")
        conn.commit()
        
    # MIGRATION CHECK: Add proyecto if not exists
    try:
        c.execute("SELECT proyecto FROM transactions LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE transactions ADD COLUMN proyecto TEXT DEFAULT 'General'")
        conn.commit()
    
    # Tabla de Activos Fijos
    c.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            fecha_adquisicion DATE NOT NULL,
            valor_inicial REAL NOT NULL,
            vida_util_anios INTEGER DEFAULT 4, -- 4 años para computación (25%)
            rubro TEXT DEFAULT 'Equipos de Computación',
            estado TEXT DEFAULT 'Activo'
        )
    ''')
    
    conn.commit()
    conn.close()

def clear_all_transactions():
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM transactions")
    # Reset auto-increment for transactions if needed
    c.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
    conn.commit()
    conn.close()

def add_transaction(fecha, tipo, categoria, detalle, n_factura, nit, monto, metodo_pago, tiene_factura, aplica_retencion=False, proyecto='General'):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO transactions (fecha, tipo, categoria, detalle, n_factura, nit, monto, metodo_pago, tiene_factura, aplica_retencion, proyecto)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (fecha, tipo, categoria, detalle, n_factura, nit, monto, metodo_pago, tiene_factura, aplica_retencion, proyecto))
    conn.commit()
    conn.close()

def get_transactions():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY fecha DESC", conn)
    conn.close()
    return df

def add_asset(nombre, fecha_adquisicion, valor_inicial, vida_util_anios, rubro):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO assets (nombre, fecha_adquisicion, valor_inicial, vida_util_anios, rubro)
        VALUES (?, ?, ?, ?, ?)
    ''', (nombre, fecha_adquisicion, valor_inicial, vida_util_anios, rubro))
    conn.commit()
    conn.close()

def get_assets():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM assets", conn)
    conn.close()
    return df

def delete_asset(asset_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
    conn.commit()
    conn.close()

