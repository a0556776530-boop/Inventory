"""Adds price, stock qty and min_threshold to the 62 Cisco items in Atlas."""
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

from app import create_app
app = create_app()

# price_usd, quantity, min_threshold
ITEM_DATA = {
    # Routers
    'C8300-1N1S-4T2X':    (3500,  4, 2),
    'C8500L-8S4X':        (8500,  3, 1),
    'C1111X-8P':          (1200,  6, 2),
    'C1161X-8P':          (1500,  5, 2),
    'ASR1001-X':          (12000, 2, 1),
    'ASR1001-HX':         (18000, 2, 1),
    'ISR 4331AX/K9':      (2800,  4, 2),
    'ISR 4331-DC/K9':     (3000,  3, 1),
    'ISR 4321':           (1800,  5, 2),
    'ASR-1009X':          (35000, 1, 1),
    'NB-VC-3400-P-RTR-C': (4200,  2, 1),
    # Aggregation
    'C9300-24S-A':        (4500,  5, 2),
    'C9300-48S-A':        (6800,  4, 2),
    'C9500-24Y4C-A':      (15000, 3, 1),
    'C9500-48Y4C-A':      (22000, 2, 1),
    'C9300X-12Y-A':       (9500,  3, 1),
    # Access Switches
    'C9300-24P-A':        (3200,  8, 3),
    'C9300-48P-A':        (4800,  6, 2),
    'C9200CX-12P-2X2G-A': (1800,  7, 3),
    'MS-390-48-HW':       (5500,  4, 2),
    'C1100TG-1N24P32A':   (2200,  5, 2),
    # SFP
    'GLC-LH-SMD':         (95,   30, 10),
    'SFP-1G-LH':          (110,  25, 10),
    'GLC-SX-MMD':         (75,   40, 15),
    'GLC-SX-MM':          (65,   35, 15),
    'SFP-10G-LR-S':       (185,  20, 8),
    'SFP-10G-SR-S':       (160,  25, 10),
    'SFP-10G-SR':         (145,  30, 10),
    'GLC-BX-D':           (130,  15, 5),
    'GLC-BX-U':           (130,  15, 5),
    'GLC-TE':             (55,   50, 20),
    'SFP-1G-T-X':         (85,   20, 8),
    'SFP-10G-T-X':        (195,  12, 5),
    # Cards
    'C-NIM-4X':           (850,   6, 2),
    'C-NIM-1X':           (450,   8, 3),
    'C-NIM-2T':           (620,   5, 2),
    'C-NIM-SM-ADPT':      (380,   7, 2),
    'ASR-MIP100':         (2200,  3, 1),
    'EPA 10X10GE':        (4500,  2, 1),
    'EPA 18X1GE':         (3800,  3, 1),
    'SPA 8X1GE':          (2800,  4, 2),
    'NIM-2GE-CU-SFP':     (550,   6, 2),
    'MA-MOD-8X10G':       (1800,  4, 2),
    'C9300-NM-8X':        (1200,  5, 2),
    # Power Supply
    'PWR-C1-715WAC-P':    (450,  10, 4),
    'PWR-C1-715WDC-P':    (520,   8, 3),
    'C9K-PWR-930WDC-R':   (680,   6, 2),
    'PWR-CC1-400WDC':     (380,   8, 3),
    'MA-PWR-350WAC':      (320,   9, 3),
    # Power Cords
    'CAB-48DC-40A-8AWG':  (45,   15, 5),
    'CAB-C15-CBN':        (25,   30, 10),
    'CAB-C19-CBN':        (28,   25, 10),
    'CAB-TA-IS':          (22,   20, 8),
    'CAB-C15-ISR':        (24,   20, 8),
    'CAB-C13-CBN':        (20,   35, 12),
    'CAB-C13-C14-2M':     (18,   30, 10),
    'CAB-TA-EU':          (22,   15, 5),
    'PWR-CAB-AC-BLK':     (30,   20, 8),
    # Console Cables
    'CAB-CONSOLE-USBRJ45':(28,   20, 8),
    'CAB-CONSOLE-RJ45':   (22,   25, 10),
    'CAB-CONSOLE-USB':    (25,   15, 6),
}

with app.app_context():
    from app.db import assets_col

    updated = skipped = 0
    for sn, (price, qty, threshold) in ITEM_DATA.items():
        result = assets_col().update_one(
            {'serial_number': sn},
            {'$set': {
                'price_usd':     float(price),
                'quantity':      qty,
                'min_threshold': threshold,
            }},
        )
        if result.matched_count:
            updated += 1
        else:
            print(f'  NOT FOUND: {sn}')
            skipped += 1

    total = assets_col().count_documents({})
    print(f'Updated: {updated}  |  Not found: {skipped}  |  Total assets: {total}')

    # Verify a sample
    sample = assets_col().find_one({'serial_number': 'GLC-LH-SMD'})
    if sample:
        print(f'\nSample — GLC-LH-SMD:')
        print(f'  price_usd={sample.get("price_usd")}  qty={sample.get("quantity")}  min_threshold={sample.get("min_threshold")}')
