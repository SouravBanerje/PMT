from flask import Blueprint, Flask, app, render_template, request, redirect, url_for, session, flash

from werkzeug.security import generate_password_hash, check_password_hash

from utils.db import get_db_connection





# Create Blueprint
auth_bp = Blueprint('auth', __name__)



# Login route
@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong
    msg = ''
    
    # Check if "username" and "password" POST requests exist
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        user_type = request.form.get('user_type', 'team_member')
        
        # Check if account exists using MySQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = %s AND user_type = %s', (username, user_type))
        
        # Fetch one record
        account = cursor.fetchone()
        
        # If account exists in accounts table in our database
        if account:
            # Check password - handle both Werkzeug format and plain hashes
            password_correct = False
            try:
                password_correct = check_password_hash(account['password'], password)
            except ValueError:
                # If the hash format is invalid, try direct comparison (for development only)
                if account['password'] == 'admin123' and username == 'admin':
                    password_correct = True
                elif account['password'] == 'pm123' and username == 'pm':
                    password_correct = True
                elif account['password'] == 'team123' and username == 'team':
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
                    return redirect(url_for('change_password'))
                else:
                    # Redirect to home page
                    return redirect(url_for('home.home'))
        
        # Account doesn't exist or password incorrect
        msg = 'Incorrect username/password!'
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        
    print(generate_password_hash('team123'))
    # Return template
    return render_template('login.html', msg=msg)