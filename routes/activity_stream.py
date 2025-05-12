from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime, timedelta


activity_stream_bp = Blueprint('activity_stream', __name__)




@activity_stream_bp.route('/activity_stream')
def activity_stream():
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch global activities (admin only)
    global_activities = []
    if session['user_type'] == 'admin':
        cursor.execute('''
            SELECT a.*, u.username, p.project_name, t.task_name
            FROM activities a
            JOIN users u ON a.user_id = u.id
            LEFT JOIN projects p ON a.project_id = p.id
            LEFT JOIN tasks t ON a.task_id = t.id
            ORDER BY a.created_at DESC
            LIMIT 100
        ''')
        global_activities = cursor.fetchall()
    
    # Fetch project activities (for PMs and their projects)
    project_activities = []
    if session['user_type'] == 'admin' or session['user_type'] == 'pm':
        if session['user_type'] == 'admin':
            cursor.execute('''
                SELECT a.*, u.username, p.project_name, t.task_name
                FROM activities a
                JOIN users u ON a.user_id = u.id
                JOIN projects p ON a.project_id = p.id
                LEFT JOIN tasks t ON a.task_id = t.id
                ORDER BY a.created_at DESC
                LIMIT 100
            ''')
        else:
            cursor.execute('''
                SELECT a.*, u.username, p.project_name, t.task_name
                FROM activities a
                JOIN users u ON a.user_id = u.id
                JOIN projects p ON a.project_id = p.id
                LEFT JOIN tasks t ON a.task_id = t.id
                WHERE p.pm_id = %s
                ORDER BY a.created_at DESC
                LIMIT 100
            ''', (session['id'],))
        project_activities = cursor.fetchall()
    
    # Fetch user's task activities
    cursor.execute('''
        SELECT a.*, u.username, p.project_name, t.task_name
        FROM activities a
        JOIN users u ON a.user_id = u.id
        LEFT JOIN projects p ON a.project_id = p.id
        LEFT JOIN tasks t ON a.task_id = t.id
        WHERE a.task_id IN (
            SELECT tr.task_id 
            FROM task_resources tr 
            WHERE tr.user_id = %s
        )
        ORDER BY a.created_at DESC
        LIMIT 100
    ''', (session['id'],))
    task_activities = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('activity_stream.html', 
                          global_activities=global_activities, 
                          project_activities=project_activities, 
                          task_activities=task_activities)