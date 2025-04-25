from flask import Flask, render_template, request, redirect, url_for, session, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime
from datetime import timedelta

capacity_planning_bp = Blueprint('capacity_planning', __name__)






# Capacity Planning Route
@capacity_planning_bp.route('/capacity_planning')
def capacity_planning():
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Get date parameters or use next 4 weeks
        today = datetime.now().date()
        start_date_str = request.args.get('start_date', today.strftime('%Y-%m-%d'))
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = start_date + timedelta(weeks=4) - timedelta(days=1)
        
        # Fetch team members
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if session['user_type'] == 'admin':
            cursor.execute('SELECT id, username FROM users WHERE user_type = "team_member"')
        else:  # PM - fetch team members assigned to their projects
            cursor.execute('''
                SELECT DISTINCT u.id, u.username
                FROM users u
                JOIN task_resources tr ON u.id = tr.user_id
                JOIN tasks t ON tr.task_id = t.id
                JOIN projects p ON t.project_id = p.id
                WHERE p.pm_id = %s AND u.user_type = "team_member"
            ''', (session['id'],))
        team_members = cursor.fetchall()
        
        # Generate list of dates for the period
        date_range = []
        delta = end_date - start_date
        for i in range(delta.days + 1):
            date = start_date + timedelta(days=i)
            date_range.append({
                'date': date,
                'week': (date - start_date).days // 7 + 1,
                'is_weekend': date.weekday() >= 5,
                'formatted': date.strftime('%Y-%m-%d')
            })
        
        # Group dates by week
        weeks = {}
        for date_info in date_range:
            week_num = date_info['week']
            if week_num not in weeks:
                weeks[week_num] = []
            weeks[week_num].append(date_info)
        
        # Fetch capacity data for each team member
        capacity_data = {}
        for member in team_members:
            # Get availability for each date
            availability = {}
            cursor.execute('''
                SELECT date, available_hours 
                FROM resource_availability 
                WHERE user_id = %s AND date BETWEEN %s AND %s
            ''', (member['id'], start_date, end_date))
            
            for row in cursor.fetchall():
                availability[row['date'].strftime('%Y-%m-%d')] = row['available_hours']
            
            # Get task assignments for each date
            assignments = {}
            cursor.execute('''
                SELECT t.id, t.task_name, t.start_date, t.end_date, p.project_name
                FROM tasks t
                JOIN projects p ON t.project_id = p.id
                JOIN task_resources tr ON t.id = tr.task_id
                WHERE tr.user_id = %s AND t.is_active = 1 AND
                      ((t.start_date <= %s AND t.end_date >= %s) OR
                       (t.start_date >= %s AND t.start_date <= %s))
            ''', (member['id'], end_date, start_date, start_date, end_date))
            
            tasks = cursor.fetchall()
            for task in tasks:
                task_start = max(task['start_date'], start_date)
                task_end = min(task['end_date'], end_date)
                
                # Calculate hours per day (simple distribution)
                task_days = (task_end - task_start).days + 1
                hours_per_day = 8 / task_days if task_days > 0 else 0  # Assume standard 8-hour day
                
                # Distribute hours across days
                current_date = task_start
                while current_date <= task_end:
                    date_str = current_date.strftime('%Y-%m-%d')
                    if date_str not in assignments:
                        assignments[date_str] = []
                    
                    assignments[date_str].append({
                        'task_id': task['id'],
                        'task_name': task['task_name'],
                        'project_name': task['project_name'],
                        'hours': hours_per_day
                    })
                    
                    current_date += timedelta(days=1)
            
            capacity_data[member['id']] = {
                'availability': availability,
                'assignments': assignments
            }
        
        # Calculate previous and next periods
        prev_period = (start_date - timedelta(weeks=4)).strftime('%Y-%m-%d')
        next_period = (start_date + timedelta(weeks=4)).strftime('%Y-%m-%d')
        
        cursor.close()
        conn.close()
        
        # Return template
        return render_template('capacity_planning.html',
                               team_members=team_members,
                               date_range=date_range,
                               weeks=weeks,
                               capacity_data=capacity_data,
                               start_date=start_date,
                               end_date=end_date,
                               prev_period=prev_period,
                               next_period=next_period)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home.home'))