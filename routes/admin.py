from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Student, Company, PlacementDrive, Application
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students = Student.query.count()
    total_companies = Company.query.count()
    total_drives = PlacementDrive.query.count()
    total_applications = Application.query.count()

    pending_companies = User.query.filter_by(role='company', is_approved=False).count()
    pending_drives = PlacementDrive.query.filter_by(is_approved=False).count()

    recent_applications = db.session.query(
        Application, Student, PlacementDrive, Company
    ).join(Student).join(PlacementDrive).join(Company).order_by(
        Application.applied_at.desc()
    ).limit(10).all()

    return render_template('admin/dashboard.html',
                           total_students=total_students,
                            total_companies=total_companies,
                            total_drives=total_drives,
                            total_applications=total_applications,
                            pending_companies=pending_companies,
                            pending_drives=pending_drives,
                            recent_applications=recent_applications)

@admin_bp.route('/companies')
@login_required
@admin_required
def companies():
    search = request.args.get('search', '')
    if search:
        companies = Company.query.filter(Company.company_name.like(f'%{search}%')).all()
    else:
        companies = Company.query.all()

    return render_template('admin/companies.html', companies=companies, search=search)

@admin_bp.route('/company/approve/<int:company_id>')
@login_required
@admin_required
def approve_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.user.is_approved = True
    db.session.commit()
    flash(f'Company {company.company_name} has been approved.', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/company/reject/<int:company_id>')
@login_required
@admin_required
def reject_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.user.is_approved = False
    db.session.commit()
    flash(f'Company {company.company_name} has been rejected.', 'warning')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/company/blacklist/<int:company_id>')
@login_required
@admin_required
def blacklist_company(company_id):
    company = Company.query.get_or_404(company_id)
    company.is_blacklisted = not company.is_blacklisted
    status = 'blacklisted' if company.is_blacklisted else 'removed from blacklist'
    db.session.commit()
    flash(f'Company {company.company_name} has been {status}.', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/company/delete/<int:company_id>', methods=['POST'])
@login_required
@admin_required
def delete_company(company_id):
    company = Company.query.get_or_404(company_id)
    user = company.user
    db.session.delete(company)
    db.session.delete(user)
    db.session.commit()
    flash('Company has been deleted.', 'success')
    return redirect(url_for('admin.companies'))

@admin_bp.route('/students')
@login_required
@admin_required
def students():
    search = request.args.get('search', '')
    search_type = request.args.get('search_type', 'name')

    if search:
        if search_type == 'name':
            students = Student.query.filter(Student.full_name.like(f'%{search}%')).all()
        elif search_type == 'student_id':
            students = Student.query.filter(Student.student_id.like(f'%{search}%')).all()
        elif search_type == 'phone':
            students = Student.query.filter(Student.phone.like(f'%{search}%')).all()
        else:
            students = Student.query.all()
    else:
        students = Student.query.all()

    return render_template('admin/students.html', students=students, search=search, search_type=search_type)

@admin_bp.route('/student/blacklist/<int:student_id>')
@login_required
@admin_required
def blacklist_student(student_id):
    student = Student.query.get_or_404(student_id)
    student.is_blacklisted = not student.is_blacklisted
    status = 'blacklisted' if student.is_blacklisted else 'removed from blacklist'
    db.session.commit()
    flash(f'Student {student.full_name} has been {status}.', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/student/delete/<int:student_id>', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    user = student.user
    db.session.delete(student)
    db.session.delete(user)
    db.session.commit()
    flash('Student has been deleted.', 'success')
    return redirect(url_for('admin.students'))

@admin_bp.route('/drives')
@login_required
@admin_required
def drives():
    status_filter = request.args.get('status', 'all')

    query = PlacementDrive.query

    if status_filter == 'pending':
        query = query.filter_by(is_approved=False)
    elif status_filter == 'approved':
        query = query.filter_by(is_approved=True, is_active=True)
    elif status_filter == 'closed':
        query = query.filter_by(is_active=False)

    drives = query.order_by(PlacementDrive.created_at.desc()).all()

    return render_template('admin/drives.html', drives=drives, status_filter=status_filter)

@admin_bp.route('/drive/approve/<int:drive_id>')
@login_required
@admin_required
def approve_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.is_approved = True
    db.session.commit()
    flash(f'Placement drive "{drive.job_title}" has been approved.', 'success')
    return redirect(url_for('admin.drives'))

@admin_bp.route('/drive/reject/<int:drive_id>')
@login_required
@admin_required
def reject_drive(drive_id):
    drive = PlacementDrive.query.get_or_404(drive_id)
    drive.is_approved = False
    db.session.commit()
    flash(f'Placement drive "{drive.job_title}" has been rejected.', 'warning')
    return redirect(url_for('admin.drives'))

@admin_bp.route('/applications')
@login_required
@admin_required
def applications():
    applications = db.session.query(
        Application, Student, PlacementDrive, Company
    ).join(Student).join(PlacementDrive).join(Company).order_by(
        Application.applied_at.desc()
    ).all()

    return render_template('admin/applications.html', applications=applications)
