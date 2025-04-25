
from flask import Flask, render_template, request, redirect, url_for, session, flash, Blueprint
import pymysql.cursors
from utils.db import get_db_connection
from datetime import datetime



manage_skills_bp = Blueprint('manage_skills', __name__)








# Manage Skills Route (admin only)
@manage_skills_bp.route('/manage_skills', methods=['GET', 'POST'])
def manage_skills():
    # Check if user is logged in and is admin
    if 'loggedin' in session and session['user_type'] == 'admin':
        # Handle form submission
        if request.method == 'POST':
            # Get form data
            skill_name = request.form['skill_name']
            skill_category = request.form['skill_category']
            description = request.form.get('description', '')
            
            # Insert skill into database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO skills 
                    (skill_name, skill_category, description) 
                    VALUES (%s, %s, %s)
                ''', (skill_name, skill_category, description))
                conn.commit()
                flash('Skill added successfully')
            except pymysql.err.IntegrityError:
                flash('Skill already exists')
            
            cursor.close()
            conn.close()
        
        # Fetch existing skills
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM skills ORDER BY skill_category, skill_name')
        skills = cursor.fetchall()
        
        # Get unique categories
        cursor.execute('SELECT DISTINCT skill_category FROM skills ORDER BY skill_category')
        categories = [row['skill_category'] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        # Return template
        return render_template('manage_skills.html', skills=skills, categories=categories)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home.home'))