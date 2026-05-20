import click
from datetime import datetime


def register_commands(app):
    @app.cli.command('seed-db')
    def seed_db():
        """Seed initial admin user and reference data into MongoDB."""
        from app import bcrypt
        from app.db import (
            users_col, sites_col, asset_types_col, ensure_indexes,
        )

        ensure_indexes()

        if not users_col().find_one({'email': 'admin@inventory.app'}):
            users_col().insert_one({
                'name':          'Admin',
                'email':         'admin@inventory.app',
                'password_hash': bcrypt.generate_password_hash('admin1234').decode('utf-8'),
                'role':          'admin',
                'created_at':    datetime.utcnow(),
            })
            click.echo('  Created admin user: admin@inventory.app / admin1234')

        for name in ['Beit VaGan', 'Tel Aviv HQ', 'Haifa DC', 'Storage Warehouse']:
            if not sites_col().find_one({'name': name}):
                sites_col().insert_one({'name': name, 'address': None, 'notes': None})
                click.echo(f'  Created site: {name}')

        for name, category in [
            ('SFP Module', 'Networking'), ('Switch', 'Networking'),
            ('Router', 'Networking'), ('Patch Panel', 'Networking'),
            ('Firewall', 'Security'), ('Server', 'Compute'),
            ('UPS', 'Power'), ('Cable', 'Cabling'),
        ]:
            if not asset_types_col().find_one({'name': name}):
                asset_types_col().insert_one({'name': name, 'category': category})
                click.echo(f'  Created asset type: {name}')

        click.echo('MongoDB seeded successfully.')
