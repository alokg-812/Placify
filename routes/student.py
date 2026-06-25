from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from functools import wraps
from models import db, Student, PlacementDrive, Application, Company
from datetime import datetime

student_bp = Blueprint('student', __name__, url_prefix='/student')

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied. Student privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    student = Student.query.filter_by(user_id=current_user.id).first()

    if not student:
        abort(403)
    if student.is_blacklisted:
        flash(
            'Your account has been blacklisted. Please contact the placement cell.',
            'danger'
        )

    approved_drives = (
        PlacementDrive.query
        .filter_by(is_approved=True, is_active=True)
        .order_by(PlacementDrive.created_at.desc())
        .all()
    )

    my_applications = (
        db.session.query(Application, PlacementDrive, Company)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.id)
        .join(Company, PlacementDrive.company_id == Company.id)
        .filter(Application.student_id == student.id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    applied_drive_ids = [app.Application.drive_id for app in my_applications]
    available_drives = [
        drive for drive in approved_drives
        if drive.id not in applied_drive_ids
    ]

    return render_template(
        'student/dashboard.html',
        student=student,
        available_drives=available_drives,
        my_applications=my_applications
    )


@student_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    student = Student.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        student.full_name = request.form.get('full_name')
        student.phone = request.form.get('phone')
        student.department = request.form.get('department')
        student.year = request.form.get('year')
        cgpa = request.form.get('cgpa')
        student.cgpa = float(cgpa) if cgpa else None
        student.resume_url = request.form.get('resume_url')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('student.profile'))

    return render_template('student/profile.html', student=student)

@student_bp.route('/drives')
@login_required
@student_required
def drives():
    student = Student.query.filter_by(user_id=current_user.id).first()

    approved_drives = PlacementDrive.query.filter_by(
        is_approved=True,
        is_active=True
    ).order_by(PlacementDrive.created_at.desc()).all()

    my_applications = Application.query.filter_by(student_id=student.id).all()
    applied_drive_ids = [app.drive_id for app in my_applications]

    drives_with_status = []
    for drive in approved_drives:
        has_applied = drive.id in applied_drive_ids
        drives_with_status.append({
            'drive': drive,
            'has_applied': has_applied
        })

    return render_template('student/drives.html', drives_with_status=drives_with_status, student=student)

@student_bp.route('/drive/<int:drive_id>')
@login_required
@student_required
def drive_detail(drive_id):
    student = Student.query.filter_by(user_id=current_user.id).first()
    drive = PlacementDrive.query.filter_by(id=drive_id, is_approved=True).first_or_404()

    has_applied = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive_id
    ).first() is not None

    return render_template('student/drive_detail.html', drive=drive, has_applied=has_applied, student=student)

@student_bp.route('/drive/<int:drive_id>/apply', methods=['POST'])
@login_required
@student_required
def apply_drive(drive_id):
    student = Student.query.filter_by(user_id=current_user.id).first()

    if student.is_blacklisted:
        flash('Your account has been blacklisted. You cannot apply for placement drives.', 'danger')
        return redirect(url_for('student.dashboard'))

    drive = PlacementDrive.query.filter_by(id=drive_id, is_approved=True, is_active=True).first_or_404()

    existing_application = Application.query.filter_by(
        student_id=student.id,
        drive_id=drive_id
    ).first()

    if existing_application:
        flash('You have already applied for this placement drive.', 'warning')
        return redirect(url_for('student.drive_detail', drive_id=drive_id))

    if drive.required_cgpa and student.cgpa and student.cgpa < drive.required_cgpa:
        flash(f'Your CGPA does not meet the minimum requirement of {drive.required_cgpa}.', 'warning')
        return redirect(url_for('student.drive_detail', drive_id=drive_id))

    application = Application(
        student_id=student.id,
        drive_id=drive_id,
        status='Applied'
    )

    db.session.add(application)
    db.session.commit()

    flash('Application submitted successfully!', 'success')
    return redirect(url_for('student.applications'))

@student_bp.route('/applications')
@login_required
@student_required
def applications():
    student = Student.query.filter_by(user_id=current_user.id).first()

    if not student:
        abort(403)

    my_applications = (
        db.session.query(Application, PlacementDrive, Company)
        .join(PlacementDrive, Application.drive_id == PlacementDrive.id)
        .join(Company, PlacementDrive.company_id == Company.id)
        .filter(Application.student_id == student.id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    return render_template(
        'student/applications.html',
        my_applications=my_applications
    )

