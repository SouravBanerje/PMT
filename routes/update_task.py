from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime, timedelta
import re







update_task_bp = Blueprint('update_task', __name__)




# Helper function to create activity
def create_activity(user_id, project_id=None, task_id=None, activity_type=None, description=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO activities 
        (user_id, project_id, task_id, activity_type, description) 
        VALUES (%s, %s, %s, %s, %s)
    ''', (user_id, project_id, task_id, activity_type, description))
    conn.commit()
    cursor.close()
    conn.close()



# Helper function to extract mentions from text
def extract_mentions(text):
    # Look for @username pattern
    mentions = re.findall(r'@(\w+)', text)
    return mentions



# Helper function to create notification
def create_notification(user_id, content, link=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notifications 
        (user_id, content, link) 
        VALUES (%s, %s, %s)
    ''', (user_id, content, link))
    conn.commit()
    cursor.close()
    conn.close()

# Helper function to create mention
def create_mention(user_id, mentioned_by, content_type, content_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO mentions 
        (user_id, mentioned_by, content_type, content_id) 
        VALUES (%s, %s, %s, %s)
    ''', (user_id, mentioned_by, content_type, content_id))
    conn.commit()
    cursor.close()
    conn.close()


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










#Update task route
@update_task_bp.route('/task/<int:task_id>/update', methods=['POST'])
def update_task(task_id):
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Create variables for easy access
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        status = request.form['status']
        
        # Update task in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE tasks 
            SET start_date = %s, end_date = %s, status = %s, color = %s 
            WHERE id = %s
        ''', (start_date, end_date, status, 'green', task_id))
        conn.commit()
        
        # Fetch task details to get project_id
        cursor.execute('SELECT project_id FROM tasks WHERE id = %s', (task_id,))
        task = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Redirect back to project details
        return redirect(url_for('project_details.project_details', project_id=task['project_id']))
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home.home'))






# Update the existing add_comment route to include mention processing
@update_task_bp.route('/task/<int:task_id>/add_comment', methods=['POST'])
def add_comment(task_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    # Create variables for easy access
    comment_text = request.form['comment_text']
    
    # Insert comment into database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch task and project info
    cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
    task = cursor.fetchone()
    
    if not task:
        cursor.close()
        conn.close()
        flash('Task not found!')
        return redirect(url_for('home'))
    
    cursor.execute('SELECT * FROM projects WHERE id = %s', (task['project_id'],))
    project = cursor.fetchone()
    
    cursor.execute('''
        INSERT INTO comments 
        (task_id, user_id, comment_text, created_at) 
        VALUES (%s, %s, %s, %s)
    ''', (task_id, session['id'], comment_text, datetime.now()))
    conn.commit()
    comment_id = cursor.lastrowid
    
    # Check for mentions
    mentions = extract_mentions(comment_text)
    if mentions:
        for username in mentions:
            cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
            mentioned_user = cursor.fetchone()
            if mentioned_user:
                # Create mention record
                create_mention(mentioned_user['id'], session['id'], 'comment', comment_id)
                
                # Create notification
                notification_content = f"{session['username']} mentioned you in a comment on task '{task['task_name']}'"
                link = f"/task/{task_id}"
                create_notification(mentioned_user['id'], notification_content, link)
    
    # Update task color to red
    cursor.execute('UPDATE tasks SET color = %s WHERE id = %s', ('red', task_id))
    conn.commit()
    
    # Log activity
    activity_description = f"Commented on task '{task['task_name']}'"
    create_activity(session['id'], task['project_id'], task_id, 'comment', activity_description)
    
    cursor.close()
    conn.close()
    
    # Redirect back to task details
    return redirect(url_for('task_details', task_id=task_id))





@update_task_bp.route('/task/<int:task_id>/update_task_resources', methods=['GET', 'POST'])
def update_task_resources(task_id):
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Fetch task info
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
        task = cursor.fetchone()
        
        # Get project ID
        project_id = task['project_id']
        
        # Get current resources
        cursor.execute('''
            SELECT tr.*, u.username, u.id as user_id 
            FROM task_resources tr 
            JOIN users u ON tr.user_id = u.id 
            WHERE tr.task_id = %s
        ''', (task_id,))
        current_resources = cursor.fetchall()
        
        # Get all available users for assignment
        cursor.execute('SELECT id, username FROM users ORDER BY username')
        all_users = cursor.fetchall()
        
        # Handle form submission (POST request)
        if request.method == 'POST':
            try:
                # Create description of current resources
                current_resources_desc = ", ".join([f"{r['username']} as {r['designation']}" for r in current_resources])
                
                # Process form submission
                resources = request.form.getlist('resources[]')
                designations = request.form.getlist('designations[]')
                
                # Remove all current resources
                cursor.execute('DELETE FROM task_resources WHERE task_id = %s', (task_id,))
                
                # Add new resources
                new_resources_desc = []
                for i in range(len(resources)):
                    if resources[i] and designations[i]:
                        cursor.execute('''
                            INSERT INTO task_resources 
                            (task_id, user_id, designation) 
                            VALUES (%s, %s, %s)
                        ''', (task_id, resources[i], designations[i]))
                        
                        # Get username for resource description
                        cursor.execute('SELECT username FROM users WHERE id = %s', (resources[i],))
                        username = cursor.fetchone()['username']
                        new_resources_desc.append(f"{username} as {designations[i]}")
                
                # Create description of new resources
                new_resources_str = ", ".join(new_resources_desc)
                
                # Update project version
                description = f"Updated resources for task '{task['task_name']}'"
                update_project_version(
                    conn, cursor, project_id,
                    'resource',
                    description,
                    current_resources_desc,
                    new_resources_str
                )
                
                conn.commit()
                
                # Redirect back to task details
                return redirect(url_for('task_details', task_id=task_id))
                
            except Exception as e:
                conn.rollback()
                print(f"Error updating resources: {e}")
                # You might want to add flash message here to show error
                
        # For GET request, render the template with current data
        cursor.close()
        conn.close()
        
        # Render the update resources form template
        return render_template('update_task_resources.html', 
                              task=task, 
                              current_resources=current_resources,
                              all_users=all_users)
    
    # User is not authorized, redirect to task details page
    return redirect(url_for('task_details', task_id=task_id))
