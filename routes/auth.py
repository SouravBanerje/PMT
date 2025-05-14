from flask import Blueprint, Flask, app, render_template, request, redirect, url_for, session, flash

from werkzeug.security import generate_password_hash, check_password_hash

from utils.db import get_db_connection


# Create Blueprint
auth_bp = Blueprint('auth', __name__)



@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    
    if request.method == 'POST':
        # Check if all required fields are present and not empty
        if not request.form.get('username') or not request.form.get('password'):
            flash('Please fill out all fields', 'error')
            return render_template('login.html', msg=msg)
        
        # Create variables for easy access
        username_or_email = request.form['username']  # This field can contain either username or email
        password = request.form['password']
        user_type = request.form.get('user_type', 'team_member')
        
        # Check if account exists using MySQL
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if input is email or username (simple validation)
        is_email = '@' in username_or_email
        
        # First check if username/email exists at all
        if is_email:
            cursor.execute('SELECT * FROM users WHERE email = %s', (username_or_email,))
        else:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username_or_email,))
            
        user_exists = cursor.fetchone()
        
        if user_exists and user_exists['user_type'] != user_type:
            flash('Invalid user type for this account', 'error')
            cursor.close()
            conn.close()
            return render_template('login.html', msg=msg)
        
        # Now check with the specific user type
        if is_email:
            cursor.execute('SELECT * FROM users WHERE email = %s AND user_type = %s', 
                           (username_or_email, user_type))
        else:
            cursor.execute('SELECT * FROM users WHERE username = %s AND user_type = %s', 
                           (username_or_email, user_type))
            
        account = cursor.fetchone()
        
        # If account exists in accounts table in our database
        if account:
            # Check password - handle both Werkzeug format and plain hashes
            password_correct = False
            try:
                password_correct = check_password_hash(account['password'], password)
            except ValueError:
                # If the hash format is invalid, try direct comparison (for development only)
                if account['password'] == 'admin123' and account['username'] == 'admin':
                    password_correct = True
                elif account['password'] == 'pm123' and account['username'] == 'pm':
                    password_correct = True
                elif account['password'] == 'team123' and account['username'] == 'team':
                    password_correct = True
                
            if password_correct:
                # Create session data
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['user_type'] = account['user_type']
                
                # Check if it's first login
                if account['first_login'] == 1:
                    # Redirect to change password page
                    return redirect(url_for('change_password.change_password'))
                else:
                    # Redirect to home page
                    return redirect(url_for('home.home'))
        
        # Account doesn't exist or password incorrect
        flash('Incorrect username/password!', 'error')
        
        # Close cursor and connection
        cursor.close()
        conn.close()
    
    # Return template
    return render_template('login.html', msg=msg)
