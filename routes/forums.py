import re
from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime


forums_bp = Blueprint('forums', __name__)



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



@forums_bp.route('/project/<int:project_id>/forums')
def forums(project_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch project details
    cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
    project = cursor.fetchone()
    
    if not project:
        cursor.close()
        conn.close()
        flash('Project not found!')
        return redirect(url_for('home.home'))
    
    # Fetch forums for this project
    cursor.execute('''
        SELECT f.*, 
        (SELECT COUNT(*) FROM forum_topics WHERE forum_id = f.id) as topic_count,
        (SELECT COUNT(*) FROM forum_topics ft JOIN forum_replies fr ON ft.id = fr.topic_id WHERE ft.forum_id = f.id) as reply_count,
        (SELECT MAX(fr.created_at) FROM forum_topics ft JOIN forum_replies fr ON ft.id = fr.topic_id WHERE ft.forum_id = f.id) as last_activity
        FROM forums f
        WHERE f.project_id = %s
        ORDER BY f.created_at DESC
    ''', (project_id,))
    forums = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('forums.html', project=project, forums=forums)

@forums_bp.route('/project/<int:project_id>/forums/create', methods=['GET', 'POST'])
def create_forum(project_id):
    # Check if user is logged in and is admin or PM
    if 'loggedin' not in session or (session['user_type'] != 'admin' and session['user_type'] != 'pm'):
        flash('You do not have permission to create forums!')
        return redirect(url_for('forums', project_id=project_id))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch project details
    cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
    project = cursor.fetchone()
    
    if not project:
        cursor.close()
        conn.close()
        flash('Project not found!')
        return redirect(url_for('home'))
    
    # Handle form submission
    if request.method == 'POST':
        forum_name = request.form['forum_name']
        description = request.form.get('description', '')
        
        # Create forum
        cursor.execute('''
            INSERT INTO forums 
            (project_id, forum_name, description) 
            VALUES (%s, %s, %s)
        ''', (project_id, forum_name, description))
        conn.commit()
        
        # Log activity
        activity_description = f"Created forum '{forum_name}' in project '{project['project_name']}'"
        create_activity(session['id'], project_id, activity_type='forum_create', description=activity_description)
        
        cursor.close()
        conn.close()
        
        flash('Forum created successfully!')
        return redirect(url_for('forums.forums', project_id=project_id))
    
    cursor.close()
    conn.close()
    
    return render_template('create_forum.html', project=project)

@forums_bp.route('/forum/<int:forum_id>')
def forum_topics(forum_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch forum details
    cursor.execute('''
        SELECT f.*, p.id as project_id, p.project_name 
        FROM forums f
        JOIN projects p ON f.project_id = p.id
        WHERE f.id = %s
    ''', (forum_id,))
    forum = cursor.fetchone()
    
    if not forum:
        cursor.close()
        conn.close()
        flash('Forum not found!')
        return redirect(url_for('home'))
    
    # Fetch topics
    cursor.execute('''
        SELECT ft.*, u.username, 
        (SELECT COUNT(*) FROM forum_replies WHERE topic_id = ft.id) as reply_count,
        (SELECT MAX(created_at) FROM forum_replies WHERE topic_id = ft.id) as last_reply_time
        FROM forum_topics ft
        JOIN users u ON ft.user_id = u.id
        WHERE ft.forum_id = %s
        ORDER BY ft.created_at DESC
    ''', (forum_id,))
    topics = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('forum_topics.html', forum=forum, topics=topics)

@forums_bp.route('/forum/<int:forum_id>/create_topic', methods=['GET', 'POST'])
def create_topic(forum_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch forum details
    cursor.execute('''
        SELECT f.*, p.id as project_id, p.project_name 
        FROM forums f
        JOIN projects p ON f.project_id = p.id
        WHERE f.id = %s
    ''', (forum_id,))
    forum = cursor.fetchone()
    
    if not forum:
        cursor.close()
        conn.close()
        flash('Forum not found!')
        return redirect(url_for('home'))
    
    # Handle form submission
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        # Create topic
        cursor.execute('''
            INSERT INTO forum_topics 
            (forum_id, user_id, title, content) 
            VALUES (%s, %s, %s, %s)
        ''', (forum_id, session['id'], title, content))
        conn.commit()
        
        # Get topic ID
        topic_id = cursor.lastrowid
        
        # Check for mentions
        mentions = extract_mentions(content)
        if mentions:
            for username in mentions:
                cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
                mentioned_user = cursor.fetchone()
                if mentioned_user:
                    # Create mention record
                    create_mention(mentioned_user['id'], session['id'], 'forum_topic', topic_id)
                    
                    # Create notification
                    notification_content = f"{session['username']} mentioned you in a forum topic"
                    link = f"/topic/{topic_id}"
                    create_notification(mentioned_user['id'], notification_content, link)
        
        # Log activity
        activity_description = f"Created topic '{title}' in forum '{forum['forum_name']}'"
        create_activity(session['id'], forum['project_id'], activity_type='topic_create', description=activity_description)
        
        cursor.close()
        conn.close()
        
        flash('Topic created successfully!')
        return redirect(url_for('forums.forum_topics', forum_id=forum_id))
    
    cursor.close()
    conn.close()
    
    return render_template('create_topic.html', forum=forum)


@forums_bp.route('/topic/<int:topic_id>')
def topic_details(topic_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch topic details
    cursor.execute('''
        SELECT ft.*, u.username, f.id as forum_id, f.forum_name, p.id as project_id, p.project_name 
        FROM forum_topics ft
        JOIN users u ON ft.user_id = u.id
        JOIN forums f ON ft.forum_id = f.id
        JOIN projects p ON f.project_id = p.id
        WHERE ft.id = %s
    ''', (topic_id,))
    topic = cursor.fetchone()
    
    if not topic:
        cursor.close()
        conn.close()
        flash('Topic not found!')
        return redirect(url_for('home'))
    
    # Fetch replies
    cursor.execute('''
        SELECT fr.*, u.username 
        FROM forum_replies fr
        JOIN users u ON fr.user_id = u.id
        WHERE fr.topic_id = %s
        ORDER BY fr.created_at
    ''', (topic_id,))
    replies = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('topic_details.html', topic=topic, replies=replies)

@forums_bp.route('/topic/<int:topic_id>/reply', methods=['POST'])
def reply_to_topic(topic_id):
    # Check if user is logged in
    if 'loggedin' not in session:
        return redirect(url_for('auth.login'))
    
    content = request.form['content']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch topic details
    cursor.execute('''
        SELECT ft.*, f.project_id, u.username as topic_creator_name
        FROM forum_topics ft
        JOIN forums f ON ft.forum_id = f.id
        JOIN users u ON ft.user_id = u.id
        WHERE ft.id = %s
    ''', (topic_id,))
    topic = cursor.fetchone()
    
    if not topic:
        cursor.close()
        conn.close()
        flash('Topic not found!')
        return redirect(url_for('home'))
    
    # Create reply
    cursor.execute('''
        INSERT INTO forum_replies 
        (topic_id, user_id, content) 
        VALUES (%s, %s, %s)
    ''', (topic_id, session['id'], content))
    conn.commit()
    
    # Get reply ID
    reply_id = cursor.lastrowid
    
    # Notify topic creator if it's not them replying
    if topic['user_id'] != session['id']:
        notification_content = f"{session['username']} replied to your topic '{topic['title']}'"
        link = f"/topic/{topic_id}"
        create_notification(topic['user_id'], notification_content, link)
    
    # Check for mentions
    mentions = extract_mentions(content)
    if mentions:
        for username in mentions:
            cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
            mentioned_user = cursor.fetchone()
            if mentioned_user:
                # Create mention record
                create_mention(mentioned_user['id'], session['id'], 'forum_reply', reply_id)
                
                # Create notification
                notification_content = f"{session['username']} mentioned you in a forum reply"
                link = f"/topic/{topic_id}"
                create_notification(mentioned_user['id'], notification_content, link)
    
    # Log activity
    activity_description = f"Replied to topic '{topic['title']}'"
    create_activity(session['id'], topic['project_id'], activity_type='topic_reply', description=activity_description)
    
    cursor.close()
    conn.close()
    
    flash('Reply posted successfully!')
    return redirect(url_for('forums.topic_details', topic_id=topic_id))
