from flask import Blueprint, Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from utils.db import get_db_connection



project_version_report_bp = Blueprint('project_version_report', __name__)



@project_version_report_bp.route('/project_versions', methods=['GET'])
def project_version_report():
    # Check if user is logged in and is admin or PM
    if 'loggedin' in session and (session['user_type'] == 'admin' or session['user_type'] == 'pm'):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get filter parameters
        selected_project_id = request.args.get('project_id', '')
        change_type = request.args.get('change_type', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Fetch all projects for dropdown
        cursor.execute('SELECT id, project_id, project_name FROM projects ORDER BY project_name')
        projects = cursor.fetchall()
        
        # Prepare query for report
        query = '''
            SELECT pv.*, p.project_id as proj_id, p.project_name, u.username
            FROM project_versions pv
            JOIN projects p ON pv.project_id = p.id
            JOIN users u ON pv.changed_by = u.id
            WHERE 1=1
        '''
        params = []
        
        # Add filters
        if selected_project_id:
            query += " AND pv.project_id = %s"
            params.append(selected_project_id)
        
        if change_type:
            query += " AND pv.change_type = %s"
            params.append(change_type)
        
        if start_date:
            query += " AND pv.changed_at >= %s"
            params.append(start_date + " 00:00:00")
        
        if end_date:
            query += " AND pv.changed_at <= %s"
            params.append(end_date + " 23:59:59")
        
        query += " ORDER BY pv.changed_at DESC"
        
        # Execute query
        cursor.execute(query, params)
        version_changes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Return template
        return render_template('project_version_report.html',
                            projects=projects,
                            selected_project_id=int(selected_project_id) if selected_project_id else '',
                            change_type=change_type,
                            start_date=start_date,
                            end_date=end_date,
                            version_changes=version_changes)
    
    # User is not authorized, redirect to home page
    return redirect(url_for('home.home'))