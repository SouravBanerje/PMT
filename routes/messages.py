

# from flask import Flask, render_template, request, redirect, url_for, session, flash
# from werkzeug.security import generate_password_hash, check_password_hash
# from utils.db import get_db_connection
# import datetime
# from datetime import datetime, timedelta
# import calendar
# from flask import Blueprint
# import re



# messages_bp = Blueprint('messages', __name__)

# # Helper function to create activity
# def create_activity(user_id, project_id=None, task_id=None, activity_type=None, description=None):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT INTO activities 
#         (user_id, project_id, task_id, activity_type, description) 
#         VALUES (%s, %s, %s, %s, %s)
#     ''', (user_id, project_id, task_id, activity_type, description))
#     conn.commit()
#     cursor.close()
#     conn.close()



# # Helper function to extract mentions from text
# def extract_mentions(text):
#     # Look for @username pattern
#     mentions = re.findall(r'@(\w+)', text)
#     return mentions



# # Helper function to create notification
# def create_notification(user_id, content, link=None):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT INTO notifications 
#         (user_id, content, link) 
#         VALUES (%s, %s, %s)
#     ''', (user_id, content, link))
#     conn.commit()
#     cursor.close()
#     conn.close()

# # Helper function to create mention
# def create_mention(user_id, mentioned_by, content_type, content_id):
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('''
#         INSERT INTO mentions 
#         (user_id, mentioned_by, content_type, content_id) 
#         VALUES (%s, %s, %s, %s)
#     ''', (user_id, mentioned_by, content_type, content_id))
#     conn.commit()
#     cursor.close()
#     conn.close()







# @messages_bp.route('/messages')
# def messages():
#     # Check if user is logged in
#     if 'loggedin' not in session:
#         return redirect(url_for('auth.login'))
    
#     # Fetch all users for messaging
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute('SELECT id, username FROM users WHERE id != %s', (session['id'],))
#     users = cursor.fetchall()
    
#     # Fetch conversations with unread counts
#     cursor.execute('''
#         SELECT u.id, u.username, 
#         (SELECT COUNT(*) FROM messages WHERE sender_id = u.id AND receiver_id = %s AND is_read = 0) as unread_count,
#         (SELECT created_at FROM messages 
#          WHERE (sender_id = u.id AND receiver_id = %s) OR (sender_id = %s AND receiver_id = u.id)
#          ORDER BY created_at DESC LIMIT 1) as last_message_time
#         FROM users u
#         WHERE u.id IN (
#             SELECT sender_id FROM messages WHERE receiver_id = %s
#             UNION
#             SELECT receiver_id FROM messages WHERE sender_id = %s
#         )
#         ORDER BY last_message_time DESC
#     ''', (session['id'], session['id'], session['id'], session['id'], session['id']))
#     conversations = cursor.fetchall()
    
#     cursor.close()
#     conn.close()
    
#     return render_template('messages.html', users=users, conversations=conversations)

# @messages_bp.route('/messages/<int:user_id>', methods=['GET', 'POST'])
# def conversation(user_id):
#     # Check if user is logged in
#     if 'loggedin' not in session:
#         return redirect(url_for('auth.login'))
    
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     # Fetch the other user's details
#     cursor.execute('SELECT id, username FROM users WHERE id = %s', (user_id,))
#     other_user = cursor.fetchone()
    
#     if not other_user:
#         cursor.close()
#         conn.close()
#         flash('User not found!')
#         return redirect(url_for('messages'))
    
#     # Handle message sending
#     if request.method == 'POST':
#         message_text = request.form['message_text']
        
#         # Insert message
#         cursor.execute('''
#             INSERT INTO messages 
#             (sender_id, receiver_id, message_text) 
#             VALUES (%s, %s, %s)
#         ''', (session['id'], user_id, message_text))
#         conn.commit()
        
#         # Check for mentions
#         mentions = extract_mentions(message_text)
#         if mentions:
#             # Get message ID
#             message_id = cursor.lastrowid
            
#             # Find mentioned users
#             for username in mentions:
#                 cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
#                 mentioned_user = cursor.fetchone()
#                 if mentioned_user:
#                     # Create mention record
#                     create_mention(mentioned_user['id'], session['id'], 'message', message_id)
                    
#                     # Create notification
#                     notification_content = f"{session['username']} mentioned you in a message"
#                     link = f"/messages/{session['id']}"
#                     create_notification(mentioned_user['id'], notification_content, link)
        
#         # Log activity
#         activity_description = f"Sent a message to {other_user['username']}"
#         create_activity(session['id'], activity_type='message', description=activity_description)
    
#     # Mark messages as read
#     cursor.execute('''
#         UPDATE messages 
#         SET is_read = 1 
#         WHERE sender_id = %s AND receiver_id = %s
#     ''', (user_id, session['id']))
#     conn.commit()
    
#     # Fetch messages
#     cursor.execute('''
#         SELECT * FROM messages 
#         WHERE (sender_id = %s AND receiver_id = %s) OR (sender_id = %s AND receiver_id = %s) 
#         ORDER BY created_at
#     ''', (session['id'], user_id, user_id, session['id']))
#     messages = cursor.fetchall()
    
#     cursor.close()
#     conn.close()
    
#     return render_template('conversation.html', other_user=other_user, messages=messages)










from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from utils.db import get_db_connection
import datetime
from datetime import datetime, timedelta
import calendar
from flask import Blueprint
import re
import os
import uuid
import emoji

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'csv'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

messages_bp = Blueprint('messages', __name__)

# Helper function to check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

# Helper function to save file attachment
def save_attachment(file, message_id):
    if file and allowed_file(file.filename):
        # Create unique filename to prevent overwriting
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Ensure upload directory exists
        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        
        # Save the file
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Store file info in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO attachments 
            (message_id, file_name, file_path, file_type, file_size) 
            VALUES (%s, %s, %s, %s, %s)
        ''', (
            message_id, 
            filename, 
            f"/static/uploads/{unique_filename}", 
            file.content_type, 
            os.path.getsize(file_path)
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
    return False

# Check if text contains emoji
def contains_emoji(text):
    return emoji.emoji_count(text) > 0

@messages_bp.route('/project/<int:project_id>/messages')
def messages(project_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    # Fetch all users for messaging
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username FROM users WHERE id != %s', (session['id'],))
    users = cursor.fetchall()

    cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
    project = cursor.fetchone()
    
    # Fetch conversations with unread counts
    cursor.execute('''
        SELECT u.id, u.username, 
        (SELECT COUNT(*) FROM messages WHERE sender_id = u.id AND receiver_id = %s AND is_read = 0) as unread_count,
        (SELECT created_at FROM messages 
         WHERE (sender_id = u.id AND receiver_id = %s) OR (sender_id = %s AND receiver_id = u.id)
         ORDER BY created_at DESC LIMIT 1) as last_message_time,
        (SELECT COUNT(*) FROM attachments a 
         JOIN messages m ON a.message_id = m.id 
         WHERE ((m.sender_id = u.id AND m.receiver_id = %s) OR (m.sender_id = %s AND m.receiver_id = u.id))
         AND m.created_at = (SELECT MAX(created_at) FROM messages 
                            WHERE (sender_id = u.id AND receiver_id = %s) OR (sender_id = %s AND receiver_id = u.id))) as has_attachment
        FROM users u
        WHERE u.id IN (
            SELECT sender_id FROM messages WHERE receiver_id = %s
            UNION
            SELECT receiver_id FROM messages WHERE sender_id = %s
        )
        ORDER BY last_message_time DESC
    ''', (session['id'], session['id'], session['id'], session['id'], session['id'], session['id'], session['id'], session['id'], session['id']))
    conversations = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('messages.html', project=project, users=users, conversations=conversations)





@messages_bp.route('/project/<int:project_id>/messages/<int:user_id>', methods=['GET', 'POST'])
def conversation(user_id, project_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch the other user's details
    cursor.execute('SELECT id, username FROM users WHERE id = %s', (user_id,))
    other_user = cursor.fetchone()

    cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
    project = cursor.fetchone()
    
    if not other_user:
        cursor.close()
        conn.close()
        flash('User not found!')
        return redirect(url_for('messages.messages', project_id=project_id))
    
    # Handle message sending
    if request.method == 'POST':
        message_text = request.form['message_text']
        has_emoji_flag = contains_emoji(message_text)
        
        # Insert message
        cursor.execute('''
            INSERT INTO messages 
            (sender_id, receiver_id, message_text, has_emoji) 
            VALUES (%s, %s, %s, %s)
        ''', (session['id'], user_id, message_text, has_emoji_flag))
        conn.commit()
        
        # Get the message ID for attachments and mentions
        message_id = cursor.lastrowid
        
        # Handle file attachment if present
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file.filename != '':
                save_attachment(file, message_id)
        
        # Check for mentions
        mentions = extract_mentions(message_text)
        if mentions:
            # Find mentioned users
            for username in mentions:
                cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
                mentioned_user = cursor.fetchone()
                if mentioned_user:
                    # Create mention record
                    create_mention(mentioned_user['id'], session['id'], 'message', message_id)
                    
                    # Create notification
                    notification_content = f"{session['username']} mentioned you in a message"
                    link = url_for('messages.conversation', 
                                user_id=session['id'], 
                                project_id=project_id)
                    create_notification(mentioned_user['id'], notification_content, link)
        
        # Log activity
        activity_description = f"Sent a message to {other_user['username']}"
        create_activity(session['id'], activity_type='message', description=activity_description)
        
        # Redirect to avoid form resubmission - FIXED HERE
        return redirect(url_for('messages.conversation', user_id=user_id, project_id=project_id))
    
    # Mark messages as read
    cursor.execute('''
        UPDATE messages 
        SET is_read = 1 
        WHERE sender_id = %s AND receiver_id = %s
    ''', (user_id, session['id']))
    conn.commit()
    
    # Fetch messages with attachments
    cursor.execute('''
        SELECT m.*, 
               (SELECT COUNT(*) FROM attachments WHERE message_id = m.id) AS attachment_count
        FROM messages m
        WHERE (m.sender_id = %s AND m.receiver_id = %s) 
           OR (m.sender_id = %s AND m.receiver_id = %s) 
        ORDER BY m.created_at
    ''', (session['id'], user_id, user_id, session['id']))
    messages = cursor.fetchall()
    
    # Fetch attachments for messages
    message_attachments = {}
    for message in messages:
        if message['attachment_count'] > 0:
            cursor.execute('SELECT * FROM attachments WHERE message_id = %s', (message['id'],))
            message_attachments[message['id']] = cursor.fetchall()
    
    # Fetch emoji reactions for messages
    message_reactions = {}
    for message in messages:
        cursor.execute('''
            SELECT er.emoji, u.username 
            FROM emoji_reactions er
            JOIN users u ON er.user_id = u.id
            WHERE er.message_id = %s
        ''', (message['id'],))
        message_reactions[message['id']] = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('conversation.html', 
                          project=project,
                          other_user=other_user, 
                          messages=messages, 
                          attachments=message_attachments,
                          reactions=message_reactions)


@messages_bp.route('/messages/react', methods=['POST'])
def react_with_emoji():
    # Check if user is logged in
    if 'loggedin' not in session:
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Not logged in'}), 401
        return redirect(url_for('auth.login'))
    
    message_id = request.form.get('message_id')
    emoji_code = request.form.get('emoji')
    
    # Add debugging to help identify issues
    print(f"Reaction received: Message ID {message_id}, Emoji {emoji_code}")
    
    if not message_id or not emoji_code:
        flash('Invalid reaction data')
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': 'Invalid reaction data'}), 400
        return redirect(url_for('messages.messages'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)  # Ensure dictionary=True to access by column name
        
        # Check if reaction already exists
        cursor.execute('''
            SELECT id FROM emoji_reactions 
            WHERE message_id = %s AND user_id = %s AND emoji = %s
        ''', (message_id, session['id'], emoji_code))
        existing = cursor.fetchone()
        
        if existing:
            # Remove reaction if already exists (toggle behavior)
            cursor.execute('DELETE FROM emoji_reactions WHERE id = %s', (existing['id'],))
            print(f"Removed existing reaction with ID {existing['id']}")
            status = 'removed'
        else:
            # Add new emoji reaction
            cursor.execute('''
                INSERT INTO emoji_reactions 
                (message_id, user_id, emoji) 
                VALUES (%s, %s, %s)
            ''', (message_id, session['id'], emoji_code))
            print(f"Added new reaction: {emoji_code}")
            status = 'added'
        
        conn.commit()
        
        # Get the conversation to redirect back to
        cursor.execute('SELECT sender_id, receiver_id FROM messages WHERE id = %s', (message_id,))
        message = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'success', 'action': status})
        
        # Handle regular form submissions
        if message:
            # Determine which user to redirect to (the other party in the conversation)
            other_user_id = message['sender_id'] if message['sender_id'] != session['id'] else message['receiver_id']
            return redirect(url_for('messages.conversation', user_id=other_user_id))
        
        return redirect(url_for('messages.messages'))
        
    except Exception as e:
        print(f"Error processing reaction: {str(e)}")
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'status': 'error', 'message': str(e)}), 500
        flash('An error occurred while processing your reaction')
        return redirect(url_for('messages.messages'))