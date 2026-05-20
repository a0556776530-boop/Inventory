from app.db import log_event as _log


def log_event(asset, event_type, performed_by, from_site=None, to_site=None, notes=None):
    _log(
        asset_id=asset.id,
        event_type=event_type,
        performed_by_id=performed_by.id,
        from_site_id=from_site.id if from_site else None,
        to_site_id=to_site.id if to_site else None,
        notes=notes,
    )
