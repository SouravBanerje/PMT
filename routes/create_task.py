from flask import Flask, render_template, request, redirect, url_for, session,Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime



create_task_bp = Blueprint('create_task', __name__)



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



# Modified create_task route to track resource changes
@create_task_bp.route('/project/<int:project_id>/create_task', methods=['GET', 'POST'])
def create_task(project_id):
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Fetch project details
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
        project = cursor.fetchone()
        
        # Fetch existing tasks for parent task dropdown
        cursor.execute('SELECT id, task_name FROM tasks WHERE project_id = %s', (project_id,))
        existing_tasks = cursor.fetchall()
        
        # Fetch team members for resource assignment
        cursor.execute('SELECT id, username FROM users WHERE user_type = "team_member"')
        team_members = cursor.fetchall()
        
        # Check if form is submitted
        if request.method == 'POST':
            # Create variables for easy access
            task_name = request.form['task_name']
            task_description = request.form.get('task_description', '')
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            dependency_days = request.form.get('dependency_days', 0)
            parent_task_id = request.form.get('parent_task_id')
            if parent_task_id == '' or not parent_task_id:
                parent_task_id = None
            is_active = request.form.get('is_active') == 'yes'
            status = request.form['status']
            
            try:
                # Insert task into database
                cursor.execute('''
                    INSERT INTO tasks 
                    (project_id, task_name, description, start_date, end_date, dependency_days, 
                    parent_task_id, is_active, status, color) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (project_id, task_name, task_description, start_date, end_date, 
                     dependency_days, parent_task_id, is_active, status, 'green'))
                conn.commit()
                
                # Get the inserted task ID
                task_id = cursor.lastrowid
                
                # Assign resources to the task
                resources = request.form.getlist('resources[]')
                designations = request.form.getlist('designations[]')
                
                resource_descriptions = []
                for i in range(len(resources)):
                    cursor.execute('''
                        INSERT INTO task_resources 
                        (task_id, user_id, designation) 
                        VALUES (%s, %s, %s)
                    ''', (task_id, resources[i], designations[i]))
                    
                    # Get username for resource description
                    cursor.execute('SELECT username FROM users WHERE id = %s', (resources[i],))
                    username = cursor.fetchone()['username']
                    resource_descriptions.append(f"{username} as {designations[i]}")
                
                # Update project version for resource changes
                if resource_descriptions:
                    resources_str = ", ".join(resource_descriptions)
                    description = f"Added resources to new task '{task_name}': {resources_str}"
                    update_project_version(
                        conn, cursor, project_id,
                        'resource',
                        description,
                        '',  # No previous value for new task
                        resources_str
                    )
                
                conn.commit()
                
                # Redirect to project details page
                return redirect(url_for('project_details.project_details', project_id=project_id))
            except Exception as e:
                conn.rollback()
                print(f"Error creating task: {e}")
        
        cursor.close()
        conn.close()
        
        # Return template
        return render_template('create_task.html', project=project, 
                               existing_tasks=existing_tasks, team_members=team_members)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home.home'))