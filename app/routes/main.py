import json
from datetime import date, timedelta, datetime

from flask import Blueprint, render_template, jsonify, redirect, request, session, url_for
from flask_login import login_required

from app.db import (
    assets_col, events_col, tasks_col, est_items_col, estimates_col,
    get_asset_type, all_settings, setting_set, setting_get,
    get_recent_events, _hydrate_asset,
)

main_bp = Blueprint('main', __name__)

_STATUS_COLORS = {
    'in_use': '#198754', 'dismantled': '#ffc107', 'in_storage': '#0dcaf0',
    'assigned': '#0d6efd', 'faulty': '#dc3545', 'retired': '#adb5bd',
}
_STATUS_LABELS = {
    'in_use': 'In Use', 'dismantled': 'Dismantled', 'in_storage': 'In Storage',
    'assigned': 'Assigned', 'faulty': 'Faulty', 'retired': 'Retired',
}


@main_bp.route('/api/mongo-health')
def mongo_health():
    from app.utils.mongo import ping_mongo
    if ping_mongo():
        return jsonify({'status': 'ok', 'message': 'החיבור למונגו עובד פיקס!'})
    return jsonify({'status': 'error', 'message': 'החיבור למונגו נכשל'}), 500


@main_bp.route('/set-lang/<code>')
def set_lang(code):
    if code in ('en', 'he'):
        session['lang'] = code
        session.permanent = True
    return redirect(request.referrer or url_for('main.dashboard'))


@main_bp.route('/api/rate')
@login_required
def exchange_rate():
    from app.utils.exchange import get_usd_to_nis
    rate = get_usd_to_nis()
    return jsonify({'rate': rate, 'base': 'USD', 'target': 'ILS'})


@main_bp.route('/api/settings', methods=['GET'])
@login_required
def get_settings():
    return jsonify(all_settings())


@main_bp.route('/api/settings', methods=['POST'])
@login_required
def save_settings():
    data = request.get_json(silent=True) or {}
    for key in ('usd_rate',):
        if key in data:
            try:
                setting_set(key, float(data[key]))
            except (ValueError, TypeError):
                pass
    return jsonify({'ok': True})


@main_bp.route('/')
@login_required
def dashboard():
    today = date.today()

    total_assets = assets_col().count_documents({})

    status_pipeline = [{'$group': {'_id': '$status', 'count': {'$sum': 1}}}]
    status_counts = {r['_id']: r['count'] for r in assets_col().aggregate(status_pipeline)}

    open_tasks_count = tasks_col().count_documents({'status': {'$ne': 'done'}})

    low_stock_docs = (
        assets_col()
        .find({
            'quantity': {'$ne': None},
            '$expr': {'$lte': ['$quantity', {'$ifNull': ['$min_threshold', 5]}]},
        })
        .sort('quantity', 1)
        .limit(20)
    )
    low_stock_assets = [_hydrate_asset(d) for d in low_stock_docs]

    recent_events = get_recent_events(limit=15)

    # ── Chart: assets by status ───────────────────────────────────────────────
    all_statuses = ['in_use', 'dismantled', 'in_storage', 'assigned', 'faulty', 'retired']
    status_chart = {
        'labels': [_STATUS_LABELS[s] for s in all_statuses],
        'data':   [status_counts.get(s, 0) for s in all_statuses],
        'colors': [_STATUS_COLORS[s] for s in all_statuses],
    }

    # ── Chart: top asset types ────────────────────────────────────────────────
    type_pipeline = [
        {'$group': {'_id': '$asset_type_id', 'count': {'$sum': 1}}},
        {'$sort': {'count': -1}},
        {'$limit': 8},
    ]
    type_chart_rows = []
    for row in assets_col().aggregate(type_pipeline):
        atype = get_asset_type(row['_id'])
        if atype:
            type_chart_rows.append((atype.name, row['count']))

    type_chart = {
        'labels': [r[0] for r in type_chart_rows],
        'data':   [r[1] for r in type_chart_rows],
    }

    # ── Chart: events per day — last 14 days ─────────────────────────────────
    activity_labels, activity_data = [], []
    for i in range(13, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end   = datetime.combine(day, datetime.max.time())
        count = events_col().count_documents({
            'event_date': {'$gte': day_start, '$lte': day_end},
        })
        activity_labels.append(day.strftime('%d %b'))
        activity_data.append(count)

    activity_chart = {'labels': activity_labels, 'data': activity_data}

    return render_template(
        'dashboard.html',
        total_assets=total_assets,
        status_counts=status_counts,
        recent_events=recent_events,
        open_tasks_count=open_tasks_count,
        low_stock_assets=low_stock_assets,
        today=today,
        status_chart=json.dumps(status_chart),
        type_chart=json.dumps(type_chart),
        activity_chart=json.dumps(activity_chart),
    )
