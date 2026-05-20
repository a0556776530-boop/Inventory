import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from app import create_app, bcrypt
app = create_app()

with app.app_context():
    from app.db import find_user_by_email

    for email, pwd in [('admin@netstock.app', 'Admin1234'), ('admin@inventory.app', 'admin1234')]:
        user = find_user_by_email(email)
        if not user:
            print(f'NOT FOUND: {email}')
            continue
        ok = bcrypt.check_password_hash(user.password_hash, pwd)
        print(f'{email} / {pwd}  =>  {"LOGIN OK" if ok else "WRONG PASSWORD"}')
