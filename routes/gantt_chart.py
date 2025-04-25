from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime, timedelta



gantt_chart_bp = Blueprint('gantt_chart', __name__)




@gantt_chart_bp.route('/project/<int:project_id>/gantt')
def gantt_chart(project_id):
    if 'loggedin' in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch project
        cursor.execute('''
            SELECT 
                id, 
                project_name, 
                DATE_FORMAT(start_date, '%%Y-%%m-%%d') as start_date,
                DATE_FORMAT(end_date, '%%Y-%%m-%%d') as end_date
            FROM projects 
            WHERE id = %s
        ''', (project_id,))
        project = cursor.fetchone()
        
        # Fetch tasks and map status to appropriate colors
        cursor.execute('''
            SELECT 
                id,
                task_name,
                DATE_FORMAT(start_date, '%%Y-%%m-%%d') as start_date,
                DATE_FORMAT(end_date, '%%Y-%%m-%%d') as end_date,
                status,
                CASE 
                    WHEN status = 'Completed' THEN 'completed'
                    WHEN status = 'In Progress' THEN 'in-progress'
                    WHEN status = 'Pending' THEN 'delayed'
                    ELSE 'not-started'
                END as status_class
            FROM tasks 
            WHERE project_id = %s 
            ORDER BY start_date
        ''', (project_id,))
        tasks = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return render_template('gantt_chart.html', project=project, tasks=tasks)
    
    return redirect(url_for('auth.login'))