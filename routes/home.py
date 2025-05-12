
from flask import Blueprint, Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection      



home_bp = Blueprint('home', __name__)




# Home route
@home_bp.route('/home')
def home():
    # Check if user is logged in
    if 'loggedin' in session:
        # Fetch projects
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        cursor.close()
        conn.close()
        
        # Return template
        return render_template('home.html', username=session['username'], 
                               user_type=session['user_type'], projects=projects)
    
    # User is not logged in, redirect to login page
    return redirect(url_for('auth.login'))