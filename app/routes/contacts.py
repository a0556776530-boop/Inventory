from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, g
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Email, Length
from bson import ObjectId
from datetime import datetime

from app.db import _col

contacts_bp = Blueprint('contacts', __name__, url_prefix='/contacts')


def contacts_col():
    return _col('contacts')


class ContactForm(FlaskForm):
    name         = StringField('Full Name',    validators=[DataRequired(), Length(max=100)])
    company      = StringField('Company',      validators=[Optional(), Length(max=150)])
    role         = StringField('Role / Title', validators=[Optional(), Length(max=100)])
    phone        = StringField('Phone',        validators=[Optional(), Length(max=50)])
    email        = StringField('Email',        validators=[Optional(), Email(check_deliverability=False)])
    notes        = TextAreaField('Notes',      validators=[Optional()])
    submit       = SubmitField('Save Contact')


@contacts_bp.route('/')
@login_required
def list_contacts():
    q = request.args.get('q', '').strip()
    query = {}
    if q:
        import re
        regex = re.compile(re.escape(q), re.IGNORECASE)
        query['$or'] = [{'name': regex}, {'company': regex}, {'phone': regex}, {'email': regex}]
    contacts = list(contacts_col().find(query).sort('name', 1))
    return render_template('contacts/list.html', contacts=contacts, q=q)


@contacts_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_contact():
    form = ContactForm()
    if form.validate_on_submit():
        contacts_col().insert_one({
            'name':       form.name.data.strip(),
            'company':    form.company.data.strip() or None,
            'role':       form.role.data.strip() or None,
            'phone':      form.phone.data.strip() or None,
            'email':      form.email.data.strip().lower() or None,
            'notes':      form.notes.data.strip() or None,
            'created_at': datetime.utcnow(),
        })
        flash(f'Contact "{form.name.data.strip()}" added successfully.', 'success')
        return redirect(url_for('contacts.list_contacts'))
    return render_template('contacts/form.html', form=form, contact=None, title='New Contact')


@contacts_bp.route('/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit_contact(id):
    doc = contacts_col().find_one({'_id': ObjectId(id)})
    if not doc:
        abort(404)
    from app.db.models import MongoDoc
    contact = MongoDoc(doc)
    form = ContactForm(obj=contact)
    if form.validate_on_submit():
        contacts_col().update_one({'_id': ObjectId(id)}, {'$set': {
            'name':    form.name.data.strip(),
            'company': form.company.data.strip() or None,
            'role':    form.role.data.strip() or None,
            'phone':   form.phone.data.strip() or None,
            'email':   form.email.data.strip().lower() or None,
            'notes':   form.notes.data.strip() or None,
        }})
        flash('Contact updated.', 'success')
        return redirect(url_for('contacts.list_contacts'))
    return render_template('contacts/form.html', form=form, contact=contact, title='Edit Contact')


@contacts_bp.route('/<id>/delete', methods=['POST'])
@login_required
def delete_contact(id):
    doc = contacts_col().find_one({'_id': ObjectId(id)})
    if not doc:
        abort(404)
    name = doc.get('name', '')
    contacts_col().delete_one({'_id': ObjectId(id)})
    flash(f'Contact "{name}" deleted.', 'warning')
    return redirect(url_for('contacts.list_contacts'))
