from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime, timedelta
import calendar

import re



video_conferences_bp = Blueprint('video_conferences', __name__)











# Helper function to create activity
def create_activity(user_id, project_id=None, task_id=None, activity_type=None, description=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO activities 
        (user_id, project_id, task_id, activity_type, description) 
        VALUES (%s, %s, %s, %s, %s)
    ''', (user_id, project_id, task_id, activity_type, description))
    conn.commit()
    cursor.close()
    conn.close()



# Helper function to extract mentions from text
def extract_mentions(text):
    # Look for @username pattern
    mentions = re.findall(r'@(\w+)', text)
    return mentions



# Helper function to create notification
def create_notification(user_id, content, link=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notifications 
        (user_id, content, link) 
        VALUES (%s, %s, %s)
    ''', (user_id, content, link))
    conn.commit()
    cursor.close()
    conn.close()

# Helper function to create mention
def create_mention(user_id, mentioned_by, content_type, content_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO mentions 
        (user_id, mentioned_by, content_type, content_id) 
        VALUES (%s, %s, %s, %s)
    ''', (user_id, mentioned_by, content_type, content_id))
    conn.commit()
    cursor.close()
    conn.close()



@video_conferences_bp.route('/video_conferences')
def video_conferences():
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch upcoming conferences the user is invited to
    cursor.execute('''
        SELECT vc.*, u.username as creator_name, p.project_name, t.task_name,
        (SELECT COUNT(*) FROM video_conference_participants WHERE conference_id = vc.id) as participant_count
        FROM video_conferences vc
        JOIN users u ON vc.created_by = u.id
        LEFT JOIN projects p ON vc.project_id = p.id
        LEFT JOIN tasks t ON vc.task_id = t.id
        JOIN video_conference_participants vcp ON vc.id = vcp.conference_id
        WHERE vcp.user_id = %s AND vc.scheduled_start >= NOW()
        ORDER BY vc.scheduled_start
    ''', (session['id'],))
    upcoming_conferences = cursor.fetchall()
    
    # Fetch past conferences the user was invited to
    cursor.execute('''
        SELECT vc.*, u.username as creator_name, p.project_name, t.task_name,
        (SELECT COUNT(*) FROM video_conference_participants WHERE conference_id = vc.id) as participant_count
        FROM video_conferences vc
        JOIN users u ON vc.created_by = u.id
        LEFT JOIN projects p ON vc.project_id = p.id
        LEFT JOIN tasks t ON vc.task_id = t.id
        JOIN video_conference_participants vcp ON vc.id = vcp.conference_id
        WHERE vcp.user_id = %s AND vc.scheduled_start < NOW()
        ORDER BY vc.scheduled_start DESC
    ''', (session['id'],))
    past_conferences = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('video_conferences.html', upcoming_conferences=upcoming_conferences, past_conferences=past_conferences)

@video_conferences_bp.route('/create_video_conference', methods=['GET', 'POST'])
def create_video_conference():
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch projects for dropdown
    if session['user_type'] == 'admin':
        cursor.execute('SELECT id, project_name FROM projects ORDER BY project_name')
    elif session['user_type'] == 'pm':
        cursor.execute('SELECT id, project_name FROM projects WHERE pm_id = %s ORDER BY project_name', (session['id'],))
    else:
        cursor.execute('''
            SELECT DISTINCT p.id, p.project_name 
            FROM projects p 
            JOIN tasks t ON p.id = t.project_id 
            JOIN task_resources tr ON t.id = tr.task_id 
            WHERE tr.user_id = %s
            ORDER BY p.project_name
        ''', (session['id'],))
    projects = cursor.fetchall()
    
    # Fetch all users
    cursor.execute('SELECT id, username FROM users ORDER BY username')
    users = cursor.fetchall()
    
    # Handle form submission
    if request.method == 'POST':
        conference_name = request.form['conference_name']
        project_id = request.form.get('project_id')
        if project_id == '':
            project_id = None
        
        task_id = request.form.get('task_id')
        if task_id == '':
            task_id = None
            
        meeting_link = request.form['meeting_link']
        scheduled_start = request.form['scheduled_start']
        scheduled_end = request.form['scheduled_end']
        
        # Create video conference
        cursor.execute('''
            INSERT INTO video_conferences 
            (created_by, project_id, task_id, conference_name, meeting_link, scheduled_start, scheduled_end) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (session['id'], project_id, task_id, conference_name, meeting_link, scheduled_start, scheduled_end))
        conn.commit()
        
        conference_id = cursor.lastrowid
        
        # Add participants
        participants = request.form.getlist('participants')
        for user_id in participants:
            cursor.execute('''
                INSERT INTO video_conference_participants
                (conference_id, user_id)
                VALUES (%s, %s)
            ''', (conference_id, user_id))
            
            # Create notification for each participant
            if int(user_id) != session['id']:
                notification_content = f"{session['username']} invited you to a video conference: {conference_name}"
                link = f"/video_conference/{conference_id}"
                create_notification(user_id, notification_content, link)
        
        conn.commit()
        
        # Log activity
        activity_description = f"Created video conference '{conference_name}'"
        create_activity(session['id'], project_id, task_id, 'video_conference_create', activity_description)
        
        cursor.close()
        conn.close()
        
        flash('Video conference created successfully!')
        return redirect(url_for('video_conferences.video_conferences'))
    
    cursor.close()
    conn.close()
    
    return render_template('create_video_conference.html', projects=projects, users=users)

@video_conferences_bp.route('/video_conference/<int:conference_id>')
def video_conference_details(conference_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch conference details
    cursor.execute('''
        SELECT vc.*, u.username as creator_name, p.project_name, t.task_name
        FROM video_conferences vc
        JOIN users u ON vc.created_by = u.id
        LEFT JOIN projects p ON vc.project_id = p.id
        LEFT JOIN tasks t ON vc.task_id = t.id
        WHERE vc.id = %s
    ''', (conference_id,))
    conference = cursor.fetchone()
    
    if not conference:
        cursor.close()
        conn.close()
        flash('Conference not found!')
        return redirect(url_for('video_conferences'))
    
    # Check if user is a participant
    cursor.execute('''
        SELECT * FROM video_conference_participants
        WHERE conference_id = %s AND user_id = %s
    ''', (conference_id, session['id']))
    is_participant = cursor.fetchone() is not None
    
    if not is_participant and conference['created_by'] != session['id'] and session['user_type'] != 'admin':
        cursor.close()
        conn.close()
        flash('You are not invited to this conference!')
        return redirect(url_for('video_conferences'))
    
    # Fetch participants
    cursor.execute('''
        SELECT vcp.*, u.username
        FROM video_conference_participants vcp
        JOIN users u ON vcp.user_id = u.id
        WHERE vcp.conference_id = %s
        ORDER BY u.username
    ''', (conference_id,))
    participants = cursor.fetchall()
    
    # Mark as attended if joining
    if conference['status'] == 'in_progress' and is_participant:
        cursor.execute('''
            UPDATE video_conference_participants
            SET attended = 1
            WHERE conference_id = %s AND user_id = %s
        ''', (conference_id, session['id']))
        conn.commit()
    
    cursor.close()
    conn.close()
    
    return render_template('video_conference_details.html', conference=conference, participants=participants, is_participant=is_participant)

@video_conferences_bp.route('/video_conference/<int:conference_id>/update_status', methods=['POST'])
def update_conference_status(conference_id):
    # Check if user is logged in and is creator or admin
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    status = request.form['status']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch conference details
    cursor.execute('SELECT * FROM video_conferences WHERE id = %s', (conference_id,))
    conference = cursor.fetchone()
    
    if not conference:
        cursor.close()
        conn.close()
        flash('Conference not found!')
        return redirect(url_for('video_conferences'))
    
    if conference['created_by'] != session['id'] and session['user_type'] != 'admin':
        cursor.close()
        conn.close()
        flash('You do not have permission to update this conference!')
        return redirect(url_for('video_conferences.video_conference_details', conference_id=conference_id))
    
    # Update status
    cursor.execute('UPDATE video_conferences SET status = %s WHERE id = %s', (status, conference_id))
    conn.commit()
    
    # Notify participants if starting
    if status == 'in_progress':
        cursor.execute('''
            SELECT vcp.user_id
            FROM video_conference_participants vcp
            WHERE vcp.conference_id = %s AND vcp.user_id != %s
        ''', (conference_id, session['id']))
        participants = cursor.fetchall()
        
        for participant in participants:
            notification_content = f"Video conference '{conference['conference_name']}' has started"
            link = f"/video_conference/{conference_id}"
            create_notification(participant['user_id'], notification_content, link)
    
    # Log activity
    activity_description = f"Updated video conference '{conference['conference_name']}' status to {status}"
    create_activity(session['id'], conference['project_id'], conference['task_id'], 'video_conference_update', activity_description)
    
    cursor.close()
    conn.close()
    
    flash('Conference status updated successfully!')
    return redirect(url_for('video_conferences.video_conference_details', conference_id=conference_id))