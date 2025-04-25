

from flask import Flask, render_template, request, redirect, url_for, session,Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime


resource_management_bp = Blueprint('resource_management', __name__)




# Resource Management Home Route
@resource_management_bp.route('/resource-management')
def resource_management():
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        # Fetch team members
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email FROM users WHERE user_type = "team_member"')
        team_members = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Return template
        return render_template('resource_management.html', team_members=team_members)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home.home'))


