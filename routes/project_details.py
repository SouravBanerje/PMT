from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from flask import Blueprint
from flask import session
import datetime
from datetime import datetime


project_details_bp = Blueprint('project_details', __name__)



# # Update the project_details route to show version information
@project_details_bp.route('/project/<int:project_id>')
def project_details(project_id):
    # Check if user is logged in
    if 'loggedin' in session:
        # Fetch project details
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
        project = cursor.fetchone()
        
        # Fetch project manager details
        cursor.execute('SELECT username FROM users WHERE id = %s', (project['pm_id'],))
        pm = cursor.fetchone()
        
        # Fetch tasks
        cursor.execute('SELECT * FROM tasks WHERE project_id = %s ORDER BY id', (project_id,))
        tasks = cursor.fetchall()
        
        # Fetch schedule version history (latest 3)
        cursor.execute('''
            SELECT sv.*, u.username 
            FROM schedule_versions sv
            JOIN users u ON sv.changed_by = u.id
            WHERE sv.project_id = %s
            ORDER BY sv.changed_at DESC
            LIMIT 3
        ''', (project_id,))
        recent_schedule_changes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Calculate project duration in days
        start_date = datetime.strptime(str(project['start_date']), '%Y-%m-%d')
        end_date = datetime.strptime(str(project['end_date']), '%Y-%m-%d')
        project_duration = (end_date - start_date).days
        
        # Return template with schedule version info
        return render_template('project_details.html', 
                               project=project, 
                               pm=pm, 
                               tasks=tasks, 
                               project_duration=project_duration,
                               recent_schedule_changes=recent_schedule_changes)
    
    # User is not logged in, redirect to login page
    return redirect(url_for('auth.login'))