from flask import Blueprint, render_template, redirect, url_for, flash, abort, g
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length
from bson import ObjectId

from app.db import (
    all_sites, get_site, sites_col, assets_col,
)
from app.utils.translations import localize_form

sites_bp = Blueprint('sites', __name__, url_prefix='/sites')


class SiteForm(FlaskForm):
    name    = StringField('Site Name', validators=[DataRequired(), Length(max=150)])
    address = TextAreaField('Address',  validators=[Optional()])
    notes   = TextAreaField('Notes',    validators=[Optional()])
    submit  = SubmitField('Save Site')


@sites_bp.route('/')
@login_required
def list_sites():
    sites = all_sites()
    counts = {s.id: assets_col().count_documents({'current_site_id': s.id}) for s in sites}
    return render_template('sites/list.html', sites=sites, counts=counts)


@sites_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_site():
    if not current_user.is_admin:
        abort(403)
    t = getattr(g, 't', {})
    form = SiteForm()
    localize_form(form, t, submit_key='form_save_site')
    if form.validate_on_submit():
        result = sites_col().insert_one({
            'name':    form.name.data.strip(),
            'address': form.address.data.strip() or None,
            'notes':   form.notes.data.strip() or None,
        })
        site = get_site(str(result.inserted_id))
        flash(t.get('flash_site_created', 'Site "{name}" created successfully.').format(name=site.name), 'success')
        return redirect(url_for('sites.detail', id=site.id))
    return render_template('sites/form.html', form=form, site=None,
                           title=t.get('form_title_add_site', 'Add New Site'))


@sites_bp.route('/<id>')
@login_required
def detail(id):
    site = get_site(id)
    if not site:
        abort(404)
    from app.db import all_assets
    assets = all_assets({'current_site_id': id}, sort_field='serial_number', sort_order=1)
    status_counts = {}
    for a in assets:
        status_counts[a.status] = status_counts.get(a.status, 0) + 1
    return render_template('sites/detail.html', site=site, assets=assets, status_counts=status_counts)


@sites_bp.route('/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    if not current_user.is_admin:
        abort(403)
    t = getattr(g, 't', {})
    site = get_site(id)
    if not site:
        abort(404)
    form = SiteForm(obj=site)
    localize_form(form, t, submit_key='form_save_site')
    if form.validate_on_submit():
        sites_col().update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'name':    form.name.data.strip(),
                'address': form.address.data.strip() or None,
                'notes':   form.notes.data.strip() or None,
            }},
        )
        flash(t.get('flash_site_updated', 'Site updated successfully.'), 'success')
        return redirect(url_for('sites.detail', id=id))
    return render_template('sites/form.html', form=form, site=site,
                           title=t.get('form_title_edit_site', 'Edit Site'))
