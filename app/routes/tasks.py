from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, g
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length
from bson import ObjectId
from datetime import datetime

from app.db import (
    all_tasks, get_task, tasks_col, assets_col, all_assets, all_users,
)
from app.utils.translations import localize_form

tasks_bp = Blueprint('tasks', __name__, url_prefix='/tasks')


def _asset_choices():
    assets = all_assets(sort_field='serial_number', sort_order=1)
    return [('', '— None —')] + [
        (a.id, f'{a.serial_number}  ({a.asset_type.name if a.asset_type else "?"})') for a in assets
    ]


def _user_choices(include_none=True):
    users = all_users()
    base = [('', '— None —')] if include_none else []
    return base + [(u.id, u.name) for u in users]


class TaskForm(FlaskForm):
    title          = StringField('Task Title', validators=[DataRequired(), Length(max=255)])
    asset_id       = SelectField('Related Asset', coerce=str, validators=[Optional()])
    assigned_to_id = SelectField('Assigned To',   coerce=str, validators=[Optional()])
    status         = SelectField('Status', choices=[
        ('pending', 'Pending'), ('in_progress', 'In Progress'), ('done', 'Done'),
    ])
    notes  = TextAreaField('Notes',  validators=[Optional()])
    submit = SubmitField('Save Task')

    def populate_choices(self):
        self.asset_id.choices       = _asset_choices()
        self.assigned_to_id.choices = _user_choices()


def _localize_task_form(form, t):
    localize_form(form, t, submit_key='form_save_task')
    form.status.choices = [
        ('pending',     t.get('task_status_pending',     'Pending')),
        ('in_progress', t.get('task_status_in_progress', 'In Progress')),
        ('done',        t.get('task_status_done',        'Done')),
    ]
    return form


@tasks_bp.route('/')
@login_required
def list_tasks():
    status_filter   = request.args.get('status', '')
    assignee_filter = request.args.get('assignee', '')
    sort   = request.args.get('sort',  'created_at')
    order  = request.args.get('order', 'desc')

    query = {}
    if status_filter:
        query['status'] = status_filter
    if assignee_filter:
        query['assigned_to_id'] = assignee_filter

    sort_order = 1 if order == 'asc' else -1
    tasks = all_tasks(query=query, sort_field=sort, sort_order=sort_order)
    users = all_users()

    return render_template(
        'tasks/list.html',
        tasks=tasks, users=users,
        status_filter=status_filter, assignee_filter=assignee_filter,
        sort=sort, order=order,
    )


@tasks_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_task():
    t = getattr(g, 't', {})
    form = TaskForm()
    form.populate_choices()
    _localize_task_form(form, t)

    if request.method == 'GET':
        asset_id = request.args.get('asset_id', '')
        if asset_id:
            form.asset_id.data = asset_id
        form.assigned_to_id.data = current_user.id

    if form.validate_on_submit():
        tasks_col().insert_one({
            'title':          form.title.data.strip(),
            'asset_id':       form.asset_id.data or None,
            'assigned_to_id': form.assigned_to_id.data or None,
            'status':         form.status.data,
            'notes':          form.notes.data.strip() or None,
            'created_at':     datetime.utcnow(),
        })
        flash(t.get('flash_task_created', 'Task created successfully.'), 'success')
        return redirect(url_for('tasks.list_tasks'))

    return render_template('tasks/form.html', form=form, task=None,
                           title=t.get('form_title_new_task', 'New Task'))


@tasks_bp.route('/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    t = getattr(g, 't', {})
    task = get_task(id)
    if not task:
        abort(404)
    form = TaskForm(obj=task)
    form.populate_choices()
    _localize_task_form(form, t)

    if form.validate_on_submit():
        tasks_col().update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'title':          form.title.data.strip(),
                'asset_id':       form.asset_id.data or None,
                'assigned_to_id': form.assigned_to_id.data or None,
                'status':         form.status.data,
                'notes':          form.notes.data.strip() or None,
            }},
        )
        flash(t.get('flash_task_updated', 'Task updated successfully.'), 'success')
        return redirect(url_for('tasks.list_tasks'))

    return render_template('tasks/form.html', form=form, task=task,
                           title=t.get('form_title_edit_task', 'Edit Task'))


@tasks_bp.route('/<id>/done', methods=['POST'])
@login_required
def mark_done(id):
    t = getattr(g, 't', {})
    task = get_task(id)
    if not task:
        abort(404)
    tasks_col().update_one({'_id': ObjectId(id)}, {'$set': {'status': 'done'}})
    flash(t.get('flash_task_done', '"{title}" marked as done.').format(title=task.title), 'success')
    return redirect(request.referrer or url_for('tasks.list_tasks'))


@tasks_bp.route('/<id>/reopen', methods=['POST'])
@login_required
def reopen(id):
    t = getattr(g, 't', {})
    task = get_task(id)
    if not task:
        abort(404)
    tasks_col().update_one({'_id': ObjectId(id)}, {'$set': {'status': 'pending'}})
    flash(t.get('flash_task_reopened', '"{title}" reopened.').format(title=task.title), 'info')
    return redirect(request.referrer or url_for('tasks.list_tasks'))


@tasks_bp.route('/<id>/delete', methods=['POST'])
@login_required
def delete(id):
    if not current_user.is_admin:
        abort(403)
    t = getattr(g, 't', {})
    task = get_task(id)
    if not task:
        abort(404)
    title = task.title
    tasks_col().delete_one({'_id': ObjectId(id)})
    flash(t.get('flash_task_deleted', 'Task "{title}" deleted.').format(title=title), 'warning')
    return redirect(url_for('tasks.list_tasks'))
