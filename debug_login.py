"""Test login through Flask test client - bypasses browser/CSRF."""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from app import create_app, bcrypt
app = create_app()
app.config['WTF_CSRF_ENABLED'] = False  # disable CSRF for test

with app.test_client() as client:
    # Try login
    resp = client.post('/auth/login', data={
        'email': 'admin@netstock.app',
        'password': 'netstock123',
        'remember': 'false',
    }, follow_redirects=True)

    print(f'Status: {resp.status_code}')
    body = resp.data.decode('utf-8', errors='replace')

    if 'dashboard' in resp.request.url or 'Dashboard' in body:
        print('SUCCESS - reached dashboard!')
    elif 'Incorrect' in body or 'incorrect' in body or 'שגוי' in body:
        print('FAIL - wrong email or password message shown')
    elif 'is-invalid' in body:
        print('FAIL - form validation errors:')
        import re
        errors = re.findall(r'invalid-feedback[^>]*>(.*?)</div>', body)
        for e in errors:
            print(f'  - {e}')
    else:
        print('Unknown result - checking page title:')
        title = re.search(r'<title>(.*?)</title>', body)
        print(f'  Title: {title.group(1) if title else "N/A"}')

    # Also check DB directly
    print()
    with app.app_context():
        from app.db import find_user_by_email
        user = find_user_by_email('admin@netstock.app')
        if user:
            ok = bcrypt.check_password_hash(user.password_hash, 'netstock123')
            print(f'DB check: user found, password_ok={ok}')
        else:
            print('DB check: USER NOT FOUND!')
