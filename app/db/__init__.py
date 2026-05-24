"""
MongoDB query layer — replaces SQLAlchemy ORM.
All reference IDs are stored as plain strings (str(ObjectId)).
Batch-loading eliminates N+1 queries on list views.
"""
from datetime import datetime
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.utils.mongo import get_db
from .models import (
    MongoUser, AssetDoc, TaskDoc, AssetEventDoc,
    EstimateDoc, EstimateItemDoc, MongoDoc,
)


def _col(name):
    return get_db('netstock')[name]


# ── Collection accessors ───────────────────────────────────────────────────────

def users_col():        return _col('users')
def sites_col():        return _col('sites')
def asset_types_col():  return _col('asset_types')
def assets_col():       return _col('assets')
def events_col():       return _col('asset_events')
def tasks_col():        return _col('tasks')
def estimates_col():    return _col('estimates')
def est_items_col():    return _col('estimate_items')
def settings_col():     return _col('app_settings')


def ensure_indexes():
    """Create indexes — safe to call multiple times."""
    def _idx(col, *args, **kwargs):
        try:
            col.create_index(*args, **kwargs)
        except Exception:
            pass

    _idx(assets_col(),    'serial_number',  unique=True, sparse=True)
    _idx(assets_col(),    'barcode',        unique=True, sparse=True)
    _idx(assets_col(),    'status')
    _idx(assets_col(),    'asset_type_id')
    _idx(assets_col(),    'current_site_id')
    _idx(assets_col(),    'assigned_to_id')
    _idx(assets_col(),    'quantity')
    _idx(events_col(),    'asset_id')
    _idx(events_col(),    [('event_date', DESCENDING)])
    _idx(tasks_col(),     'assigned_to_id')
    _idx(tasks_col(),     'status')
    _idx(estimates_col(), 'status')
    _idx(est_items_col(), 'estimate_id')
    _idx(est_items_col(), 'asset_id')


# ── Batch reference caches ─────────────────────────────────────────────────────

def _load_all_types():
    """Load all asset types into {id_str: MongoDoc} dict — 1 query."""
    return {str(d['_id']): MongoDoc(d) for d in asset_types_col().find()}


def _load_all_sites():
    """Load all sites into {id_str: MongoDoc} dict — 1 query."""
    return {str(d['_id']): MongoDoc(d) for d in sites_col().find()}


def _load_all_users():
    """Load all users into {id_str: MongoUser} dict — 1 query."""
    return {str(d['_id']): MongoUser(d) for d in users_col().find()}


# ── User helpers ───────────────────────────────────────────────────────────────

def get_user(user_id):
    if not user_id:
        return None
    try:
        doc = users_col().find_one({'_id': ObjectId(user_id)})
    except Exception:
        return None
    return MongoUser(doc) if doc else None


def find_user_by_email(email):
    doc = users_col().find_one({'email': email})
    return MongoUser(doc) if doc else None


def all_users():
    return [MongoUser(d) for d in users_col().find().sort('name', ASCENDING)]


# ── Site helpers ───────────────────────────────────────────────────────────────

def get_site(site_id):
    if not site_id:
        return None
    try:
        doc = sites_col().find_one({'_id': ObjectId(site_id)})
    except Exception:
        return None
    return MongoDoc(doc) if doc else None


def all_sites():
    return [MongoDoc(d) for d in sites_col().find().sort('name', ASCENDING)]


# ── AssetType helpers ──────────────────────────────────────────────────────────

def get_asset_type(type_id):
    if not type_id:
        return None
    try:
        doc = asset_types_col().find_one({'_id': ObjectId(type_id)})
    except Exception:
        return None
    return MongoDoc(doc) if doc else None


def all_asset_types():
    return [MongoDoc(d) for d in asset_types_col().find().sort('name', ASCENDING)]


# ── Asset helpers ──────────────────────────────────────────────────────────────

def _hydrate_asset(doc, types_cache=None, sites_cache=None, users_cache=None):
    """Hydrate a single asset doc. Uses caches when available (batch mode)."""
    if doc is None:
        return None
    asset = AssetDoc(doc)

    if types_cache is not None:
        asset.set_ref('asset_type', types_cache.get(doc.get('asset_type_id')))
    else:
        asset.set_ref('asset_type', get_asset_type(doc.get('asset_type_id')))

    if sites_cache is not None:
        asset.set_ref('current_site', sites_cache.get(doc.get('current_site_id')))
    else:
        asset.set_ref('current_site', get_site(doc.get('current_site_id')))

    if users_cache is not None:
        asset.set_ref('assignee', users_cache.get(doc.get('assigned_to_id')))
    else:
        uid = doc.get('assigned_to_id')
        asset.set_ref('assignee', get_user(uid) if uid else None)

    return asset


def get_asset(asset_id):
    if not asset_id:
        return None
    try:
        doc = assets_col().find_one({'_id': ObjectId(asset_id)})
    except Exception:
        return None
    return _hydrate_asset(doc)


def all_assets(query=None, sort_field='created_at', sort_order=DESCENDING):
    """Load all assets with batch-hydration: 4 DB queries total, not 3×N."""
    types_cache = _load_all_types()
    sites_cache = _load_all_sites()
    users_cache = _load_all_users()
    docs = list(assets_col().find(query or {}).sort(sort_field, sort_order))
    return [_hydrate_asset(d, types_cache, sites_cache, users_cache) for d in docs]


# ── AssetEvent helpers ─────────────────────────────────────────────────────────

def _hydrate_event(doc, assets_cache=None, sites_cache=None, users_cache=None):
    if doc is None:
        return None
    event = AssetEventDoc(doc)

    if assets_cache is not None:
        event.set_ref('asset', assets_cache.get(doc.get('asset_id')))
    else:
        event.set_ref('asset', get_asset(doc.get('asset_id')))

    if sites_cache is not None:
        event.set_ref('from_site', sites_cache.get(doc.get('from_site_id')))
        event.set_ref('to_site',   sites_cache.get(doc.get('to_site_id')))
    else:
        event.set_ref('from_site', get_site(doc.get('from_site_id')))
        event.set_ref('to_site',   get_site(doc.get('to_site_id')))

    if users_cache is not None:
        event.set_ref('performed_by_user', users_cache.get(doc.get('performed_by_id')))
    else:
        event.set_ref('performed_by_user', get_user(doc.get('performed_by_id')))

    return event


def get_asset_events(asset_id, limit=None):
    if not asset_id:
        return []
    cursor = events_col().find({'asset_id': asset_id}).sort('event_date', DESCENDING)
    if limit:
        cursor = cursor.limit(limit)
    sites_cache = _load_all_sites()
    users_cache = _load_all_users()
    return [_hydrate_event(d, sites_cache=sites_cache, users_cache=users_cache) for d in cursor]


def get_recent_events(limit=15):
    """Batch-load recent events for dashboard — minimal queries."""
    docs = list(events_col().find().sort('event_date', DESCENDING).limit(limit))
    if not docs:
        return []

    asset_ids = list({d['asset_id'] for d in docs if d.get('asset_id')})
    try:
        asset_oid_map = {str(d['_id']): _hydrate_asset(d)
                         for d in assets_col().find({'_id': {'$in': [ObjectId(i) for i in asset_ids]}})}
    except Exception:
        asset_oid_map = {}

    sites_cache = _load_all_sites()
    users_cache = _load_all_users()

    return [_hydrate_event(d, assets_cache=asset_oid_map,
                           sites_cache=sites_cache, users_cache=users_cache)
            for d in docs]


def log_event(asset_id, event_type, performed_by_id,
              from_site_id=None, to_site_id=None, notes=None):
    events_col().insert_one({
        'asset_id':        asset_id,
        'event_type':      event_type,
        'from_site_id':    from_site_id,
        'to_site_id':      to_site_id,
        'performed_by_id': performed_by_id,
        'notes':           notes,
        'event_date':      datetime.utcnow(),
    })


# ── Task helpers ───────────────────────────────────────────────────────────────

def _hydrate_task(doc, assets_cache=None, users_cache=None):
    if doc is None:
        return None
    task = TaskDoc(doc)

    if assets_cache is not None:
        task.set_ref('asset', assets_cache.get(doc.get('asset_id')))
    else:
        aid = doc.get('asset_id')
        task.set_ref('asset', get_asset(aid) if aid else None)

    if users_cache is not None:
        task.set_ref('assignee', users_cache.get(doc.get('assigned_to_id')))
    else:
        uid = doc.get('assigned_to_id')
        task.set_ref('assignee', get_user(uid) if uid else None)

    return task


def get_task(task_id):
    if not task_id:
        return None
    try:
        doc = tasks_col().find_one({'_id': ObjectId(task_id)})
    except Exception:
        return None
    return _hydrate_task(doc)


def all_tasks(query=None, sort_field='created_at', sort_order=DESCENDING):
    """Batch-load tasks."""
    users_cache = _load_all_users()
    docs = list(tasks_col().find(query or {}).sort(sort_field, sort_order))

    asset_ids = list({d['asset_id'] for d in docs if d.get('asset_id')})
    assets_cache = {}
    if asset_ids:
        try:
            types_cache = _load_all_types()
            sites_cache = _load_all_sites()
            for d in assets_col().find({'_id': {'$in': [ObjectId(i) for i in asset_ids]}}):
                assets_cache[str(d['_id'])] = _hydrate_asset(d, types_cache, sites_cache, users_cache)
        except Exception:
            pass

    return [_hydrate_task(d, assets_cache=assets_cache, users_cache=users_cache) for d in docs]


# ── Estimate helpers ───────────────────────────────────────────────────────────

def _hydrate_estimate(doc):
    if doc is None:
        return None
    est = EstimateDoc(doc)
    users_cache = _load_all_users()
    types_cache = _load_all_types()
    sites_cache = _load_all_sites()

    items_raw = list(est_items_col().find({'estimate_id': est.id}).sort('_id', ASCENDING))
    asset_ids = list({d['asset_id'] for d in items_raw if d.get('asset_id')})
    assets_cache = {}
    if asset_ids:
        try:
            for d in assets_col().find({'_id': {'$in': [ObjectId(i) for i in asset_ids]}}):
                assets_cache[str(d['_id'])] = _hydrate_asset(d, types_cache, sites_cache, users_cache)
        except Exception:
            pass

    items = []
    for item_doc in items_raw:
        item = EstimateItemDoc(item_doc)
        item.set_ref('asset',    assets_cache.get(item_doc.get('asset_id')))
        item.set_ref('estimate', est)
        items.append(item)

    est.set_ref('items',      items)
    est.set_ref('created_by', users_cache.get(doc.get('created_by_id')))
    return est


def get_estimate(est_id):
    if not est_id:
        return None
    try:
        doc = estimates_col().find_one({'_id': ObjectId(est_id)})
    except Exception:
        return None
    return _hydrate_estimate(doc)


def all_estimates(query=None):
    docs = estimates_col().find(query or {}).sort('created_at', DESCENDING)
    return [_hydrate_estimate(d) for d in docs]


def next_allocation_number():
    last = estimates_col().find_one({}, sort=[('allocation_number', DESCENDING)])
    return (last['allocation_number'] if last else 0) + 1


# ── AppSetting helpers ─────────────────────────────────────────────────────────

SETTING_DEFAULTS = {'usd_rate': '3.0'}


def setting_get(key):
    doc = settings_col().find_one({'_id': key})
    if doc:
        return float(doc['value'])
    return float(SETTING_DEFAULTS.get(key, '0'))


def setting_set(key, value):
    settings_col().replace_one({'_id': key}, {'_id': key, 'value': str(value)}, upsert=True)


def all_settings():
    stored = {d['_id']: d['value'] for d in settings_col().find()}
    return {k: float(stored.get(k, v)) for k, v in SETTING_DEFAULTS.items()}
