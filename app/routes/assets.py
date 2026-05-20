import json
import re
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, g
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField, DecimalField, IntegerField
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from collections import defaultdict
from bson import ObjectId

from app.db import (
    all_assets, get_asset, assets_col, all_sites, all_users, all_asset_types,
    get_site, get_user, get_asset_events, est_items_col, estimates_col, all_settings,
)
from app.utils.events import log_event
from app.utils.translations import localize_form

assets_bp = Blueprint('assets', __name__, url_prefix='/assets')

CATEGORY_ORDER = [
    'Router', 'Aggregation', 'Access Switch', 'SFP', 'Cards',
    'Power Supply', 'Power Cords', 'Console Cables',
]
CATEGORY_LABELS = {
    'Router': 'Routers', 'Aggregation': 'Aggregation',
    'Access Switch': 'Access Switches', 'SFP': 'SFP Modules',
    'Cards': 'Cards & Modules', 'Power Supply': 'Power Supplies',
    'Power Cords': 'Power Cords', 'Console Cables': 'Console Cables',
}


def _site_choices():
    return [('', '— None —')] + [(s.id, s.name) for s in all_sites()]


def _user_choices():
    return [('', '— None —')] + [(u.id, u.name) for u in all_users()]


def _type_choices():
    return [(t.id, f'{t.name} ({t.category})') for t in all_asset_types()]


class AssetForm(FlaskForm):
    component_id   = StringField('Asset ID',      validators=[Optional(), Length(max=50)])
    serial_number  = StringField('Mfr. Part No.', validators=[DataRequired(), Length(max=100)])
    barcode        = StringField('Barcode',        validators=[Optional(), Length(max=100)])
    asset_type_id  = SelectField('Asset Type',    coerce=str, validators=[DataRequired()])
    model          = StringField('Description',   validators=[Optional(), Length(max=150)])
    manufacturer   = StringField('Manufacturer',  validators=[Optional(), Length(max=150)])
    status = SelectField('Status', choices=[
        ('in_storage', 'In Storage'), ('in_use', 'In Use'), ('dismantled', 'Dismantled'),
        ('assigned', 'Assigned'), ('faulty', 'Faulty'), ('retired', 'Retired'),
    ])
    current_site_id = SelectField('Current Site', coerce=str, validators=[Optional()])
    assigned_to_id  = SelectField('Assigned To',  coerce=str, validators=[Optional()])
    notes      = TextAreaField('Notes',        validators=[Optional()])
    price_usd  = DecimalField('Price USD ($)', validators=[Optional(), NumberRange(min=0)], places=0)
    price_nis  = DecimalField('Price NIS (₪)', validators=[Optional(), NumberRange(min=0)], places=0)
    quantity      = IntegerField('Stock Qty',    validators=[Optional(), NumberRange(min=0)])
    min_threshold = IntegerField('Min Threshold', validators=[Optional(), NumberRange(min=0)])
    submit        = SubmitField('Save Asset')

    def populate_choices(self):
        self.asset_type_id.choices  = _type_choices()
        self.current_site_id.choices = _site_choices()
        self.assigned_to_id.choices  = _user_choices()


class DismantleForm(FlaskForm):
    from_site_id = SelectField('Dismantled From', coerce=str, validators=[Optional()])
    notes  = TextAreaField('Notes',  validators=[Optional()])
    submit = SubmitField('Confirm Dismantle')

    def populate_choices(self):
        self.from_site_id.choices = _site_choices()


class AssignForm(FlaskForm):
    assigned_to_id = SelectField('Assign To',      coerce=str, validators=[DataRequired()])
    to_site_id     = SelectField('Deploy to Site', coerce=str, validators=[Optional()])
    notes  = TextAreaField('Notes',  validators=[Optional()])
    submit = SubmitField('Confirm Assignment')

    def populate_choices(self):
        self.assigned_to_id.choices = [(u.id, u.name) for u in all_users()]
        self.to_site_id.choices     = _site_choices()


class MoveForm(FlaskForm):
    to_site_id = SelectField('Move to Site', coerce=str, validators=[DataRequired()])
    notes  = TextAreaField('Notes',  validators=[Optional()])
    submit = SubmitField('Confirm Move')

    def populate_choices(self):
        self.to_site_id.choices = [(s.id, s.name) for s in all_sites()]


class ReturnForm(FlaskForm):
    to_site_id = SelectField('Return to Site (Storage)', coerce=str, validators=[Optional()])
    notes  = TextAreaField('Notes',  validators=[Optional()])
    submit = SubmitField('Confirm Return')

    def populate_choices(self):
        self.to_site_id.choices = _site_choices()


class RetireForm(FlaskForm):
    submit = SubmitField('Retire Asset')


# ── List ──────────────────────────────────────────────────────────────────────

@assets_bp.route('/')
@login_required
def list_assets():
    q             = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '')
    type_filter   = request.args.get('type',   '')
    site_filter   = request.args.get('site',   '')
    sort          = request.args.get('sort',  'created_at')
    order         = request.args.get('order', 'desc')

    mongo_query = {}
    if q:
        regex = re.compile(re.escape(q), re.IGNORECASE)
        mongo_query['$or'] = [
            {'serial_number': regex}, {'model': regex}, {'component_id': regex},
        ]
    if status_filter:
        mongo_query['status'] = status_filter
    if type_filter:
        mongo_query['asset_type_id'] = type_filter
    if site_filter:
        mongo_query['current_site_id'] = site_filter

    sort_order = 1 if order == 'asc' else -1
    sort_field = sort if sort in ('component_id', 'serial_number', 'status',
                                  'created_at', 'price_usd', 'price_nis', 'quantity') else 'created_at'
    assets = all_assets(mongo_query, sort_field=sort_field, sort_order=sort_order)

    by_type = defaultdict(list)
    for asset in assets:
        by_type[asset.asset_type.name if asset.asset_type else 'Other'].append(asset)

    grouped_assets, seen = [], set()
    for cat in CATEGORY_ORDER:
        if cat in by_type:
            grouped_assets.append((CATEGORY_LABELS.get(cat, cat), by_type[cat]))
            seen.add(cat)
    for cat, items in by_type.items():
        if cat not in seen:
            grouped_assets.append((cat, items))

    all_types = all_asset_types()
    asset_types = sorted(
        all_types,
        key=lambda t: CATEGORY_ORDER.index(t.name) if t.name in CATEGORY_ORDER else len(CATEGORY_ORDER),
    )
    sites = all_sites()
    global_settings = json.dumps(all_settings())

    # Commitments: pending estimate items per asset
    pending_est_ids = [str(d['_id']) for d in estimates_col().find({'status': 'pending'}, {'_id': 1})]
    commitment_pipeline = [
        {'$match': {'estimate_id': {'$in': pending_est_ids}}},
        {'$group': {'_id': '$asset_id', 'total': {'$sum': '$quantity'}}},
    ]
    commitments = {r['_id']: r['total'] for r in est_items_col().aggregate(commitment_pipeline)}

    return render_template(
        'assets/list.html',
        assets=assets, grouped_assets=grouped_assets,
        asset_types=asset_types, sites=sites,
        q=q, status_filter=status_filter, type_filter=type_filter,
        site_filter=site_filter, sort=sort, order=order,
        global_settings=global_settings, commitments=commitments,
    )


# ── Create ────────────────────────────────────────────────────────────────────

@assets_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_asset():
    if not current_user.can_edit:
        abort(403)
    t = getattr(g, 't', {})
    form = AssetForm()
    form.populate_choices()
    localize_form(form, t, submit_key='form_save_asset')

    if request.method == 'GET':
        prefill = request.args.get('serial', '').strip().upper()
        if prefill:
            form.serial_number.data = prefill

    if form.validate_on_submit():
        sn = form.serial_number.data.strip().upper()
        if assets_col().find_one({'serial_number': sn}):
            existing = get_asset(str(assets_col().find_one({'serial_number': sn})['_id']))
            flash(
                t.get('flash_asset_duplicate',
                      'Model already registered: <a href="{url}">{sn}</a>').format(
                    url=url_for('assets.detail', id=existing.id), sn=sn),
                'danger',
            )
        else:
            result = assets_col().insert_one({
                'component_id':   (form.component_id.data or '').strip() or None,
                'serial_number':  sn,
                'barcode':        (form.barcode.data or '').strip() or None,
                'asset_type_id':  form.asset_type_id.data or None,
                'model':          (form.model.data or '').strip() or None,
                'manufacturer':   (form.manufacturer.data or '').strip() or None,
                'status':         'in_storage',
                'current_site_id': None,
                'assigned_to_id':  None,
                'notes':          (form.notes.data or '').strip() or None,
                'price_usd':      float(form.price_usd.data) if form.price_usd.data is not None else None,
                'price_nis':      float(form.price_nis.data) if form.price_nis.data is not None else None,
                'quantity':       form.quantity.data,
                'min_threshold':  form.min_threshold.data,
                'created_at':     datetime.utcnow(),
                'updated_at':     datetime.utcnow(),
            })
            asset = get_asset(str(result.inserted_id))
            log_event(asset, 'created', current_user,
                      notes=f'Asset registered. Status: {asset.status_label}')
            flash(t.get('flash_asset_created', '{sn} registered successfully.').format(
                sn=asset.serial_number), 'success')
            return redirect(url_for('assets.detail', id=asset.id))

    return render_template('assets/form.html', form=form, asset=None,
                           title=t.get('form_title_register_asset', 'Register New Asset'))


# ── Detail ────────────────────────────────────────────────────────────────────

@assets_bp.route('/<id>')
@login_required
def detail(id):
    t = getattr(g, 't', {})
    asset = get_asset(id)
    if not asset:
        abort(404)
    events = get_asset_events(id)

    dismantle_form = DismantleForm(prefix='dismantle')
    dismantle_form.populate_choices()
    if asset.current_site_id:
        dismantle_form.from_site_id.data = asset.current_site_id
    localize_form(dismantle_form, t, submit_key='form_confirm_dismantle')

    assign_form = AssignForm(prefix='assign')
    assign_form.populate_choices()
    localize_form(assign_form, t, submit_key='form_confirm_assignment',
                  extra={'to_site_id': 'form_deploy_to_site'})

    move_form = MoveForm(prefix='move')
    move_form.populate_choices()
    localize_form(move_form, t, submit_key='form_confirm_move',
                  extra={'to_site_id': 'form_move_to_site'})

    return_form = ReturnForm(prefix='ret')
    return_form.populate_choices()
    localize_form(return_form, t, submit_key='form_confirm_return',
                  extra={'to_site_id': 'form_return_to_site'})

    retire_form = RetireForm(prefix='retire')
    localize_form(retire_form, t, submit_key='form_retire_asset')

    return render_template(
        'assets/detail.html',
        asset=asset, events=events,
        dismantle_form=dismantle_form, assign_form=assign_form,
        move_form=move_form, return_form=return_form, retire_form=retire_form,
    )


# ── Edit ──────────────────────────────────────────────────────────────────────

@assets_bp.route('/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not current_user.can_edit:
        abort(403)
    t = getattr(g, 't', {})
    asset = get_asset(id)
    if not asset:
        abort(404)
    form = AssetForm(obj=asset)
    form.populate_choices()
    localize_form(form, t, submit_key='form_save_asset')

    if form.validate_on_submit():
        assets_col().update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'component_id':  (form.component_id.data or '').strip() or None,
                'serial_number': form.serial_number.data.strip().upper(),
                'barcode':       (form.barcode.data or '').strip() or None,
                'asset_type_id': form.asset_type_id.data or None,
                'model':         (form.model.data or '').strip() or None,
                'manufacturer':  (form.manufacturer.data or '').strip() or None,
                'notes':         (form.notes.data or '').strip() or None,
                'price_usd':     float(form.price_usd.data) if form.price_usd.data is not None else None,
                'price_nis':     float(form.price_nis.data) if form.price_nis.data is not None else None,
                'quantity':      form.quantity.data,
                'min_threshold': form.min_threshold.data,
                'updated_at':    datetime.utcnow(),
            }},
        )
        flash(t.get('flash_asset_updated', 'Asset updated successfully.'), 'success')
        return redirect(url_for('assets.list_assets'))

    return render_template('assets/form.html', form=form, asset=asset,
                           title=t.get('form_title_edit_asset', 'Edit Asset'))


# ── Actions ───────────────────────────────────────────────────────────────────

@assets_bp.route('/<id>/dismantle', methods=['POST'])
@login_required
def dismantle(id):
    if not current_user.can_edit:
        abort(403)
    t = getattr(g, 't', {})
    asset = get_asset(id)
    if not asset:
        abort(404)
    form = DismantleForm(prefix='dismantle')
    form.populate_choices()
    if form.validate_on_submit():
        from_site = get_site(form.from_site_id.data) if form.from_site_id.data else asset.current_site
        assets_col().update_one(
            {'_id': ObjectId(id)},
            {'$set': {'status': 'dismantled', 'assigned_to_id': None,
                      'current_site_id': None, 'updated_at': datetime.utcnow()}},
        )
        asset = get_asset(id)
        log_event(asset, 'dismantled', current_user,
                  from_site=from_site,
                  notes=(form.notes.data or '').strip() or None)
        flash(t.get('flash_dismantled', '{sn} marked as dismantled.').format(
            sn=asset.serial_number), 'warning')
    else:
        flash(t.get('flash_form_error', 'Form error. Please try again.'), 'danger')
    return redirect(url_for('assets.detail', id=id))


@assets_bp.route('/<id>/assign', methods=['POST'])
@login_required
def assign(id):
    if not current_user.can_edit:
        abort(403)
    t = getattr(g, 't', {})
    asset = get_asset(id)
    if not asset:
        abort(404)
    form = AssignForm(prefix='assign')
    form.populate_choices()
    if form.validate_on_submit():
        to_site   = get_site(form.to_site_id.data) if form.to_site_id.data else None
        prev_site = asset.current_site
        update = {
            'status': 'assigned',
            'assigned_to_id': form.assigned_to_id.data,
            'updated_at': datetime.utcnow(),
        }
        if to_site:
            update['current_site_id'] = to_site.id
        assets_col().update_one({'_id': ObjectId(id)}, {'$set': update})
        asset = get_asset(id)
        log_event(asset, 'assigned', current_user, from_site=prev_site, to_site=to_site,
                  notes=(form.notes.data or '').strip() or None)
        flash(t.get('flash_assigned', '{sn} assigned successfully.').format(
            sn=asset.serial_number), 'success')
    else:
        flash(t.get('flash_form_error', 'Form error. Please try again.'), 'danger')
    return redirect(url_for('assets.detail', id=id))


@assets_bp.route('/<id>/move', methods=['POST'])
@login_required
def move(id):
    if not current_user.can_edit:
        abort(403)
    t = getattr(g, 't', {})
    asset = get_asset(id)
    if not asset:
        abort(404)
    form = MoveForm(prefix='move')
    form.populate_choices()
    if form.validate_on_submit():
        to_site   = get_site(form.to_site_id.data)
        prev_site = asset.current_site
        assets_col().update_one(
            {'_id': ObjectId(id)},
            {'$set': {'current_site_id': to_site.id, 'updated_at': datetime.utcnow()}},
        )
        asset = get_asset(id)
        log_event(asset, 'moved', current_user, from_site=prev_site, to_site=to_site,
                  notes=(form.notes.data or '').strip() or None)
        flash(t.get('flash_moved', '{sn} moved to {site}.').format(
            sn=asset.serial_number, site=to_site.name), 'success')
    else:
        flash(t.get('flash_form_error', 'Form error. Please try again.'), 'danger')
    return redirect(url_for('assets.detail', id=id))


@assets_bp.route('/<id>/return', methods=['POST'])
@login_required
def return_asset(id):
    if not current_user.can_edit:
        abort(403)
    t = getattr(g, 't', {})
    asset = get_asset(id)
    if not asset:
        abort(404)
    form = ReturnForm(prefix='ret')
    form.populate_choices()
    if form.validate_on_submit():
        to_site   = get_site(form.to_site_id.data) if form.to_site_id.data else None
        prev_site = asset.current_site
        update = {
            'status': 'in_storage', 'assigned_to_id': None, 'updated_at': datetime.utcnow(),
        }
        if to_site:
            update['current_site_id'] = to_site.id
        assets_col().update_one({'_id': ObjectId(id)}, {'$set': update})
        asset = get_asset(id)
        log_event(asset, 'returned', current_user, from_site=prev_site, to_site=to_site,
                  notes=(form.notes.data or '').strip() or None)
        flash(t.get('flash_returned', '{sn} returned to storage.').format(
            sn=asset.serial_number), 'info')
    else:
        flash(t.get('flash_form_error', 'Form error. Please try again.'), 'danger')
    return redirect(url_for('assets.detail', id=id))


@assets_bp.route('/<id>/retire', methods=['POST'])
@login_required
def retire(id):
    if not current_user.can_edit:
        abort(403)
    t = getattr(g, 't', {})
    asset = get_asset(id)
    if not asset:
        abort(404)
    assets_col().update_one(
        {'_id': ObjectId(id)},
        {'$set': {'status': 'retired', 'assigned_to_id': None, 'updated_at': datetime.utcnow()}},
    )
    asset = get_asset(id)
    log_event(asset, 'retired', current_user)
    flash(t.get('flash_retired', '{sn} retired from service.').format(
        sn=asset.serial_number), 'secondary')
    return redirect(url_for('assets.detail', id=id))


@assets_bp.route('/<id>/delete', methods=['POST'])
@login_required
def delete_asset(id):
    if not current_user.is_admin:
        abort(403)
    asset = get_asset(id)
    if not asset:
        abort(404)
    sn = asset.serial_number
    from app.db import events_col
    events_col().delete_many({'asset_id': id})
    assets_col().delete_one({'_id': ObjectId(id)})
    flash(f'Asset "{sn}" permanently deleted.', 'warning')
    return redirect(url_for('assets.list_assets'))
