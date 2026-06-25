# Placify - Placement-Portal-Application

A comprehensive web application for managing campus placements, built with Flask, SQLite, and Bootstrap.

## Features

### Admin Features
- Dashboard with statistics and analytics
- Approve/reject company registrations
- Approve/reject placement drives
- Manage students (view, search, blacklist, delete)
- Manage companies (view, search, blacklist, delete)
- View all applications and historical data

### Company Features
- Self-registration (requires admin approval)
- Create and manage placement drives
- View student applications
- Update application status (Applied, Shortlisted, Selected, Rejected)
- Edit company profile

### Student Features
- Self-registration (instant activation)
- Browse approved placement drives
- Apply for drives
- View application status and history
- Edit student profile

## Tech Stack

- **Backend:** Flask (Python)
- **Frontend:** Jinja2 Templates, HTML, CSS, Bootstrap 5
- **Database:** SQLite

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python3 app.py
```

3. Access the application at `http://localhost:5000`

## Default Admin Credentials

- **Email:** admin@placify.portal
- **Password:** admin123

## Database

The SQLite database (`placement_portal.db`) is created automatically on first run. The database includes:

- **users** - All user accounts (admin, company, student)
- **students** - Student profile information
- **companies** - Company profile information
- **placement_drives** - Job postings by companies
- **applications** - Student applications to drives

## Business Rules

1. **Companies** must be approved by admin before they can login
2. **Placement drives** must be approved by admin before students can see them
3. **Students** cannot apply to the same drive more than once (enforced at database level)
4. **Blacklisted** companies and students cannot perform actions
5. **CGPA requirements** are enforced when students apply
6. **Application history** is maintained and immutable

## Application Structure

```
placement-portal/
├── app.py                  # Main Flask application
├── config.py               # Configuration settings
├── models.py               # Database models
├── requirements.txt        # Python dependencies
├── routes/
│   ├── auth.py            # Authentication routes
│   ├── admin.py           # Admin routes
│   ├── company.py         # Company routes
│   └── student.py         # Student routes
├── templates/
│   ├── base.html          # Base template
│   ├── login.html
│   ├── register_student.html
│   ├── register_company.html
│   ├── admin/             # Admin templates
│   ├── company/           # Company templates
│   └── student/           # Student templates
└── instance/placify.db    # SQLite database (auto-created)
```

## Usage Guide

### For Admin

1. Login with default credentials
2. Navigate to "Companies" to approve/reject company registrations
3. Navigate to "Drives" to approve/reject placement drives
4. Navigate to "Students" to search and manage students
5. View all applications in "Applications" section

### For Companies

1. Register through the company registration page
2. Wait for admin approval
3. After approval, login and create placement drives
4. View applications for your drives
5. Update application status for candidates

### For Students

1. Register through the student registration page
2. Login immediately (no approval needed)
3. Browse approved placement drives
4. Apply for drives that match your profile
5. Track application status in "My Applications"

## Security Features

- Password hashing using Werkzeug
- Role-based access control
- Session management with Flask-Login
- CSRF protection (Flask default)
- Database constraints to prevent duplicate applications
