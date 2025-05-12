from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import re
from werkzeug.security import generate_password_hash
from utils.db import get_db_connection

change_password_bp = Blueprint('change_password', __name__)

def validate_password_strength(password):
    """Validate password strength and return tuple (is_valid, error_message)"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, None

# Change password route
@change_password_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    # For debugging - print if we're in the route
    print("Change password route accessed")
    
    # Check if user is logged in
    if 'loggedin' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # For debugging - print the form data
        print("Form submitted", request.form)
        
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # For debugging - print the passwords
        print(f"Password length: {len(password) if password else 0}")
        print(f"Confirm password length: {len(confirm_password) if confirm_password else 0}")
        
        if not password or not confirm_password:
            flash('Please fill in all fields', 'error')
            return render_template('change_password.html')
        
        # Validate password strength
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            flash(error_message, 'error')
            return render_template('change_password.html')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('change_password.html')
        
        try:
            # Hash the new password
            hashed_password = generate_password_hash(password)
            
            # For debugging - print user ID from session
            print(f"User ID from session: {session.get('id')}")
            
            # Update password in database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Update the password and set first_login to 0
            cursor.execute(
                'UPDATE users SET password = %s, first_login = 0 WHERE id = %s',
                (hashed_password, session['id'])
            )
            
            # For debugging - print affected rows
            print(f"Rows affected: {cursor.rowcount}")
            
            if cursor.rowcount == 0:
                flash('Failed to update password. Please try again.', 'error')
                cursor.close()
                conn.close()
                return render_template('change_password.html')
            
            conn.commit()
            cursor.close()
            conn.close()
            
            flash('Password successfully updated!', 'success')
            
            # If it was first login, redirect to home, otherwise stay on the page
            if request.form.get('first_login'):
                return redirect(url_for('home.home'))
            return render_template('login.html')
        
        except Exception as e:
            flash('An error occurred while updating your password. Please try again.', 'error')
            print(f"Error updating password: {str(e)}")  # For debugging
            return render_template('change_password.html')
    
    # GET request - show the form
    return render_template('change_password.html')