from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime, timedelta




update_time_entry_status_bp = Blueprint('update_time_entry_status', __name__)










# # Update Time Entry Status Route
# @update_time_entry_status_bp.route('/update_time_entry_status', methods=['POST'])
# def update_time_entry_status():
#     # Check if user is logged in and is admin or PM
#     if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
#         # Get form data
#         entry_id = request.form['entry_id']
#         status = request.form['status']
        
#         # Update status in database
#         conn = get_db_connection()
#         cursor = conn.cursor()
        
#         cursor.execute('UPDATE time_entries SET status = %s WHERE id = %s', (status, entry_id))
#         conn.commit()
        
#         # Get entry date to return to correct week
#         cursor.execute('SELECT entry_date FROM time_entries WHERE id = %s', (entry_id,))
#         entry = cursor.fetchone()
        
#         cursor.close()
#         conn.close()
        
#         # Redirect back to time tracking
#         start_date = (entry['entry_date'] - timedelta(days=entry['entry_date'].weekday())).strftime('%Y-%m-%d')
#         return redirect(url_for('time_tracking.time_tracking', start_date=start_date))
    
#     # User is not authorized, redirect to home page
#     return redirect(url_for('home.home'))

@update_time_entry_status_bp.route('/update_time_entry_status', methods=['POST'])
def update_time_entry_status():
    # Check if user is logged in and has approve permissions
    if 'loggedin' in session and session['user_type'] in ['admin', 'pm']:
        # Get form data
        entry_id = request.form['entry_id'] 
        status = request.form['status']  # 'approved' or 'rejected'
        
        # Update entry status
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE time_entries
            SET status = %s
            WHERE id = %s
        ''', (status, entry_id))
        
        # Get the entry date to redirect back to the right week
        cursor.execute('''
            SELECT entry_date FROM time_entries WHERE id = %s
        ''', (entry_id,))
        
        entry = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Calculate the week start date for the redirect
        if entry:
            entry_date = entry['entry_date']
            start_date = (entry_date - timedelta(days=entry_date.weekday())).strftime('%Y-%m-%d')
        else:
            # Fallback to current week if entry not found
            today = datetime.now().date()
            start_date = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
        
        flash(f'Time entry {status} successfully')
        return redirect(url_for('time_tracking.time_tracking', start_date=start_date))
    
    # User is not logged in or doesn't have permissions
    return redirect(url_for('auth.login'))

