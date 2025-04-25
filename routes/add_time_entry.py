from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime, timedelta


add_time_entry_bp = Blueprint('add_time_entry', __name__)



# Add Time Entry Route
@add_time_entry_bp.route('/add_time_entry', methods=['POST'])
def add_time_entry():
    # Check if user is logged in
    if 'loggedin' in session:
        # Get form data
        user_id = request.form['user_id']
        task_id = request.form['task_id']
        entry_date = request.form['entry_date']
        hours_worked = float(request.form['hours_worked'])
        description = request.form.get('description', '')
        
        # Check if user is authorized (can only add own time entries unless admin/PM)
        if str(session['id']) != str(user_id) and session['user_type'] not in ['admin', 'pm']:
            flash('You are not authorized to add time entries for this user')
            return redirect(url_for('time_tracking'))
        
        # Insert time entry into database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO time_entries 
            (user_id, task_id, entry_date, hours_worked, description, status) 
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (user_id, task_id, entry_date, hours_worked, description, 'draft'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Redirect back to time tracking
        start_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
        start_date = (start_date - timedelta(days=start_date.weekday())).strftime('%Y-%m-%d')
        return redirect(url_for('time_tracking.time_tracking', start_date=start_date))
    
    # User is not logged in, redirect to login page
    return redirect(url_for('auth.login'))
