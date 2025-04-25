

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime, timedelta
import calendar
from flask import Blueprint
import re



messages_bp = Blueprint('messages', __name__)

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







@messages_bp.route('/messages')
def messages():
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    # Fetch all users for messaging
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username FROM users WHERE id != %s', (session['id'],))
    users = cursor.fetchall()
    
    # Fetch conversations with unread counts
    cursor.execute('''
        SELECT u.id, u.username, 
        (SELECT COUNT(*) FROM messages WHERE sender_id = u.id AND receiver_id = %s AND is_read = 0) as unread_count,
        (SELECT created_at FROM messages 
         WHERE (sender_id = u.id AND receiver_id = %s) OR (sender_id = %s AND receiver_id = u.id)
         ORDER BY created_at DESC LIMIT 1) as last_message_time
        FROM users u
        WHERE u.id IN (
            SELECT sender_id FROM messages WHERE receiver_id = %s
            UNION
            SELECT receiver_id FROM messages WHERE sender_id = %s
        )
        ORDER BY last_message_time DESC
    ''', (session['id'], session['id'], session['id'], session['id'], session['id']))
    conversations = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('messages.html', users=users, conversations=conversations)

@messages_bp.route('/messages/<int:user_id>', methods=['GET', 'POST'])
def conversation(user_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch the other user's details
    cursor.execute('SELECT id, username FROM users WHERE id = %s', (user_id,))
    other_user = cursor.fetchone()
    
    if not other_user:
        cursor.close()
        conn.close()
        flash('User not found!')
        return redirect(url_for('messages'))
    
    # Handle message sending
    if request.method == 'POST':
        message_text = request.form['message_text']
        
        # Insert message
        cursor.execute('''
            INSERT INTO messages 
            (sender_id, receiver_id, message_text) 
            VALUES (%s, %s, %s)
        ''', (session['id'], user_id, message_text))
        conn.commit()
        
        # Check for mentions
        mentions = extract_mentions(message_text)
        if mentions:
            # Get message ID
            message_id = cursor.lastrowid
            
            # Find mentioned users
            for username in mentions:
                cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
                mentioned_user = cursor.fetchone()
                if mentioned_user:
                    # Create mention record
                    create_mention(mentioned_user['id'], session['id'], 'message', message_id)
                    
                    # Create notification
                    notification_content = f"{session['username']} mentioned you in a message"
                    link = f"/messages/{session['id']}"
                    create_notification(mentioned_user['id'], notification_content, link)
        
        # Log activity
        activity_description = f"Sent a message to {other_user['username']}"
        create_activity(session['id'], activity_type='message', description=activity_description)
    
    # Mark messages as read
    cursor.execute('''
        UPDATE messages 
        SET is_read = 1 
        WHERE sender_id = %s AND receiver_id = %s
    ''', (user_id, session['id']))
    conn.commit()
    
    # Fetch messages
    cursor.execute('''
        SELECT * FROM messages 
        WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s) 
        ORDER BY created_at
    ''', (session['id'], user_id, user_id, session['id']))
    messages = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('conversation.html', other_user=other_user, messages=messages)

