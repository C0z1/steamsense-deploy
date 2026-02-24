import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.db.connection import init_db, get_db
from src.db.models import create_all_tables, create_user_tables

init_db()
con = get_db()

total = con.execute('SELECT COUNT(*) FROM games').fetchone()[0]
print(f'Total games: {total}')

no_appid = con.execute('SELECT COUNT(*) FROM games WHERE appid IS NULL').fetchone()[0]
print(f'Sin appid: {no_appid}')

orphans = con.execute("SELECT COUNT(*) FROM games WHERE title = id").fetchone()[0]
print(f'Titulo = ID (huerfanos): {orphans}')

fixable = con.execute('''
    SELECT COUNT(DISTINCT g.id)
    FROM games g
    JOIN price_history ph ON ph.game_id = g.id
    WHERE g.appid IS NULL AND ph.appid IS NOT NULL
''').fetchone()[0]
print(f'Reparables (appid en price_history): {fixable}')

print('\n--- 10 ejemplos de problematicos ---')
rows = con.execute('''
    SELECT 
        g.id, 
        g.title, 
        g.appid,
        (SELECT ph.appid FROM price_history ph 
         WHERE ph.game_id = g.id AND ph.appid IS NOT NULL 
         LIMIT 1) as ph_appid
    FROM games g
    WHERE g.title = g.id OR g.appid IS NULL
    LIMIT 10
''').fetchdf()
print(rows.to_string())