from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime,timedelta
import re






notifications_bp = Blueprint('notifications', __name__)








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















@notifications_bp.route('/project/<int:project_id>/notifications')
def notifications(project_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    

    # Fetch project details
    cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
    project = cursor.fetchone()

    # Fetch unread notifications
    cursor.execute('''
        SELECT * FROM notifications
        WHERE user_id = %s AND is_read = 0
        ORDER BY created_at DESC
    ''', (session['id'],))
    unread_notifications = cursor.fetchall()
    
    # Fetch read notifications
    cursor.execute('''
        SELECT * FROM notifications
        WHERE user_id = %s AND is_read = 1
        ORDER BY created_at DESC
        LIMIT 50
    ''', (session['id'],))
    read_notifications = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('notifications.html', project=project, unread_notifications=unread_notifications, read_notifications=read_notifications)

@notifications_bp.route('/project/<int:project_id>/notifications/mark_read/<int:notification_id>')
def mark_notification_read(project_id, notification_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch notification
    cursor.execute('SELECT * FROM notifications WHERE id = %s', (notification_id,))
    notification = cursor.fetchone()
    
    if not notification or notification['user_id'] != session['id']:
        cursor.close()
        conn.close()
        flash('Notification not found!')
        return redirect(url_for('notifications'))
    
    # Mark as read
    cursor.execute('UPDATE notifications SET is_read = 1 WHERE id = %s', (notification_id,))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    # Redirect to notification link if available
    if notification['link']:
        return redirect(notification['link'])
    else:
        return redirect(url_for('notifications.notifications', project_id=project_id))

@notifications_bp.route('/project/<int:project_id>/notifications/mark_all_read')
def mark_all_notifications_read(project_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Mark all as read
    cursor.execute('UPDATE notifications SET is_read = 1 WHERE user_id = %s', (session['id'],))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    flash('All notifications marked as read!')
    return redirect(url_for('notifications.notifications', project_id=project_id))

@notifications_bp.route('/project/<int:project_id>/notifications/mentions')
def mentions(project_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
    project = cursor.fetchone()
    
    # Fetch mentions
    cursor.execute('''
        SELECT m.*, u.username as mentioned_by_name, m.content_type, m.content_id,
        (CASE
            WHEN m.content_type = 'comment' THEN (SELECT comment_text FROM comments WHERE id = m.content_id)
            WHEN m.content_type = 'message' THEN (SELECT message_text FROM messages WHERE id = m.content_id)
            WHEN m.content_type = 'forum_topic' THEN (SELECT title FROM forum_topics WHERE id = m.content_id)
            WHEN m.content_type = 'forum_reply' THEN (SELECT content FROM forum_replies WHERE id = m.content_id)
        END) as content_preview
        FROM mentions m
        JOIN users u ON m.mentioned_by = u.id
        WHERE m.user_id = %s
        ORDER BY m.created_at DESC
    ''', (session['id'],))
    mentions = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('mentions.html', mentions=mentions,project=project)

@notifications_bp.route('/project/<int:project_id>/notifications/mentions/mark_read/<int:mention_id>')
def mark_mention_read(project_id, mention_id):
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))

    conn = get_db_connection()
    cursor = conn.cursor()


    # Fetch project details
    cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
    project = cursor.fetchone()
    # Fetch mention
    cursor.execute('SELECT * FROM mentions WHERE id = %s', (mention_id,))
    mention = cursor.fetchone()

    if not mention or mention['user_id'] != session['id']:
        cursor.close()
        conn.close()
        flash('Mention not found!')
        return redirect(url_for('mentions'))

    # Mark as read
    cursor.execute('UPDATE mentions SET is_read = 1 WHERE id = %s', (mention_id,))
    conn.commit()

    # Prepare redirect
    redirect_url = url_for('notifications.mentions',project_id=project_id )

    if mention['content_type'] == 'comment':
        cursor.execute('SELECT task_id FROM comments WHERE id = %s', (mention['content_id'],))
        comment = cursor.fetchone()
        if comment:
            redirect_url = url_for(' task_details', task_id=comment['task_id'])

    elif mention['content_type'] == 'message':
        cursor.execute('SELECT sender_id FROM messages WHERE id = %s', (mention['content_id'],))
        message = cursor.fetchone()
        if message:
            redirect_url = url_for('messages.conversation', user_id=message['sender_id'], project_id=project_id)

    elif mention['content_type'] == 'forum_topic':
        redirect_url = url_for('forums.topic_details', topic_id=mention['content_id'])

    elif mention['content_type'] == 'forum_reply':
        cursor.execute('SELECT topic_id FROM forum_replies WHERE id = %s', (mention['content_id'],))
        reply = cursor.fetchone()
        if reply:
            redirect_url = url_for('forums.topic_details', topic_id=reply['topic_id'])

    cursor.close()
    conn.close()
    return redirect(redirect_url)
