from flask import Flask, render_template, request, redirect, url_for, session, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime, timedelta
import calendar



resource_calendar_bp = Blueprint('resource_calendar', __name__)




# Resource Calendar Route
@resource_calendar_bp.route('/resource_calendar')
def resource_calendar():
    # Check if user is logged in
    if 'loggedin' in session:
        # Get month and year parameters or use current month
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Get first and last day of month
        first_day = datetime(year, month, 1)
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Fetch team members
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if session['user_type'] == 'admin' or session['user_type'] == 'pm':
            cursor.execute('SELECT id, username FROM users WHERE user_type = "team_member"')
        else:
            cursor.execute('SELECT id, username FROM users WHERE id = %s', (session['id'],))
        team_members = cursor.fetchall()
        
        # Fetch availability data
        availability_data = {}
        for member in team_members:
            cursor.execute('''
                SELECT date, available_hours, reason 
                FROM resource_availability 
                WHERE user_id = %s AND date BETWEEN %s AND %s
            ''', (member['id'], first_day, last_day))
            availability = {row['date'].strftime('%Y-%m-%d'): row for row in cursor.fetchall()}
            availability_data[member['id']] = availability
        
        # Fetch assigned tasks
        task_assignments = {}
        for member in team_members:
            cursor.execute('''
                SELECT t.id, t.task_name, t.start_date, t.end_date, p.project_name 
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                JOIN task_resources tr ON t.id = tr.task_id
                WHERE tr.user_id = %s AND 
                ((t.start_date <= %s AND t.end_date >= %s) OR
                (t.start_date >= %s AND t.start_date <= %s))
            ''', (member['id'], last_day, first_day, first_day, last_day))
            task_assignments[member['id']] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Create calendar data
        cal = calendar.monthcalendar(year, month)
        month_name = calendar.month_name[month]
        
        # Navigate to previous/next month
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        # Return template
        return render_template('resource_calendar.html', 
                               calendar_data=cal, 
                               month=month, 
                               year=year,
                               month_name=month_name,
                               prev_month=prev_month,
                               prev_year=prev_year,
                               next_month=next_month,
                               next_year=next_year,
                               team_members=team_members,
                               availability_data=availability_data,
                               task_assignments=task_assignments,
                               today=datetime.now().strftime('%Y-%m-%d'))
    
    # User is not logged in, redirect to login page
    return redirect(url_for('auth.login'))