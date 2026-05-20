from flask_login import UserMixin


class MongoDoc:
    """Wraps a MongoDB document dict — gives attribute-style read/write access."""

    def __init__(self, data):
        object.__setattr__(self, '_data', data or {})
        object.__setattr__(self, '_refs', {})

    @property
    def id(self):
        return str(self._data.get('_id', ''))

    def __getattr__(self, name):
        refs = object.__getattribute__(self, '_refs')
        if name in refs:
            return refs[name]
        data = object.__getattribute__(self, '_data')
        if name in data:
            return data[name]
        return None

    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            object.__getattribute__(self, '_data')[name] = value

    def set_ref(self, name, obj):
        object.__getattribute__(self, '_refs')[name] = obj

    def __bool__(self):
        return bool(object.__getattribute__(self, '_data'))

    def get(self, key, default=None):
        return object.__getattribute__(self, '_data').get(key, default)

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.id}>'


class MongoUser(UserMixin, MongoDoc):

    def get_id(self):
        return str(self._data['_id'])

    @property
    def is_admin(self):
        return self._data.get('role') == 'admin'

    @property
    def can_edit(self):
        return self._data.get('role') in ('admin', 'technician')


class AssetDoc(MongoDoc):
    STATUSES = ['in_use', 'dismantled', 'in_storage', 'assigned', 'faulty', 'retired']
    STATUS_LABELS = {
        'in_use': 'בשימוש', 'dismantled': 'פורק', 'in_storage': 'באחסון',
        'assigned': 'מוקצה', 'faulty': 'פגום', 'retired': 'הוצא משירות',
    }
    STATUS_COLORS = {
        'in_use': 'success', 'dismantled': 'warning', 'in_storage': 'info',
        'assigned': 'primary', 'faulty': 'danger', 'retired': 'secondary',
    }

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self._data.get('status', ''), self._data.get('status', ''))

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self._data.get('status', ''), 'secondary')


class TaskDoc(MongoDoc):
    STATUS_LABELS = {'pending': 'ממתין', 'in_progress': 'בביצוע', 'done': 'הושלם'}
    STATUS_COLORS = {'pending': 'warning', 'in_progress': 'primary', 'done': 'success'}

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self._data.get('status', ''), self._data.get('status', ''))

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self._data.get('status', ''), 'secondary')


class AssetEventDoc(MongoDoc):
    EVENT_LABELS = {
        'dismantled': 'פורק', 'moved': 'הועבר', 'assigned': 'הוקצה',
        'returned': 'הוחזר', 'repaired': 'תוקן', 'created': 'נוצר',
        'retired': 'הוצא משירות', 'status_change': 'סטטוס שונה',
    }
    EVENT_ICONS = {
        'dismantled': 'bi-tools', 'moved': 'bi-arrow-left-right',
        'assigned': 'bi-person-check', 'returned': 'bi-arrow-return-left',
        'repaired': 'bi-wrench', 'created': 'bi-plus-circle',
        'retired': 'bi-archive', 'status_change': 'bi-arrow-repeat',
    }

    @property
    def event_label(self):
        return self.EVENT_LABELS.get(self._data.get('event_type', ''), self._data.get('event_type', ''))

    @property
    def event_icon(self):
        return self.EVENT_ICONS.get(self._data.get('event_type', ''), 'bi-circle')


class EstimateDoc(MongoDoc):
    @property
    def formatted_total(self):
        total = self._data.get('total_nis')
        if total is None:
            return '—'
        return '{:,.2f} ₪'.format(float(total))


class EstimateItemDoc(MongoDoc):
    @property
    def line_total_nis(self):
        unit_price = self._data.get('unit_price_usd')
        estimate = self._refs.get('estimate')
        qty = self._data.get('quantity', 1)
        if not unit_price or not estimate:
            return 0.0
        rate = float(estimate.usd_rate or 3.0)
        return round(float(unit_price) * rate * 1.7 * 1.18 * qty, 2)
