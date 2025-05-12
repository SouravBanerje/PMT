from flask import Flask, render_template, request, redirect, url_for, session, Blueprint
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime
from flask import flash



skill_matrix_bp = Blueprint('skill_matrix', __name__)



# Skill Matrix Routes
@skill_matrix_bp.route('/skill_matrix')
def skill_matrix():
    # Check if user is logged in
    if 'loggedin' in session:
        # Fetch skills and categories
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, skill_name, skill_category FROM skills ORDER BY skill_category, skill_name')
        skills = cursor.fetchall()
        
        # Get unique skill categories
        cursor.execute('SELECT DISTINCT skill_category FROM skills ORDER BY skill_category')
        categories = [row['skill_category'] for row in cursor.fetchall()]
        
        # Fetch team members based on user type
        if session['user_type'] == 'admin' or session['user_type'] == 'pm':
            cursor.execute('SELECT id, username FROM users WHERE user_type = "team_member"')
        else:
            cursor.execute('SELECT id, username FROM users WHERE id = %s', (session['id'],))
        team_members = cursor.fetchall()
        
        # Fetch user skills
        user_skills = {}
        for member in team_members:
            cursor.execute('''
                SELECT us.skill_id, us.proficiency_level, us.years_experience 
                FROM user_skills us
                WHERE us.user_id = %s
            ''', (member['id'],))
            member_skills = {row['skill_id']: row for row in cursor.fetchall()}
            user_skills[member['id']] = member_skills
        
        cursor.close()
        conn.close()
        
    
        return render_template('skill_matrix.html', 
                               skills=skills, 
                               categories=categories,
                               team_members=team_members,
                               user_skills=user_skills)
    
   
    return redirect(url_for('auth.login'))