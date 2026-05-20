import csv
import io
import json
from datetime import date, timedelta, datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, Response
from flask_login import login_required, current_user
from bson import ObjectId

from app.db import (
    all_estimates, get_estimate, estimates_col, est_items_col,
    assets_col, all_assets, next_allocation_number, setting_get, all_settings,
    _hydrate_asset,
)

estimates_bp = Blueprint('estimates', __name__, url_prefix='/estimates')


@estimates_bp.route('/')
@login_required
def list_estimates():
    estimates = all_estimates({'status': 'pending'})
    return render_template('estimates/list.html', estimates=estimates)


@estimates_bp.route('/history')
@login_required
def history():
    estimates = all_estimates({'status': 'withdrawn'})
    return render_template('estimates/history.html', estimates=estimates)


@estimates_bp.route('/<id>/withdraw', methods=['POST'])
@login_required
def withdraw(id):
    estimate = get_estimate(id)
    if not estimate:
        abort(404)
    estimates_col().update_one({'_id': ObjectId(id)}, {'$set': {'status': 'withdrawn'}})
    flash(f'Assignment {estimate.allocation_number} marked as ongoing and moved to History.', 'success')
    return redirect(url_for('estimates.detail', id=id))


@estimates_bp.route('/<id>/restore', methods=['POST'])
@login_required
def restore(id):
    estimate = get_estimate(id)
    if not estimate:
        abort(404)
    estimates_col().update_one({'_id': ObjectId(id)}, {'$set': {'status': 'pending'}})
    flash(f'Assignment {estimate.allocation_number} restored to Pending.', 'success')
    return redirect(url_for('estimates.detail', id=id))


@estimates_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_estimate():
    usd_rate = setting_get('usd_rate') or 3.0
    today    = date.today()
    validity = today + timedelta(days=90)

    if request.method == 'POST':
        task_name    = (request.form.get('task_name') or '').strip()
        project_name = (request.form.get('project_name') or '').strip()
        items_raw    = request.form.get('items_json', '[]')

        if not task_name:
            flash('Task name is required.', 'danger')
            return redirect(url_for('estimates.new_estimate'))

        try:
            items_data = json.loads(items_raw)
        except (json.JSONDecodeError, TypeError):
            items_data = []

        est_result = estimates_col().insert_one({
            'allocation_number': next_allocation_number(),
            'task_name':         task_name,
            'project_name':      project_name or None,
            'status':            'pending',
            'created_date':      datetime.combine(today, datetime.min.time()),
            'valid_until':       datetime.combine(validity, datetime.min.time()),
            'usd_rate':          float(usd_rate),
            'created_by_id':     current_user.id,
            'created_at':        datetime.utcnow(),
        })
        est_id = str(est_result.inserted_id)

        total_nis = 0.0
        for item in items_data:
            asset_id = item.get('asset_id')
            qty      = max(1, int(item.get('quantity', 1)))
            doc = assets_col().find_one({'_id': ObjectId(asset_id)}) if asset_id else None
            if not doc or not doc.get('price_usd'):
                continue
            unit_usd = float(doc['price_usd'])
            line_nis = round(unit_usd * float(usd_rate) * 1.7 * 1.18 * qty, 2)
            total_nis += line_nis
            est_items_col().insert_one({
                'estimate_id':    est_id,
                'asset_id':       asset_id,
                'quantity':       qty,
                'unit_price_usd': unit_usd,
            })

        estimates_col().update_one(
            {'_id': ObjectId(est_id)},
            {'$set': {'total_nis': round(total_nis, 2)}},
        )
        flash(f'Estimate "{task_name}" saved successfully.', 'success')
        return redirect(url_for('estimates.list_estimates'))

    assets = [_hydrate_asset(d) for d in
              assets_col().find({'price_usd': {'$ne': None}}).sort('serial_number', 1)]
    assets_json = json.dumps([{
        'id':            a.id,
        'component_id':  a.component_id or '',
        'serial_number': a.serial_number,
        'model':         a.model or '',
        'manufacturer':  a.manufacturer or '',
        'type':          a.asset_type.name if a.asset_type else '',
        'price_usd':     float(a.price_usd),
        'quantity':      a.quantity if a.quantity is not None else 0,
    } for a in assets])

    return render_template('estimates/new.html',
                           assets_json=assets_json,
                           usd_rate=float(usd_rate),
                           today=today,
                           valid_until=validity)


@estimates_bp.route('/<id>')
@login_required
def detail(id):
    estimate = get_estimate(id)
    if not estimate:
        abort(404)
    return render_template('estimates/detail.html', estimate=estimate)


@estimates_bp.route('/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    estimate = get_estimate(id)
    if not estimate:
        abort(404)
    usd_rate = float(estimate.usd_rate)

    if request.method == 'POST':
        task_name    = (request.form.get('task_name') or '').strip()
        project_name = (request.form.get('project_name') or '').strip()
        items_raw    = request.form.get('items_json', '[]')

        if not task_name:
            flash('Requester name is required.', 'danger')
            return redirect(url_for('estimates.edit', id=id))

        try:
            items_data = json.loads(items_raw)
        except (json.JSONDecodeError, TypeError):
            items_data = []

        est_items_col().delete_many({'estimate_id': id})

        total_nis = 0.0
        for item in items_data:
            asset_id = item.get('asset_id')
            qty      = max(1, int(item.get('quantity', 1)))
            doc = assets_col().find_one({'_id': ObjectId(asset_id)}) if asset_id else None
            if not doc or not doc.get('price_usd'):
                continue
            unit_usd = float(doc['price_usd'])
            line_nis = round(unit_usd * usd_rate * 1.7 * 1.18 * qty, 2)
            total_nis += line_nis
            est_items_col().insert_one({
                'estimate_id':    id,
                'asset_id':       asset_id,
                'quantity':       qty,
                'unit_price_usd': unit_usd,
            })

        estimates_col().update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'task_name':    task_name,
                'project_name': project_name or None,
                'total_nis':    round(total_nis, 2),
            }},
        )
        flash('Estimate updated successfully.', 'success')
        return redirect(url_for('estimates.detail', id=id))

    assets = [_hydrate_asset(d) for d in
              assets_col().find({'price_usd': {'$ne': None}}).sort('serial_number', 1)]
    assets_json = json.dumps([{
        'id':            a.id,
        'component_id':  a.component_id or '',
        'serial_number': a.serial_number,
        'model':         a.model or '',
        'manufacturer':  a.manufacturer or '',
        'type':          a.asset_type.name if a.asset_type else '',
        'price_usd':     float(a.price_usd),
        'quantity':      a.quantity if a.quantity is not None else 0,
    } for a in assets])

    selected_json = json.dumps([{
        'asset_id': item.asset_id,
        'quantity': item.quantity,
    } for item in estimate.items])

    return render_template('estimates/edit.html',
                           estimate=estimate,
                           assets_json=assets_json,
                           selected_json=selected_json,
                           usd_rate=usd_rate)


@estimates_bp.route('/<id>/export.csv')
@login_required
def export_csv(id):
    estimate = get_estimate(id)
    if not estimate:
        abort(404)
    buf = io.StringIO()
    w = csv.writer(buf)
    created = estimate.created_date
    valid   = estimate.valid_until
    w.writerow(['Allocation Number', estimate.allocation_number or ''])
    w.writerow(['Requester Name',    estimate.task_name])
    w.writerow(['Project',           estimate.project_name or ''])
    w.writerow(['Date',       created.strftime('%d %b %Y') if created else ''])
    w.writerow(['Valid Until', valid.strftime('%d %b %Y')   if valid   else ''])
    w.writerow([])
    w.writerow(['Part No.', 'Description', 'Type', 'Qty',
                'Unit Price (USD)', 'Unit Price (ILS)', 'Line Total (ILS)'])
    rate = float(estimate.usd_rate)
    for item in estimate.items:
        unit_usd = float(item.unit_price_usd) if item.unit_price_usd else 0.0
        unit_ils = round(unit_usd * rate * 1.7 * 1.18, 2)
        line_ils = round(unit_ils * item.quantity, 2)
        w.writerow([
            item.asset.serial_number if item.asset else '',
            item.asset.model         if item.asset else '',
            item.asset.asset_type.name if item.asset and item.asset.asset_type else '',
            item.quantity,
            f'{unit_usd:.2f}',
            f'{unit_ils:.2f}',
            f'{line_ils:.2f}',
        ])
    w.writerow([])
    w.writerow(['', '', '', '', '', 'TOTAL (ILS)',
                estimate.formatted_total.replace(' ₪', '')])
    task_name = estimate.task_name or 'estimate'
    created_str = created.strftime('%Y-%m-%d') if created else 'unknown'
    filename = f"estimate_{task_name.replace(' ', '_')}_{created_str}.csv"
    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'},
    )


@estimates_bp.route('/<id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.is_admin:
        abort(403)
    estimate = get_estimate(id)
    if not estimate:
        abort(404)
    name = estimate.task_name
    est_items_col().delete_many({'estimate_id': id})
    estimates_col().delete_one({'_id': ObjectId(id)})
    flash(f'Estimate "{name}" deleted.', 'info')
    return redirect(url_for('estimates.list_estimates'))
