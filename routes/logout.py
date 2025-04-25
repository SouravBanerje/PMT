from flask import Flask, render_template, redirect, url_for, session, Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime
from datetime import datetime,  timedelta

logout_bp = Blueprint('logout', __name__)





# Logout route
@logout_bp.route('/logout')
def logout():
    # Remove session data
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('user_type', None)
    
    # Redirect to login page
    return redirect(url_for('auth.login'))