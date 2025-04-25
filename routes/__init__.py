from flask import Blueprint
from .auth import auth_bp  
from .change_password import change_password_bp 
from .forget_password import forget_password_bp 
from .home import home_bp  
from .define_project import define_project_bp 
from .search_project import search_project_bp 
from .project_details import project_details_bp 
from .update_project_cost import update_project_cost_bp  
from .update_project_schedule import update_project_schedule_bp 
from .project_version_report import project_version_report_bp  
from .update_project import update_project_bp
from .create_task import create_task_bp
from .resource_management import resource_management_bp
from .resource_calender import resource_calendar_bp
from .update_availability import update_availability_bp
from .skill_matrix import skill_matrix_bp
from .manage_skills import manage_skills_bp
from .update_skill import update_skill_bp
from .time_tracking import time_tracking_bp
from .submit_timesheet import submit_timesheet_bp
from .add_time_entry import add_time_entry_bp
from .update_time_entry_status import update_time_entry_status_bp
from .resource_utilization import resource_utilization_bp
from .resource_optimization import resource_optimization_bp
from .capacity_planning import capacity_planning_bp
from .forums import forums_bp
from .video_conferences import video_conferences_bp
from .messages import messages_bp
from .notifications import notifications_bp
from .activity_stream import activity_stream_bp
from .update_task import update_task_bp
from .gantt_chart import gantt_chart_bp
from .logout import logout_bp


def init_app(app):
    """Initialize route blueprints with app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(change_password_bp)
    app.register_blueprint(forget_password_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(define_project_bp)
    app.register_blueprint(search_project_bp)
    app.register_blueprint(project_details_bp)
    app.register_blueprint(update_project_cost_bp)
    app.register_blueprint(update_project_schedule_bp)
    app.register_blueprint(project_version_report_bp)
    app.register_blueprint(update_project_bp)
    app.register_blueprint(create_task_bp)
    app.register_blueprint(resource_management_bp)
    app.register_blueprint(resource_calendar_bp)
    app.register_blueprint(update_availability_bp)
    app.register_blueprint(skill_matrix_bp)
    app.register_blueprint(manage_skills_bp)
    app.register_blueprint(update_skill_bp)
    app.register_blueprint(time_tracking_bp)
    app.register_blueprint(submit_timesheet_bp)
    app.register_blueprint(add_time_entry_bp)
    app.register_blueprint(update_time_entry_status_bp)
    app.register_blueprint(resource_utilization_bp) 
    app.register_blueprint(resource_optimization_bp)
    app.register_blueprint(capacity_planning_bp)
    app.register_blueprint(forums_bp)
    app.register_blueprint(video_conferences_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(activity_stream_bp)
    app.register_blueprint(update_task_bp)
    app.register_blueprint(gantt_chart_bp)
    app.register_blueprint(logout_bp)
    return app