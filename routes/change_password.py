from flask import Blueprint, Flask, app, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection



#create Blueprint
change_password_bp = Blueprint('change_password', __name__)


# Change password route
@change_password_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    # Check if user is logged in
    if 'loggedin' in session:
        # Output message
        msg = ''
        
        # Check if "password" and "confirm_password" POST requests exist
        if request.method == 'POST' and 'password' in request.form and 'confirm_password' in request.form:
            # Create variables for easy access
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            
            # If password and confirm_password match
            if password == confirm_password:
                # Hash the password
                hashed_password = generate_password_hash(password)
                
                # Update the password in the database
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET password = %s, first_login = 0 WHERE id = %s', 
                              (hashed_password, session['id']))
                conn.commit()
                cursor.close()
                conn.close()
                
                # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Passwords don't match
                msg = 'Passwords do not match!'
        
        # Return template
        return render_template('change_password.html', msg=msg)
    
    # User is not logged in, redirect to login page
    return redirect(url_for('login'))