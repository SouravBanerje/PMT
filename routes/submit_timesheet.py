
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime
from flask import Blueprint
from datetime import timedelta


submit_timesheet_bp = Blueprint('submit_timesheet', __name__)






# Submit Timesheet Route
@submit_timesheet_bp.route('/submit_timesheet', methods=['POST'])
def submit_timesheet():
    # Check if user is logged in
    if 'loggedin' in session:
        # Get form data
        user_id = request.form['user_id']
        start_date = request.form['start_date']
        
        # Check if user is authorized (can only submit own timesheet unless admin/PM)
        if str(session['id']) != str(user_id) and session['user_type'] not in ['admin', 'pm']:
            flash('You are not authorized to submit timesheets for this user')
            return redirect(url_for('time_tracking'))
        
        # Update status of all draft entries for this week
        conn = get_db_connection()
        cursor = conn.cursor()
        
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = start + timedelta(days=6)
        
        cursor.execute('''
            UPDATE time_entries 
            SET status = 'submitted' 
            WHERE user_id = %s AND entry_date BETWEEN %s AND %s AND status = 'draft'
        ''', (user_id, start, end))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Redirect back to time tracking
        return redirect(url_for('time_tracking.time_tracking', start_date=start_date))
    
    # User is not logged in, redirect to login page
    return redirect(url_for('auth.login'))