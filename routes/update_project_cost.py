from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime
from flask import Blueprint




update_project_cost_bp = Blueprint('update_project_cost', __name__)



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








# Update project cost route
@update_project_cost_bp.route('/project/<int:project_id>/update_cost', methods=['GET', 'POST'])
def update_project_cost(project_id):
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
            change_reason = request.form['change_reason']
            
            if project['project_type'] == 'fixed':
                new_cost = request.form['total_amount']
                previous_value = str(project['total_amount'])
                cost_field = 'total_amount'
            else:  # T&M
                new_cost = request.form['per_month_billing']
                previous_value = str(project['per_month_billing'])
                cost_field = 'per_month_billing'
            
            # Begin transaction
            try:
                # Update version and record change
                update_project_version(
                    conn, cursor, project_id, 
                    'cost', 
                    change_reason,
                    previous_value, 
                    new_cost
                )
                
                # Update project cost
                cursor.execute(f'UPDATE projects SET {cost_field} = %s WHERE id = %s', (new_cost, project_id))
                
                conn.commit()
                
                # Redirect to project details page
                return redirect(url_for('project_details.project_details', project_id=project_id))
            except Exception as e:
                # Rollback in case of error
                conn.rollback()
                print(f"Error updating cost: {e}")
        
        # Fetch version history for cost changes
        cursor.execute('''
            SELECT pv.*, u.username 
            FROM project_versions pv
            JOIN users u ON pv.changed_by = u.id
            WHERE pv.project_id = %s AND pv.change_type = 'cost'
            ORDER BY pv.changed_at DESC
        ''', (project_id,))
        cost_versions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Return template
        return render_template('update_project_cost.html', project=project, cost_versions=cost_versions)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home.home'))