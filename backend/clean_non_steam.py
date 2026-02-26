import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.db.connection import init_db, get_db
init_db()
con = get_db()
total = con.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
print(f"Total registros: {total:,}")
stores = con.execute("SELECT shop_name, shop_id, COUNT(*) as cnt FROM price_history GROUP BY shop_name, shop_id ORDER BY cnt DESC LIMIT 20").fetchdf()
print(stores.to_string())
other_count = con.execute("SELECT COUNT(*) FROM price_history WHERE shop_id != 61 AND shop_id IS NOT NULL AND LOWER(shop_name) NOT LIKE '%steam%' AND shop_name IS NOT NULL").fetchone()[0]
print(f"\nRegistros de otras tiendas: {other_count:,}")
if other_count == 0:
    print("DB ya esta limpia.")
    sys.exit(0)
confirm = input(f"Eliminar {other_count:,} registros? (s/n): ").strip().lower()
if confirm == "s":
    con.execute("DELETE FROM price_history WHERE shop_id != 61 AND shop_id IS NOT NULL AND LOWER(shop_name) NOT LIKE '%steam%' AND shop_name IS NOT NULL")
    after = con.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
    print(f"Listo. Antes: {total:,} | Despues: {after:,} | Eliminados: {total-after:,}")
