from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import random
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your_secret_key'

# MySQL configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Sourav0978'
app.config['MYSQL_DB'] = 'project_management'

# Initialize MySQL
mysql = MySQL(app)

# Helper function to send email
def send_password_reset_email(email, new_password):
    sender_email = "sourav2473486@gmail.com"
    password = "sourav0987"
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset"
    message["From"] = sender_email
    message["To"] = email
    
    text = f"""
    Hello,
    
    Your password has been reset. Your new password is: {new_password}
    
    Please log in and change your password.
    
    Best regards,
    Project Management System
    """
    
    part = MIMEText(text, "plain")
    message.attach(part)
    
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(e)
        return False

# Login route
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong
    msg = ''
    
    # Check if "username" and "password" POST requests exist
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        user_type = request.form.get('user_type', 'team_member')
        
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND user_type = %s', (username, user_type))
        
        # Fetch one record
        account = cursor.fetchone()
        
        # If account exists in accounts table in our database
        if account:
            # Check password - handle both Werkzeug format and plain hashes
            password_correct = False
            try:
                password_correct = check_password_hash(account['password'], password)
            except ValueError:
                # If the hash format is invalid, try direct comparison (for development only)
                if account['password'] == 'admin123' and username == 'admin':
                    password_correct = True
                elif account['password'] == 'pm123' and username == 'pm':
                    password_correct = True
                elif account['password'] == 'team123' and username == 'team':
                    password_correct = True
            
            if password_correct:
                # Create session data
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['user_type'] = account['user_type']
                
                # Check if it's first login
                if account['first_login'] == 1:
                    # Redirect to change    password page
                    return redirect(url_for('change_password'))
                else:
                    # Redirect to home page
                    return redirect(url_for('home'))
        
        # Account doesn't exist or password incorrect
        msg = 'Incorrect username/password!'
    print(generate_password_hash('team123'))
    # Return template
    return render_template('login.html', msg=msg)

# Change password route
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    # Check if user is logged in
    if 'loggedin' in session:
        # Output message
        msg = ''
        
        # Check if "password" and "confirm_password" POST requests exist
        if request.method == 'POST' and 'password' in request.form and 'confirm_password' in request.form:
            # Create variables for easy access
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            
            # If password and confirm_password match
            if password == confirm_password:
                # Hash the password
                hashed_password = generate_password_hash(password)
                
                # Update the password in the database
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute('UPDATE users SET password = %s, first_login = 0 WHERE id = %s', (hashed_password, session['id']))
                mysql.connection.commit()
                
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Passwords don't match
                msg = 'Passwords do not match!'
        
        # Return template
        return render_template('change_password.html', msg=msg)
    
    # User is not logged in, redirect to login page
    return redirect(url_for('login'))

# Forgot password route
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    # Output message
    msg = ''
    
    # Check if "email" POST request exists
    if request.method == 'POST' and 'email' in request.form:
        # Create variables for easy access
        email = request.form['email']
        
        # Check if email exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        
        # Fetch one record
        account = cursor.fetchone()
        
        # If account exists
        if account:
            # Generate a random password
            new_password = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(8))
            
            # Hash the password
            hashed_password = generate_password_hash(new_password)
            
            # Update the password in the database
            cursor.execute('UPDATE users SET password = %s, first_login = 1 WHERE id = %s', (hashed_password, account['id']))
            mysql.connection.commit()
            
            # Send email
            if send_password_reset_email(email, new_password):
                msg = 'Password reset email sent!'
            else:
                msg = 'Failed to send password reset email!'
        else:
            # Email doesn't exist
            msg = 'Email does not exist!'
    
    # Return template
    return render_template('forgot_password.html', msg=msg)

# Home route
@app.route('/home')
def home():
    # Check if user is logged in
    if 'loggedin' in session:
        # Fetch projects
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        if session['user_type'] == 'admin':
            # Admin can see all projects
            cursor.execute('SELECT * FROM projects')
        elif session['user_type'] == 'pm':
            # PM can see projects they manage
            cursor.execute('SELECT * FROM projects WHERE pm_id = %s', (session['id'],))
        else:
            # Team members can see projects they are assigned to
            cursor.execute('''
                SELECT DISTINCT p.* 
                FROM projects p 
                JOIN tasks t ON p.id = t.project_id 
                JOIN task_resources tr ON t.id = tr.task_id 
                WHERE tr.user_id = %s
            ''', (session['id'],))
        
        projects = cursor.fetchall()
        
        # Return template
        return render_template('home.html', username=session['username'], user_type=session['user_type'], projects=projects)
    
    # User is not logged in, redirect to login page
    return redirect(url_for('login'))

# Project definition route
@app.route('/define_project', methods=['GET', 'POST'])
def define_project():
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Output message
        msg = ''
        
        # Fetch project managers for dropdown
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT id, username FROM users WHERE user_type = "pm"')
        project_managers = cursor.fetchall()
        
        # Check if form is submitted
        if request.method == 'POST':
            # Create variables for easy access
            project_name = request.form['project_name']
            project_description = request.form.get('project_description', '')
            start_date = request.form['start_date']
            end_date = request.form['end_date']
            project_type = request.form['project_type']
            
            # Check project type specific fields
            if project_type == 'fixed':
                total_amount = request.form['total_amount']
                per_month_billing = 0
            else:  # T&M
                total_amount = 0
                per_month_billing = request.form['per_month_billing']
            
            pm_id = request.form['pm_id']
            po_number = request.form.get('po_number', '')
            # In a real app, handle file upload for SOW
            # sow_attachment = request.files['sow_attachment']
            status = 'Entered'  # Default status
            
            # Generate a 5-digit project ID
            project_id = ''.join(random.choice('0123456789') for i in range(5))
            
            # Insert project into database
            cursor.execute('''
                INSERT INTO projects 
                (project_id, project_name, description, start_date, end_date, project_type, 
                total_amount, per_month_billing, pm_id, po_number, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (project_id, project_name, project_description, start_date, end_date, 
                 project_type, total_amount, per_month_billing, pm_id, po_number, status))
            mysql.connection.commit()
            
            # Redirect to home page
            msg = 'Project created successfully!'
            return redirect(url_for('home'))
        
        # Return template
        return render_template('define_project.html', msg=msg, project_managers=project_managers)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home'))

# Search project route
@app.route('/search_project', methods=['GET', 'POST'])
def search_project():
    # Check if user is logged in
    if 'loggedin' in session:
        # Output message
        msg = ''
        projects = []
        
        # Check if form is submitted
        if request.method == 'POST':
            # Create variables for easy access
            search_term = request.form['search_term']
            
            # Search for projects
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            
            # Different queries based on user type
            if session['user_type'] == 'admin':
                cursor.execute('''
                    SELECT * FROM projects 
                    WHERE project_name LIKE %s OR project_id LIKE %s OR description LIKE %s
                ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            elif session['user_type'] == 'pm':
                cursor.execute('''
                    SELECT * FROM projects 
                    WHERE pm_id = %s AND (project_name LIKE %s OR project_id LIKE %s OR description LIKE %s)
                ''', (session['id'], f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            else:
                cursor.execute('''
                    SELECT DISTINCT p.* 
                    FROM projects p 
                    JOIN tasks t ON p.id = t.project_id 
                    JOIN task_resources tr ON t.id = tr.task_id 
                    WHERE tr.user_id = %s AND (p.project_name LIKE %s OR p.project_id LIKE %s OR p.description LIKE %s)
                ''', (session['id'], f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
            
            projects = cursor.fetchall()
            
            if not projects:
                msg = 'No projects found!'
        
        # Return template
        return render_template('search_project.html', msg=msg, projects=projects)
    
    # User is not logged in, redirect to login page
    return redirect(url_for('login'))

# Project details route
@app.route('/project/<int:project_id>')
def project_details(project_id):
    # Check if user is logged in
    if 'loggedin' in session:
        # Fetch project details
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
        project = cursor.fetchone()
        
        # Fetch project manager details
        cursor.execute('SELECT username FROM users WHERE id = %s', (project['pm_id'],))
        pm = cursor.fetchone()
        
        # Fetch tasks
        cursor.execute('SELECT * FROM tasks WHERE project_id = %s ORDER BY id', (project_id,))
        tasks = cursor.fetchall()
        
        # Calculate project duration in days
        start_date = datetime.datetime.strptime(str(project['start_date']), '%Y-%m-%d')
        end_date = datetime.datetime.strptime(str(project['end_date']), '%Y-%m-%d')
        project_duration = (end_date - start_date).days
        
        # Return template
        return render_template('project_details.html', project=project, pm=pm, tasks=tasks, project_duration=project_duration)
    
    # User is not logged in, redirect to login page
    return redirect(url_for('login'))

# Create task route
@app.route('/project/<int:project_id>/create_task', methods=['GET', 'POST'])
def create_task(project_id):
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Fetch project details
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
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
            
            # Insert task into database
            cursor.execute('''
                INSERT INTO tasks 
                (project_id, task_name, description, start_date, end_date, dependency_days, 
                parent_task_id, is_active, status, color) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (project_id, task_name, task_description, start_date, end_date, 
                 dependency_days, parent_task_id, is_active, status, 'green'))
            mysql.connection.commit()
            
            # Get the inserted task ID
            task_id = cursor.lastrowid
            
            # Assign resources to the task
            resources = request.form.getlist('resources[]')
            designations = request.form.getlist('designations[]')
            
            for i in range(len(resources)):
                cursor.execute('''
                    INSERT INTO task_resources 
                    (task_id, user_id, designation) 
                    VALUES (%s, %s, %s)
                ''', (task_id, resources[i], designations[i]))
            mysql.connection.commit()
            
            # Redirect to project details page
            return redirect(url_for('project_details', project_id=project_id))
        
        # Return template
        return render_template('create_task.html', project=project, existing_tasks=existing_tasks, team_members=team_members)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home'))

# Task details route
@app.route('/task/<int:task_id>')
def task_details(task_id):
    # Check if user is logged in
    if 'loggedin' in session:
        # Fetch task details
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
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
        
        # Calculate task duration in hours
        start_date = datetime.datetime.strptime(str(task['start_date']), '%Y-%m-%d')
        end_date = datetime.datetime.strptime(str(task['end_date']), '%Y-%m-%d')
        task_hours = (end_date - start_date).days * 8  # Assuming 8 working hours per day
        
        # Return template
        return render_template('task_details.html', task=task, project=project, resources=resources, comments=comments, task_hours=task_hours)
    
    # User is not logged in, redirect to login page
    return redirect(url_for('login'))

# Add comment route
@app.route('/task/<int:task_id>/add_comment', methods=['POST'])
def add_comment(task_id):
    # Check if user is logged in
    if 'loggedin' in session:
        # Create variables for easy access
        comment_text = request.form['comment_text']
        
        # Insert comment into database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            INSERT INTO comments 
            (task_id, user_id, comment_text, created_at) 
            VALUES (%s, %s, %s, %s)
        ''', (task_id, session['id'], comment_text, datetime.datetime.now()))
        mysql.connection.commit()
        
        # Update task color to red
        cursor.execute('UPDATE tasks SET color = %s WHERE id = %s', ('red', task_id))
        mysql.connection.commit()
        
        # Redirect back to task details
        return redirect(url_for('task_details', task_id=task_id))
    
    # User is not logged in, redirect to login page
    return redirect(url_for('login'))

# Update task route
@app.route('/task/<int:task_id>/update', methods=['POST'])
def update_task(task_id):
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Create variables for easy access
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        status = request.form['status']
        
        # Update task in database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('''
            UPDATE tasks 
            SET start_date = %s, end_date = %s, status = %s, color = %s 
            WHERE id = %s
        ''', (start_date, end_date, status, 'green', task_id))
        mysql.connection.commit()
        
        # Fetch task details to get project_id
        cursor.execute('SELECT project_id FROM tasks WHERE id = %s', (task_id,))
        task = cursor.fetchone()
        
        # Redirect back to project details
        return redirect(url_for('project_details', project_id=task['project_id']))
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home'))

# Gantt chart route
@app.route('/project/<int:project_id>/gantt')
def gantt_chart(project_id):
    # Check if user is logged in
    if 'loggedin' in session:
        # Fetch project details
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
        project = cursor.fetchone()
        
        # Fetch tasks
        cursor.execute('SELECT * FROM tasks WHERE project_id = %s ORDER BY id', (project_id,))
        tasks = cursor.fetchall()
        
        # Return template
        return render_template('gantt_chart.html', project=project, tasks=tasks)
    
    # User is not logged in, redirect to login page
    return redirect(url_for('login'))

# Logout route
@app.route('/logout')
def logout():
    # Remove session data
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('user_type', None)
    
    # Redirect to login page
    return redirect(url_for('login'))

# Main function
if __name__ == '__main__':
    app.run(debug=True)