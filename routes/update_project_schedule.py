from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime
from flask import Blueprint




update_project_schedule_bp = Blueprint('update_project_schedule', __name__)




# Helper function to update project version
def update_project_version(conn, cursor, project_id, change_type, description, previous_value, new_value):
    # Get current project version
    cursor.execute('SELECT version FROM projects WHERE id = %s', (project_id,))
    current_version = cursor.fetchone()['version']
    
    # Increment version
    major, minor = current_version.split('.')
    new_version = f"{major}.{int(minor) + 1}"
    
    # Record the change
    cursor.execute('''
        INSERT INTO project_versions 
        (project_id, version, change_type, description, previous_value, new_value, changed_by) 
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (project_id, new_version, change_type, description, previous_value, new_value, session['id']))
    
    # Update project version
    cursor.execute('UPDATE projects SET version = %s WHERE id = %s', (new_version, project_id))
    
    return new_version








# Update project schedule route
@update_project_schedule_bp.route('/project/<int:project_id>/update_schedule', methods=['GET', 'POST'])
def update_project_schedule(project_id):
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Fetch project details
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
        project = cursor.fetchone()
        
        # Process form submission
        if request.method == 'POST':
            # Get form data
            new_end_date = request.form['new_end_date']
            change_reason = request.form['change_reason']
            
            # Begin transaction
            try:
                # Update version and record change
                update_project_version(
                    conn, cursor, project_id, 
                    'schedule', 
                    change_reason,
                    str(project['end_date']), 
                    new_end_date
                )
                
                # Update project end date
                cursor.execute('UPDATE projects SET end_date = %s WHERE id = %s', (new_end_date, project_id))
                
                conn.commit()
                
                # Redirect to project details page
                return redirect(url_for('project_details', project_id=project_id))
            except Exception as e:
                # Rollback in case of error
                conn.rollback()
                print(f"Error updating schedule: {e}")
        
        # Fetch version history for schedule changes
        cursor.execute('''
            SELECT pv.*, u.username 
            FROM project_versions pv
            JOIN users u ON pv.changed_by = u.id
            WHERE pv.project_id = %s AND pv.change_type = 'schedule'
            ORDER BY pv.changed_at DESC
        ''', (project_id,))
        schedule_versions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Return template
        return render_template('update_project_schedule.html', project=project, schedule_versions=schedule_versions)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home.home'))

