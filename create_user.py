import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from app import create_app, bcrypt
app = create_app()

with app.app_context():
    from app.db import users_col, find_user_by_email
    from datetime import datetime

    email = 'admin@netstock.app'
    existing = find_user_by_email(email)
    if existing:
        print(f'User already exists: {email}')
    else:
        users_col().insert_one({
            'name': 'Admin',
            'email': email,
            'password_hash': bcrypt.generate_password_hash('Admin1234').decode(),
            'role': 'admin',
            'created_at': datetime.utcnow(),
        })
        print(f'Created: {email}')

    print('\nAll users in DB:')
    for u in users_col().find({}, {'email': 1, 'role': 1}):
        print(f'  {u["email"]}  ({u["role"]})')
