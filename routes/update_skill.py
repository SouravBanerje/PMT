from flask import Flask, render_template, request, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime

update_skill_bp = Blueprint('update_skill', __name__)





# Update Skill Route
@update_skill_bp.route('/update_skill', methods=['POST'])
def update_skill():
    # Check if user is logged in
    if 'loggedin' in session:
        # Get form data
        user_id = request.form['user_id']
        skill_id = request.form['skill_id']
        proficiency_level = int(request.form['proficiency_level'])
        years_experience = float(request.form['years_experience'])
        
        # Check if user is authorized (can only update own skills unless admin/PM)
        if str(session['id']) != str(user_id) and session['user_type'] not in ['admin', 'pm']:
            flash('You are not authorized to update this resource\'s skills')
            return redirect(url_for('skill_matrix'))
        
        # Update skill in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if entry exists
        cursor.execute('SELECT id FROM user_skills WHERE user_id = %s AND skill_id = %s', 
                      (user_id, skill_id))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            cursor.execute('''
                UPDATE user_skills 
                SET proficiency_level = %s, years_experience = %s 
                WHERE user_id = %s AND skill_id = %s
            ''', (proficiency_level, years_experience, user_id, skill_id))
        else:
            # Insert new record
            cursor.execute('''
                INSERT INTO user_skills 
                (user_id, skill_id, proficiency_level, years_experience) 
                VALUES (%s, %s, %s, %s)
            ''', (user_id, skill_id, proficiency_level, years_experience))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Redirect back to skill matrix
        return redirect(url_for('skill_matrix.skill_matrix'))
    
    # User is not logged in, redirect to login page
    return redirect(url_for('auth.login'))