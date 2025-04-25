from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql.cursors
import re
import random   
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import calendar
from flask import jsonify
from pymysql.cursors import DictCursor
import json
from routes import init_app
from utils.db import get_db_connection

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'




init_app(app)





# Task details route
@app.route('/task/<int:task_id>')
def task_details(task_id):
    # Check if user is logged in
    if 'loggedin' in session:
        # Fetch task details
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
        task = cursor.fetchone()
        
        # Fetch project details
        cursor.execute('SELECT * FROM projects WHERE id = %s', (task['project_id'],))
        project = cursor.fetchone()
        
        # Fetch assigned resources
        cursor.execute('''
            SELECT tr.*, u.username 
            FROM task_resources tr 
            JOIN users u ON tr.user_id = u.id 
            WHERE tr.task_id = %s
        ''', (task_id,))
        resources = cursor.fetchall()
        
        # Fetch comments
        cursor.execute('''
            SELECT c.*, u.username 
            FROM comments c 
            JOIN users u ON c.user_id = u.id 
            WHERE c.task_id = %s 
            ORDER BY c.created_at
        ''', (task_id,))
        comments = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Calculate task duration in hours
        start_date =datetime.strptime(str(task['start_date']), '%Y-%m-%d')
        end_date = datetime.strptime(str(task['end_date']), '%Y-%m-%d')
        task_hours = (end_date - start_date).days * 8  # Assuming 8 working hours per day
        
        # Return template
        return render_template('task_details.html', task=task, project=project, 
                               resources=resources, comments=comments, task_hours=task_hours)
    
    # User is not logged in, redirect to login page
    return redirect(url_for('login'))






# Assign Resource Route
@app.route('/assign_resource', methods=['POST'])
def assign_resource():
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Get form data
        task_id = request.form['task_id']
        user_id = request.form['user_id']
        designation = request.form['designation']
        project_id = request.form['project_id']
        
        # Insert into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if already assigned
        cursor.execute('SELECT id FROM task_resources WHERE task_id = %s AND user_id = %s', 
                      (task_id, user_id))
        existing = cursor.fetchone()
        
        if not existing:
            cursor.execute('''
                INSERT INTO task_resources 
                (task_id, user_id, designation) 
                VALUES (%s, %s, %s)
            ''', (task_id, user_id, designation))
            conn.commit()
        
        cursor.close()
        conn.close()
        
        # Redirect back to optimization page
        return redirect(url_for('resource_optimization', project_id=project_id))
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home'))

# Remove Resource Route
@app.route('/remove_resource', methods=['POST'])
def remove_resource():
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Get form data
        resource_id = request.form['resource_id']
        project_id = request.form['project_id']
        
        # Delete from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM task_resources WHERE id = %s', (resource_id,))
        conn.commit()
        cursor.close()
        conn.close()
        
        # Redirect back to optimization page
        return redirect(url_for('resource_optimization', project_id=project_id))
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home'))


















# Add notifications count API
@app.route('/api/notifications/count')
def notifications_count():
    # Check if user is logged in
    if 'loggedin' not in session:
        return jsonify({'count': 0})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Count unread notifications
    cursor.execute('SELECT COUNT(*) as count FROM notifications WHERE user_id = %s AND is_read = 0', (session['id'],))
    notification_count = cursor.fetchone()['count']
    
    # Count unread mentions
    cursor.execute('SELECT COUNT(*) as count FROM mentions WHERE user_id = %s AND is_read = 0', (session['id'],))
    mention_count = cursor.fetchone()['count']
    
    cursor.close()
    conn.close()
    
    return jsonify({
        'notification_count': notification_count,
        'mention_count': mention_count,
        'total_count': notification_count + mention_count
    })




# Project version report route

# Main function
if __name__ == '__main__':
    app.run(debug=True)



