from flask import Flask, render_template, request, redirect, url_for, session,Blueprint, flash
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection
import datetime





update_project_bp = Blueprint('update_project', __name__)




@update_project_bp.route('/project/<int:project_id>/update_project', methods=['GET', 'POST'])
def update_project(project_id):
    # Check if the user is logged in and has proper permission
    if 'loggedin' not in session or (session['user_type'] not in ['admin', 'pm']):
        return redirect(url_for('login'))  # Redirect to login if not logged in or has insufficient permissions

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch current project details
    cursor.execute('SELECT * FROM projects WHERE id = %s', (project_id,))
    project = cursor.fetchone()

    if project is None:
        flash('Project not found.', 'danger')
        return redirect(url_for('home'))

    # If the form is submitted (POST request)
    if request.method == 'POST':
        project_name = request.form['project_name']
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        project_type = request.form['project_type']
        total_amount = request.form['total_amount']
        per_month_billing = request.form['per_month_billing']
        po_number = request.form['po_number']
        sow_attachment = request.form['sow_attachment']
        status = request.form['status']

        # Update project in the database
        cursor.execute(''' 
            UPDATE projects
            SET project_name = %s, description = %s, start_date = %s, end_date = %s,
                project_type = %s, total_amount = %s, per_month_billing = %s,
                po_number = %s, sow_attachment = %s, status = %s
            WHERE id = %s
        ''', (project_name, description, start_date, end_date, project_type,
              total_amount, per_month_billing, po_number, sow_attachment, status, project_id))

        conn.commit()
        cursor.close()
        conn.close()

        flash('Project updated successfully!', 'success')
        return redirect(url_for('project_details.project_details', project_id=project_id))  # Redirect to project details

    # If it's a GET request, display the form with current project details
    cursor.close()
    conn.close()

    return render_template('update_project.html', project=project)