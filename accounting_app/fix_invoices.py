import sqlite3

def fix_transactions():
    conn = sqlite3.connect('accounting_app/contabilidad_warp6.db')
    c = conn.cursor()
    
    # Items that the user reported were missing from the detailed report
    # because they likely had 'tiene_factura' set to 0 due to the importer bug.
    items_to_fix = [
        '%puerta cristembo%',
        '%solvencia fiscal%',
        '%legalizacion de poderes%',
        '%dominio adsib%'
    ]
    
    print("Fixing transactions...")
    count = 0
    for item in items_to_fix:
        # Check if they exist first
        c.execute("SELECT count(*) FROM transactions WHERE detalle LIKE ? AND tiene_factura = 0", (item,))
        found = c.fetchone()[0]
        if found > 0:
            print(f"Found {found} items matching '{item}' to fix.")
            c.execute("UPDATE transactions SET tiene_factura = 1 WHERE detalle LIKE ?", (item,))
            count += found
        else:
            print(f"No items needing fix for '{item}' (might already be fixed or not found).")
            
    conn.commit()
    conn.close()
    print(f"Done. Updated {count} transactions.")

if __name__ == "__main__":
    fix_transactions()
