from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from utils.db import get_db_connection
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import session
from flask import Blueprint




forget_password_bp = Blueprint('forget_password', __name__)





# Helper function to send email
def send_password_reset_email(email, new_password):
    sender_email = "sourav2473486@gmail.com"
    password = "jkmtipyjbixxubme"
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Password Reset"
    message["From"] = sender_email
    message["To"] = email
    
    text = f"""
    Hello,
    
    Your password has been reset. Your new password is: {new_password}
    
    Please log in and change your password.
    
    Best regards,
    Project Management System
    """
    
    part = MIMEText(text, "plain")
    message.attach(part)
    
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print(e)
        return False



# Forgot password route
@forget_password_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    # Output message
    msg = ''
    
    # Check if "email" POST request exists
    if request.method == 'POST' and 'email' in request.form:
        # Create variables for easy access
        email = request.form['email']
        
        # Check if email exists using MySQL
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        
        # Fetch one record
        account = cursor.fetchone()
        
        # If account exists
        if account:
            # Generate a random password
            new_password = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(8))
            
            # Hash the password
            hashed_password = generate_password_hash(new_password)
            
            # Update the password in the database
            cursor.execute('UPDATE users SET password = %s, first_login = 1 WHERE id = %s', 
                          (hashed_password, account['id']))
            conn.commit()
            
            # Send email
            if send_password_reset_email(email, new_password):
                msg = 'Password reset email sent!'
            else:
                msg = 'Failed to send password reset email!'
        else:
            # Email doesn't exist
            msg = 'Email does not exist!'
            
        cursor.close()
        conn.close()
    
    # Return template
    return render_template('forgot_password.html', msg=msg)