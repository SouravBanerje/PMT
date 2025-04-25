from flask import Blueprint, Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection  



search_project_bp = Blueprint('search_project', __name__)


# Search project route
@search_project_bp.route('/search_project', methods=['GET', 'POST'])
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
            conn = get_db_connection()
            cursor = conn.cursor()
            
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
            
            cursor.close()
            conn.close()
            
            if not projects:
                msg = 'No projects found!'
        
        # Return template
        return render_template('search_project.html', msg=msg, projects=projects)
    
    # User is not logged in, redirect to login page
    return redirect(url_for('auth.login'))