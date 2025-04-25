from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime
from datetime import timedelta


time_tracking_bp = Blueprint('time_tracking', __name__)





# Time Tracking Routes
@time_tracking_bp.route('/time_tracking')
def time_tracking():
    # Check if user is logged in
    if 'loggedin' in session:
        # Get date parameters or use current week
        today = datetime.now().date()
        start_date_str = request.args.get('start_date', (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d'))
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=6)
        
        # Fetch users based on permissions
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if session['user_type'] == 'admin' or session['user_type'] == 'pm':
            cursor.execute('SELECT id, username FROM users WHERE user_type = "team_member"')
            can_approve = True
        else:
            cursor.execute('SELECT id, username FROM users WHERE id = %s', (session['id'],))
            can_approve = False
        users = cursor.fetchall()
        
        # Fetch projects and tasks the user has access to
        tasks_by_user = {}
        for user in users:
            if session['user_type'] == 'admin':
                cursor.execute('''
                    SELECT t.id, t.task_name, p.id AS project_id, p.project_name
                    FROM tasks t
                    JOIN projects p ON t.project_id = p.id
                    JOIN task_resources tr ON t.id = tr.task_id AND tr.user_id = %s
                    ORDER BY p.project_name, t.task_name
                    ''', (user['id'],))
                
            elif session['user_type'] == 'pm':
                cursor.execute('''
                    SELECT t.id, t.task_name, p.id AS project_id, p.project_name
                    FROM tasks t
                    JOIN projects p ON t.project_id = p.id
                    JOIN task_resources tr ON t.id = tr.task_id AND tr.user_id = %s
                    WHERE p.pm_id = %s
                    ORDER BY p.project_name, t.task_name
                    ''', (user['id'], session['id']))
            else:
                cursor.execute('''
                    SELECT t.id, t.task_name, p.id AS project_id, p.project_name 
                    FROM tasks t
                    JOIN projects p ON t.project_id = p.id
                    JOIN task_resources tr ON t.id = tr.task_id AND tr.user_id = %s
                    ORDER BY p.project_name, t.task_name
                    ''', (user['id'],))
            tasks_by_user[user['id']] = cursor.fetchall()
        
        # Fetch time entries for the selected week
        time_entries = {}
        for user in users:
            cursor.execute('''
                SELECT * FROM time_entries 
                WHERE user_id = %s AND entry_date BETWEEN %s AND %s
                ORDER BY entry_date
            ''', (user['id'], start_date, end_date))
            
            # Group by date
            entries_by_date = {}
            for entry in cursor.fetchall():
                date_str = entry['entry_date'].strftime('%Y-%m-%d')
                if date_str not in entries_by_date:
                    entries_by_date[date_str] = []
                entries_by_date[date_str].append(entry)
            
            time_entries[user['id']] = entries_by_date
        
        cursor.close()
        conn.close()
        
        # Create date range for the week
        date_range = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            date_range.append({
                'date': date,
                'day': date.strftime('%a'),
                'is_weekend': date.weekday() >= 5,
                'is_today': date == today,
                'formatted': date.strftime('%Y-%m-%d')
            })
        
        # Calculate previous and next weeks
        prev_week = (start_date - timedelta(days=7)).strftime('%Y-%m-%d')
        next_week = (start_date + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Return template
        return render_template('time_tracking.html', 
                               users=users,
                               tasks_by_user=tasks_by_user,
                               time_entries=time_entries,
                               date_range=date_range,
                               start_date=start_date,
                               end_date=end_date,
                               prev_week=prev_week,
                               next_week=next_week,
                               can_approve=can_approve,
                               current_user_id=session['id'])
    
    # User is not logged in, redirect to login page
    return redirect(url_for('auth.login'))