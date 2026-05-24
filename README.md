# NetStock — Cisco Inventory Management

Flask + MongoDB Atlas inventory system for managing Cisco networking equipment.

## Stack
- **Backend:** Python 3 / Flask
- **Database:** MongoDB Atlas (cloud)
- **Auth:** Flask-Login + Flask-Bcrypt
- **Frontend:** Bootstrap 5 + Chart.js

## Setup

```bash
pip install -r requirements.txt
# Create .env with MONGO_URI (see .env.example)
python run.py
```

## Login
- Email: `admin@netstock.app`
- Password: set via `reset_pass.py`

## Features
- Asset inventory with Red Line alerts
- Per-asset commission multiplier (×1.7 default)
- Sites, Tasks, Estimates, Contacts
- CSV exports, barcode scanner
- Hebrew / English UI
