from flask import Blueprint, render_template

bp_view = Blueprint('backup_view', __name__)

@bp_view.route('/backup/backup-restore')
def backup_restore_page():
    """Show backup and restore page"""
    return render_template('backup/backup_restore.html')
