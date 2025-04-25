from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime, timedelta
import calendar


resource_utilization_bp = Blueprint('resource_utilization', __name__)






# Resource Utilization Report Route
@resource_utilization_bp.route('/resource_utilization')
def resource_utilization():
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Get date parameters or use current month
        month = request.args.get('month', datetime.now().month, type=int)
        year = request.args.get('year', datetime.now().year, type=int)
        
        # Calculate first and last day of month
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1).date() - timedelta(days=1)
        
        # Fetch team members
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username FROM users WHERE user_type = "team_member"')
        team_members = cursor.fetchall()
        
        # Calculate utilization for each team member
        utilization_data = []
        for member in team_members:
            # Get total available hours
            cursor.execute('''
                SELECT SUM(available_hours) as total_available 
                FROM resource_availability 
                WHERE user_id = %s AND date BETWEEN %s AND %s
            ''', (member['id'], first_day, last_day))
            available_result = cursor.fetchone()
            
            # Calculate working days in month (excluding weekends)
            working_days = 0
            current_date = first_day
            while current_date <= last_day:
                if current_date.weekday() < 5:  # Monday to Friday
                    working_days += 1
                current_date += timedelta(days=1)
            
            # Default available hours (8 hours per working day)
            default_available = working_days * 8
            
            # Use custom availability if set, otherwise use default
            total_available = available_result['total_available'] if available_result['total_available'] else default_available
            
            # Get logged hours
            cursor.execute('''
                SELECT SUM(hours_worked) as total_logged 
                FROM time_entries 
                WHERE user_id = %s AND entry_date BETWEEN %s AND %s AND status IN ('submitted', 'approved')
            ''', (member['id'], first_day, last_day))
            logged_result = cursor.fetchone()
            total_logged = logged_result['total_logged'] if logged_result['total_logged'] else 0
            
            # Calculate utilization percentage
            utilization = (total_logged / total_available * 100) if total_available > 0 else 0
            
            # Get project allocation breakdown
            cursor.execute('''
                SELECT p.project_name, SUM(te.hours_worked) as project_hours
                FROM time_entries te
                JOIN tasks t ON te.task_id = t.id
                JOIN projects p ON t.project_id = p.id
                WHERE te.user_id = %s AND te.entry_date BETWEEN %s AND %s AND te.status IN ('submitted', 'approved')
                GROUP BY p.id
                ORDER BY project_hours DESC
            ''', (member['id'], first_day, last_day))
            project_allocation = cursor.fetchall()
            
            utilization_data.append({
                'user_id': member['id'],
                'username': member['username'],
                'available_hours': total_available,
                'logged_hours': total_logged,
                'utilization': round(utilization, 2),
                'project_allocation': project_allocation
            })
        
        # Navigate to previous/next month
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        
        cursor.close()
        conn.close()
        
        # Return template
        return render_template('resource_utilization.html',
                               month=month,
                               year=year,
                               month_name=calendar.month_name[month],
                               prev_month=prev_month,
                               prev_year=prev_year,
                               next_month=next_month,
                               next_year=next_year,
                               utilization_data=utilization_data)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home.home'))