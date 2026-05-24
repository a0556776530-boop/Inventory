"""Verifies all main routes and Atlas data."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

from app import create_app
app = create_app()
app.config['WTF_CSRF_ENABLED'] = False

results = []

with app.test_client() as client:
    client.post('/auth/login', data={
        'email': 'admin@netstock.app',
        'password': 'netstock123',
    }, follow_redirects=True)

    routes = [
        ('Dashboard',    '/'),
        ('Assets list',  '/assets/'),
        ('New asset',    '/assets/new'),
        ('Sites',        '/sites/'),
        ('Tasks',        '/tasks/'),
        ('Estimates',    '/estimates/'),
        ('History',      '/estimates/history'),
        ('Contacts',     '/contacts/'),
        ('Scan',         '/scan/'),
        ('Admin users',  '/admin/users'),
        ('Export page',  '/admin/export'),
        ('Settings API', '/api/settings'),
    ]

    for name, url in routes:
        r = client.get(url, follow_redirects=True)
        ok = r.status_code == 200
        results.append((name, url, r.status_code, 'OK' if ok else 'FAIL'))

with app.app_context():
    from app.db import assets_col
    total      = assets_col().count_documents({})
    with_price = assets_col().count_documents({'price_usd': {'$ne': None}})
    with_qty   = assets_col().count_documents({'quantity':  {'$ne': None}})
    with_thr   = assets_col().count_documents({'min_threshold': {'$ne': None}})
    low_stock  = assets_col().count_documents({
        'quantity': {'$ne': None},
        '$expr': {'$lte': ['$quantity', {'$ifNull': ['$min_threshold', 5]}]},
    })

print('\n=== ROUTE CHECKS ===')
for name, url, code, status in results:
    print(f'  [{status}]  {name:<18} HTTP {code}')

print(f'\n=== ATLAS DATA ===')
print(f'  Total assets   : {total}')
print(f'  With price     : {with_price}')
print(f'  With qty       : {with_qty}')
print(f'  With threshold : {with_thr}')
print(f'  Low stock items: {low_stock}')

all_ok = all(r[3] == 'OK' for r in results)
print(f'\n>>> {"ALL ROUTES OK" if all_ok else "SOME ROUTES FAILED"} <<<')
