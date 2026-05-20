"""מייבא את קטלוג הציוד מ-seed_inventory.py ל-MongoDB Atlas."""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from app import create_app
app = create_app()

INVENTORY = [
    dict(serial_number='C8300-1N1S-4T2X',     model='C8300-1N1S-4T2X',     asset_type='Router',         manufacturer='Cisco'),
    dict(serial_number='C8500L-8S4X',          model='C8500L-8S4X',          asset_type='Router',         manufacturer='Cisco'),
    dict(serial_number='C1111X-8P',            model='C1111X-8P',            asset_type='Router',         manufacturer='Cisco'),
    dict(serial_number='C1161X-8P',            model='C1161X-8P',            asset_type='Router',         manufacturer='Cisco'),
    dict(serial_number='ASR1001-X',            model='ASR1001-X',            asset_type='Router',         manufacturer='Cisco'),
    dict(serial_number='ASR1001-HX',           model='ASR1001-HX',           asset_type='Router',         manufacturer='Cisco'),
    dict(serial_number='ISR 4331AX/K9',        model='ISR 4331AX/K9',        asset_type='Router',         manufacturer='Cisco'),
    dict(serial_number='ISR 4331-DC/K9',       model='ISR 4331-DC/K9',       asset_type='Router',         manufacturer='Cisco'),
    dict(serial_number='ISR 4321',             model='ISR 4321',             asset_type='Router',         manufacturer='Cisco'),
    dict(serial_number='ASR-1009X',            model='ASR-1009X',            asset_type='Router',         manufacturer='Cisco'),
    dict(serial_number='NB-VC-3400-P-RTR-C',  model='NB-VC-3400-P-RTR-C',  asset_type='Router',         manufacturer='Dell'),
    dict(serial_number='C9300-24S-A',          model='C9300-24S-A',          asset_type='Aggregation',    manufacturer='Cisco'),
    dict(serial_number='C9300-48S-A',          model='C9300-48S-A',          asset_type='Aggregation',    manufacturer='Cisco'),
    dict(serial_number='C9500-24Y4C-A',        model='C9500-24Y4C-A',        asset_type='Aggregation',    manufacturer='Cisco'),
    dict(serial_number='C9500-48Y4C-A',        model='C9500-48Y4C-A',        asset_type='Aggregation',    manufacturer='Cisco'),
    dict(serial_number='C9300X-12Y-A',         model='C9300X-12Y-A',         asset_type='Aggregation',    manufacturer='Cisco'),
    dict(serial_number='C9300-24P-A',          model='C9300-24P-A',          asset_type='Access Switch',  manufacturer='Cisco'),
    dict(serial_number='C9300-48P-A',          model='C9300-48P-A',          asset_type='Access Switch',  manufacturer='Cisco'),
    dict(serial_number='C9200CX-12P-2X2G-A',  model='C9200CX-12P-2X2G-A',  asset_type='Access Switch',  manufacturer='Cisco'),
    dict(serial_number='MS-390-48-HW',         model='MS-390-48-HW',         asset_type='Access Switch',  manufacturer='Cisco Meraki'),
    dict(serial_number='C1100TG-1N24P32A',     model='C1100TG-1N24P32A',     asset_type='Access Switch',  manufacturer='Cisco'),
    dict(serial_number='GLC-LH-SMD',           model='GLC-LH-SMD',           asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='SFP-1G-LH',            model='SFP-1G-LH',            asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='GLC-SX-MMD',           model='GLC-SX-MMD',           asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='GLC-SX-MM',            model='GLC-SX-MM',            asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='SFP-10G-LR-S',         model='SFP-10G-LR-S',         asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='SFP-10G-SR-S',         model='SFP-10G-SR-S',         asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='SFP-10G-SR',           model='SFP-10G-SR',           asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='GLC-BX-D',             model='GLC-BX-D',             asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='GLC-BX-U',             model='GLC-BX-U',             asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='GLC-TE',               model='GLC-TE',               asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='SFP-1G-T-X',           model='SFP-1G-T-X',           asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='SFP-10G-T-X',          model='SFP-10G-T-X',          asset_type='SFP',            manufacturer='Cisco'),
    dict(serial_number='C-NIM-4X',             model='C-NIM-4X',             asset_type='Cards',          manufacturer='Cisco'),
    dict(serial_number='C-NIM-1X',             model='C-NIM-1X',             asset_type='Cards',          manufacturer='Cisco'),
    dict(serial_number='C-NIM-2T',             model='C-NIM-2T',             asset_type='Cards',          manufacturer='Cisco'),
    dict(serial_number='C-NIM-SM-ADPT',        model='C-NIM-SM-ADPT',        asset_type='Cards',          manufacturer='Cisco'),
    dict(serial_number='ASR-MIP100',           model='ASR-MIP100',           asset_type='Cards',          manufacturer='Cisco'),
    dict(serial_number='EPA 10X10GE',          model='EPA 10X10GE',          asset_type='Cards',          manufacturer='Cisco'),
    dict(serial_number='EPA 18X1GE',           model='EPA 18X1GE',           asset_type='Cards',          manufacturer='Cisco'),
    dict(serial_number='SPA 8X1GE',            model='SPA 8X1GE',            asset_type='Cards',          manufacturer='Cisco'),
    dict(serial_number='NIM-2GE-CU-SFP',       model='NIM-2GE-CU-SFP',       asset_type='Cards',          manufacturer='Cisco'),
    dict(serial_number='MA-MOD-8X10G',         model='MA-MOD-8X10G',         asset_type='Cards',          manufacturer='Cisco Meraki'),
    dict(serial_number='C9300-NM-8X',          model='C9300-NM-8X',          asset_type='Cards',          manufacturer='Cisco'),
    dict(serial_number='PWR-C1-715WAC-P',      model='PWR-C1-715WAC-P',      asset_type='Power Supply',   manufacturer='Cisco'),
    dict(serial_number='PWR-C1-715WDC-P',      model='PWR-C1-715WDC-P',      asset_type='Power Supply',   manufacturer='Cisco'),
    dict(serial_number='C9K-PWR-930WDC-R',     model='C9K-PWR-930WDC-R',     asset_type='Power Supply',   manufacturer='Cisco'),
    dict(serial_number='PWR-CC1-400WDC',       model='PWR-CC1-400WDC',       asset_type='Power Supply',   manufacturer='Cisco'),
    dict(serial_number='MA-PWR-350WAC',        model='MA-PWR-350WAC',        asset_type='Power Supply',   manufacturer='Cisco Meraki'),
    dict(serial_number='CAB-48DC-40A-8AWG',    model='CAB-48DC-40A-8AWG',    asset_type='Power Cords',    manufacturer='Cisco'),
    dict(serial_number='CAB-C15-CBN',          model='CAB-C15-CBN',          asset_type='Power Cords',    manufacturer='Cisco'),
    dict(serial_number='CAB-C19-CBN',          model='CAB-C19-CBN',          asset_type='Power Cords',    manufacturer='Cisco'),
    dict(serial_number='CAB-TA-IS',            model='CAB-TA-IS',            asset_type='Power Cords',    manufacturer='Cisco'),
    dict(serial_number='CAB-C15-ISR',          model='CAB-C15-ISR',          asset_type='Power Cords',    manufacturer='Cisco'),
    dict(serial_number='CAB-C13-CBN',          model='CAB-C13-CBN',          asset_type='Power Cords',    manufacturer='Cisco'),
    dict(serial_number='CAB-C13-C14-2M',       model='CAB-C13-C14-2M',       asset_type='Power Cords',    manufacturer='Cisco'),
    dict(serial_number='CAB-TA-EU',            model='CAB-TA-EU',            asset_type='Power Cords',    manufacturer='Cisco'),
    dict(serial_number='PWR-CAB-AC-BLK',       model='PWR-CAB-AC-BLK',       asset_type='Power Cords',    manufacturer='Cisco'),
    dict(serial_number='CAB-CONSOLE-USBRJ45',  model='CAB-CONSOLE-USBRJ45',  asset_type='Console Cables', manufacturer='Cisco'),
    dict(serial_number='CAB-CONSOLE-RJ45',     model='CAB-CONSOLE-RJ45',     asset_type='Console Cables', manufacturer='Cisco'),
    dict(serial_number='CAB-CONSOLE-USB',      model='CAB-CONSOLE-USB',      asset_type='Console Cables', manufacturer='Cisco'),
]

TYPE_CATEGORIES = {
    'Router':         'Networking',
    'Aggregation':    'Networking',
    'Access Switch':  'Networking',
    'SFP':            'Networking',
    'Cards':          'Networking',
    'Power Supply':   'Power',
    'Power Cords':    'Power',
    'Console Cables': 'Cabling',
}

with app.app_context():
    from app.db import assets_col, asset_types_col, sites_col
    from datetime import datetime

    # ── וודא שכל סוגי הציוד קיימים ──────────────────────────────────────────
    type_id_map = {}
    for type_name, category in TYPE_CATEGORIES.items():
        doc = asset_types_col().find_one({'name': type_name})
        if not doc:
            res = asset_types_col().insert_one({'name': type_name, 'category': category})
            doc = asset_types_col().find_one({'_id': res.inserted_id})
            print(f'  Created asset type: {type_name}')
        type_id_map[type_name] = str(doc['_id'])

    # ── וודא שה-site "Kodkod Base" קיים ──────────────────────────────────────
    site_doc = sites_col().find_one({'name': 'Kodkod Base'})
    if not site_doc:
        res = sites_col().insert_one({'name': 'Kodkod Base', 'address': None, 'notes': None})
        site_doc = sites_col().find_one({'_id': res.inserted_id})
        print('  Created site: Kodkod Base')
    site_id = str(site_doc['_id'])

    # ── ייבוא הציוד ──────────────────────────────────────────────────────────
    inserted = skipped = 0
    for item in INVENTORY:
        if assets_col().find_one({'serial_number': item['serial_number']}):
            skipped += 1
            continue
        assets_col().insert_one({
            'serial_number':  item['serial_number'],
            'model':          item['model'],
            'manufacturer':   item['manufacturer'],
            'asset_type_id':  type_id_map[item['asset_type']],
            'current_site_id': site_id,
            'status':         'in_storage',
            'created_at':     datetime.utcnow(),
            'updated_at':     datetime.utcnow(),
        })
        print(f'  + {item["serial_number"]:35s} ({item["asset_type"]})')
        inserted += 1

    total = assets_col().count_documents({})
    print(f'\nSummary: inserted={inserted}, skipped={skipped}')
    print(f'Total assets in MongoDB Atlas: {total}')
