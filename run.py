"""
Development entry point.

Usage:
    python run.py

Seeds the admin user and reference data on first run.
Default login: admin@inventory.app / admin1234
"""
import os

from app import create_app, bcrypt
from app.db import (
    users_col, sites_col, asset_types_col, ensure_indexes, find_user_by_email,
)

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        ensure_indexes()

        if not find_user_by_email('admin@inventory.app'):
            from datetime import datetime
            users_col().insert_one({
                'name':          'Admin',
                'email':         'admin@inventory.app',
                'password_hash': bcrypt.generate_password_hash('admin1234').decode(),
                'role':          'admin',
                'created_at':    datetime.utcnow(),
            })
            for name in ['Beit VaGan', 'Tel Aviv HQ', 'Haifa DC', 'Storage Warehouse']:
                sites_col().insert_one({'name': name, 'address': None, 'notes': None})
            for name, cat in [
                ('SFP Module', 'Networking'), ('Switch', 'Networking'),
                ('Router', 'Networking'), ('Patch Panel', 'Networking'),
                ('Firewall', 'Security'), ('Server', 'Compute'),
                ('UPS', 'Power'), ('Cable', 'Cabling'),
            ]:
                asset_types_col().insert_one({'name': name, 'category': cat})
            print('[Inventory] First run — seeded admin user and reference data.')
            print('[Inventory] Login: admin@inventory.app / admin1234')

    app.run(debug=True, host='127.0.0.1', port=5000)
