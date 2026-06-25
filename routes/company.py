from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db, Company, PlacementDrive, Application, Student
from datetime import datetime

company_bp = Blueprint('company', __name__, url_prefix='/company')

def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'company':
            flash('Access denied. Company privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        if not current_user.is_approved:
            flash('Your company account is pending admin approval.', 'warning')
            return redirect(url_for('auth.logout'))
        return f(*args, **kwargs)
    return decorated_function

@company_bp.route('/dashboard')
@login_required
@company_required
def dashboard():
    company = Company.query.filter_by(user_id=current_user.id).first()

    drives = PlacementDrive.query.filter_by(company_id=company.id).order_by(
        PlacementDrive.created_at.desc()
    ).all()

    drive_stats = []
    for drive in drives:
        applicant_count = Application.query.filter_by(drive_id=drive.id).count()
        drive_stats.append({
            'drive': drive,
            'applicant_count': applicant_count
        })

    return render_template('company/dashboard.html', company=company, drive_stats=drive_stats)

@company_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@company_required
def profile():
    company = Company.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        company.company_name = request.form.get('company_name')
        company.industry = request.form.get('industry')
        company.website = request.form.get('website')
        company.contact_person = request.form.get('contact_person')
        company.phone = request.form.get('phone')
        company.address = request.form.get('address')

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('company.profile'))

    return render_template('company/profile.html', company=company)

@company_bp.route('/drives')
@login_required
@company_required
def drives():
    company = Company.query.filter_by(user_id=current_user.id).first()
    drives = PlacementDrive.query.filter_by(company_id=company.id).order_by(
        PlacementDrive.created_at.desc()
    ).all()

    return render_template('company/drives.html', drives=drives)

@company_bp.route('/drive/create', methods=['GET', 'POST'])
@login_required
@company_required
def create_drive():
    company = Company.query.filter_by(user_id=current_user.id).first()

    if company.is_blacklisted:
        flash('Your company has been blacklisted and cannot create placement drives.', 'danger')
        return redirect(url_for('company.dashboard'))

    if request.method == 'POST':
        job_title = request.form.get('job_title')
        job_description = request.form.get('job_description')
        job_type = request.form.get('job_type')
        location = request.form.get('location')
        salary = request.form.get('salary')
        required_cgpa = request.form.get('required_cgpa')
        eligible_departments = request.form.get('eligible_departments')
        eligible_years = request.form.get('eligible_years')
        total_positions = request.form.get('total_positions')
        deadline = request.form.get('deadline')

        drive = PlacementDrive(
            company_id=company.id,
            job_title=job_title,
            job_description=job_description,
            job_type=job_type,
            location=location,
            salary=salary,
            required_cgpa=float(required_cgpa) if required_cgpa else None,
            eligible_departments=eligible_departments,
            eligible_years=eligible_years,
            total_positions=int(total_positions) if total_positions else None,
            deadline=datetime.strptime(deadline, '%Y-%m-%d') if deadline else None,
            is_approved=False,
            is_active=True
        )

        db.session.add(drive)
        db.session.commit()

        flash('Placement drive created successfully! Awaiting admin approval.', 'success')
        return redirect(url_for('company.drives'))

    return render_template('company/create_drive.html')

@company_bp.route('/drive/edit/<int:drive_id>', methods=['GET', 'POST'])
@login_required
@company_required
def edit_drive(drive_id):
    company = Company.query.filter_by(user_id=current_user.id).first()
    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()

    if request.method == 'POST':
        drive.job_title = request.form.get('job_title')
        drive.job_description = request.form.get('job_description')
        drive.job_type = request.form.get('job_type')
        drive.location = request.form.get('location')
        drive.salary = request.form.get('salary')
        required_cgpa = request.form.get('required_cgpa')
        drive.required_cgpa = float(required_cgpa) if required_cgpa else None
        drive.eligible_departments = request.form.get('eligible_departments')
        drive.eligible_years = request.form.get('eligible_years')
        total_positions = request.form.get('total_positions')
        drive.total_positions = int(total_positions) if total_positions else None
        deadline = request.form.get('deadline')
        drive.deadline = datetime.strptime(deadline, '%Y-%m-%d') if deadline else None

        db.session.commit()
        flash('Placement drive updated successfully!', 'success')
        return redirect(url_for('company.drives'))

    return render_template('company/edit_drive.html', drive=drive)

@company_bp.route('/drive/close/<int:drive_id>')
@login_required
@company_required
def close_drive(drive_id):
    company = Company.query.filter_by(user_id=current_user.id).first()
    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()

    drive.is_active = False
    db.session.commit()

    flash(f'Placement drive "{drive.job_title}" has been closed.', 'success')
    return redirect(url_for('company.drives'))

@company_bp.route('/drive/<int:drive_id>/applications')
@login_required
@company_required
def drive_applications(drive_id):
    company = Company.query.filter_by(user_id=current_user.id).first()
    drive = PlacementDrive.query.filter_by(id=drive_id, company_id=company.id).first_or_404()

    applications = db.session.query(Application, Student).join(Student).filter(
        Application.drive_id == drive_id
    ).order_by(Application.applied_at.desc()).all()

    return render_template('company/applications.html', drive=drive, applications=applications)

@company_bp.route('/application/<int:application_id>/update', methods=['POST'])
@login_required
@company_required
def update_application_status(application_id):
    application = Application.query.get_or_404(application_id)
    company = Company.query.filter_by(user_id=current_user.id).first()

    if application.placement_drive.company_id != company.id:
        flash('Access denied.', 'danger')
        return redirect(url_for('company.dashboard'))

    new_status = request.form.get('status')
    if new_status in ['Applied', 'Shortlisted', 'Selected', 'Rejected']:
        application.status = new_status
        application.updated_at = datetime.utcnow()
        db.session.commit()
        flash(f'Application status updated to {new_status}.', 'success')
    else:
        flash('Invalid status.', 'danger')

    return redirect(url_for('company.drive_applications', drive_id=application.drive_id))
