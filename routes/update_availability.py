from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime




update_availability_bp = Blueprint('update_availability', __name__)






# Update Resource Availability Route
@update_availability_bp.route('/update_availability', methods=['POST'])
def update_availability():
    # Check if user is logged in
    if 'loggedin' in session:
        # Get form data
        user_id = request.form['user_id']
        date = request.form['date']
        available_hours = float(request.form['available_hours'])
        reason = request.form.get('reason', '')
        
        # Check if user is authorized (can only update own availability unless admin/PM)
        if str(session['id']) != str(user_id) and session['user_type'] not in ['admin', 'pm']:
            flash('You are not authorized to update this resource\'s availability')
            return redirect(url_for('resource_calendar'))
        
        # Update availability in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if entry exists
        cursor.execute('SELECT id FROM resource_availability WHERE user_id = %s AND date = %s', 
                      (user_id, date))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute('''
                UPDATE resource_availability 
                SET available_hours = %s, reason = %s 
                WHERE user_id = %s AND date = %s
            ''', (available_hours, reason, user_id, date))
        else:
            # Insert new record
            cursor.execute('''
                INSERT INTO resource_availability 
                (user_id, date, available_hours, reason) 
                VALUES (%s, %s, %s, %s)
            ''', (user_id, date, available_hours, reason))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Redirect back to calendar
        return redirect(url_for('resource_calendar.resource_calendar', month=datetime.strptime(date, '%Y-%m-%d').month,
                                year=datetime.strptime(date, '%Y-%m-%d').year))
    
    # User is not logged in, redirect to login page
    return redirect(url_for('auth.login'))


