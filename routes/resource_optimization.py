from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime
from datetime import timedelta



resource_optimization_bp = Blueprint('resource_optimization', __name__)
















# Resource Allocation Optimization Route
@resource_optimization_bp.route('/resource_optimization')
def resource_optimization():
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Fetch active projects
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if session['user_type'] == 'admin':
            cursor.execute('''
                SELECT id, project_name 
                FROM projects 
                WHERE status = 'Approved & Active'
                ORDER BY project_name
            ''')
        else:  # PM
            cursor.execute('''
                SELECT id, project_name 
                FROM projects 
                WHERE status = 'Approved & Active' AND pm_id = %s
                ORDER BY project_name
            ''', (session['id'],))
        projects = cursor.fetchall()
        
        # Get selected project
        project_id = request.args.get('project_id', type=int)
        if project_id:
            # Fetch project details
            cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
            project = cursor.fetchone()
            
            # Fetch tasks for this project
            cursor.execute('''
                SELECT * FROM tasks 
                WHERE project_id = %s AND status != 'Completed'
                ORDER BY start_date
            ''', (project_id,))
            tasks = cursor.fetchall()
            
            # Fetch resources currently assigned to each task
            task_resources = {}
            for task in tasks:
                cursor.execute('''
                    SELECT tr.*, u.username 
                    FROM task_resources tr 
                    JOIN users u ON tr.user_id = u.id 
                    WHERE tr.task_id = %s
                ''', (task['id'],))
                task_resources[task['id']] = cursor.fetchall()
            
            # Find team members with the right skills for each task
            task_candidates = {}
            for task in tasks:
                # Determine skills needed for this task based on task name/description
                # This is a simple example - in a real system, you'd have task skills mapping
                keywords = task['task_name'].lower() + ' ' + (task['description'] or '').lower()
                
                # Query for team members with matching skills
                cursor.execute('''
                    SELECT DISTINCT u.id, u.username, COUNT(us.skill_id) as matching_skills,
                           AVG(us.proficiency_level) as avg_proficiency
                    FROM users u
                    JOIN user_skills us ON u.id = us.user_id
                    JOIN skills s ON us.skill_id = s.id
                    WHERE u.user_type = 'team_member' AND 
                          (s.skill_name IN ('Python', 'Java', 'Project Management', 'UI Design', 'Testing'))
                    GROUP BY u.id
                    ORDER BY matching_skills DESC, avg_proficiency DESC
                ''')
                candidates = cursor.fetchall()
                
                # Check current workload for each candidate
                for i, candidate in enumerate(candidates):
                    # Count overlapping tasks
                    cursor.execute('''
                        SELECT COUNT(*) as task_count
                        FROM task_resources tr
                        JOIN tasks t ON tr.task_id = t.id
                        WHERE tr.user_id = %s AND t.is_active = 1 AND
                              ((t.start_date <= %s AND t.end_date >= %s) OR
                               (t.start_date >= %s AND t.start_date <= %s))
                    ''', (candidate['id'], task['end_date'], task['start_date'], 
                          task['start_date'], task['end_date']))
                    workload = cursor.fetchone()
                    candidates[i]['current_workload'] = workload['task_count']
                
                task_candidates[task['id']] = candidates
            
            # Calculate overall resource allocation
            cursor.execute('''
                SELECT u.id, u.username, COUNT(tr.id) as assignment_count
                FROM users u
                LEFT JOIN task_resources tr ON u.id = tr.user_id
                LEFT JOIN tasks t ON tr.task_id = t.id AND t.is_active = 1
                WHERE u.user_type = 'team_member'
                GROUP BY u.id
                ORDER BY assignment_count DESC
            ''')
            resource_allocation = cursor.fetchall()
        else:
            project = None
            tasks = []
            task_resources = {}
            task_candidates = {}
            resource_allocation = []
        
        cursor.close()
        conn.close()
        
        # Return template
        return render_template('resource_optimization.html',
                               projects=projects,
                               selected_project=project,
                               tasks=tasks,
                               task_resources=task_resources,
                               task_candidates=task_candidates,
                               resource_allocation=resource_allocation)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home.home'))
