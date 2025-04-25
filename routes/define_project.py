from flask import Blueprint, Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import random


define_project_bp = Blueprint('define_project', __name__)

# Project definition route
@define_project_bp.route('/define_project', methods=['GET', 'POST'])
def define_project():
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Output message
        msg = ''
        
        # Fetch project managers for dropdown
        conn = get_db_connection()
        cursor = conn.cursor()
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
            conn.commit()
            
            # Redirect to home page
            msg = 'Project created successfully!'
            
            cursor.close()
            conn.close()
            return redirect(url_for('home.home'))
        
        cursor.close()
        conn.close()
        
        # Return template
        return render_template('define_project.html', msg=msg, project_managers=project_managers)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home.home'))
