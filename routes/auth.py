from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Student, Company

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'company':
            return redirect(url_for('company.dashboard'))
        elif current_user.role == 'student':
            return redirect(url_for('student.dashboard'))
    return render_template('index.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.role == 'admin':
                login_user(user)
                return redirect(url_for('admin.dashboard'))
            elif not user.is_approved:
                flash('Your account is pending approval. Please wait for admin approval.', 'warning')
                return redirect(url_for('auth.login'))
            else:
                login_user(user)
                return redirect(url_for('auth.index'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')

@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        student_id = request.form.get('student_id')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        department = request.form.get('department')
        year = request.form.get('year')
        cgpa = request.form.get('cgpa')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register_student'))

        if Student.query.filter_by(student_id=student_id).first():
            flash('Student ID already registered', 'danger')
            return redirect(url_for('auth.register_student'))

        user = User(email=email, role='student', is_approved=True)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        student = Student(
            user_id=user.id,
            student_id=student_id,
            full_name=full_name,
            phone=phone,
            department=department,
            year=year,
            cgpa=float(cgpa) if cgpa else None
        )
        db.session.add(student)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register_student.html')

@auth_bp.route('/register/company', methods=['GET', 'POST'])
def register_company():
    if current_user.is_authenticated:
        return redirect(url_for('auth.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        company_name = request.form.get('company_name')
        industry = request.form.get('industry')
        website = request.form.get('website')
        contact_person = request.form.get('contact_person')
        phone = request.form.get('phone')
        address = request.form.get('address')

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register_company'))

        user = User(email=email, role='company', is_approved=False)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        company = Company(
            user_id=user.id,
            company_name=company_name,
            industry=industry,
            website=website,
            contact_person=contact_person,
            phone=phone,
            address=address
        )
        db.session.add(company)
        db.session.commit()

        flash('Registration successful! Your account is pending admin approval.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register_company.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))
