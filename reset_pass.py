import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from app import create_app, bcrypt
from bson import ObjectId

app = create_app()
with app.app_context():
    from app.db import users_col, find_user_by_email

    new_password = 'netstock123'
    new_hash = bcrypt.generate_password_hash(new_password).decode()

    for email in ['admin@netstock.app', 'admin@inventory.app']:
        user = find_user_by_email(email)
        if user:
            users_col().update_one(
                {'_id': ObjectId(user.id)},
                {'$set': {'password_hash': new_hash}}
            )
            print(f'Reset: {email}  =>  password: {new_password}')
