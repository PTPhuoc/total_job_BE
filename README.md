# DEVELOPING AN ONLINE RECRUITMENT SYSTEM USING MACHINE LEARNING APPLICATIONS TO DETECT FRAUDULENT RECRUITMENT
Backend API for total_job – a full-stack job recruitment platform connecting Job Seekers, Employers, and Administrators. Built with Django, Django REST Framework, and Microsoft SQL Server.

## Features
### Authentication & User Management
- Multi-role registration (Job Seeker / Employer / Admin)
- JWT authentication with refresh tokens
- Role-based access control
### Job Seeker Module
- Profile management (education, experience, skills)
- Apply to jobs with duplicate prevention
- Track application status (Pending → Reviewed → Interview → Hired/Rejected)
- Save favorite jobs
### Employer Module
- Company profile management
- Post, edit, close job listings with auto-expiry
- View and manage applicants
- Recruitment analytics dashboard
### Admin Module
- User account management (approve/suspend)
- Job posting moderation
- Manage categories, industries, locations
- Platform statistics
### Public API
- Browse jobs and companies (no login required)
- Basic search functionality
### Tech Stack
|Layer|Technology|
|-----|----------|
|Framework|Django + Django REST Framework|
|Database|Microsoft SQL Server|
|Authentication|JWT (JSON Web Tokens)|
|API|RESTful|
|Email|SMTP (Gmail/Outlook)|
|Version|Control	Git/GitHub|
### Installation
Prerequisites
- Python 3.9+
- Microsoft SQL Server
- pip (Python package manager)
## Steps
Clone repository
```
git clone https://github.com/PTPhuoc/total_job_BE.git
cd total_job_BE
```
### Create virtual environment
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
### Install dependencies
```
pip install -r requirements.txt
```
### Configure database
Update settings.py with your SQL Server credentials:
```
DATABASES = {
    'default': {
        'ENGINE': 'mssql',
        'NAME': 'your_db_name',
        'USER': 'your_username',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '',
        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    }
}
```
### Run migrations
```
python manage.py migrate
```
### Create superuser (for admin access)
```
python manage.py createsuperuser
```
### Run development server
```
python manage.py runserver
```
API will be available at http://localhost:8000

## Project Structure
```
total_job_BE/
├── manage.py
├── requirements.txt
├── total_job/              # Main project folder
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/                    # Django apps
│   ├── accounts/            # Authentication & users
│   ├── jobs/                # Job postings
│   ├── applications/        # Job applications
│   ├── employers/           # Employer profiles
│   └── admin_panel/         # Admin features
├── static/
├── media/
└── test_and_train/          # Unit tests
```
## API Endpoints
|Method|Endpoint|Description|Access|
|------|--------|-----------|------|
|POST|/api/auth/register/|User|registration|Public|
|POST|/api/auth/login/|Get|JWT token|Public|
|POST|/api/auth/refresh/|Refresh token|Public|
|GET|/api/jobs/|List jobs (with filters)|Public|
|GET|/api/jobs/{id}/|Job details|Public|
|POST|/api/applications/|Apply to job|Job Seeker|
|GET|/api/applications/my/|My applications|Job Seeker|
|POST|/api/employer/jobs/|Post new job|Employer|
|GET|/api/employer/dashboard/|Employer stats|Employer|
|GET|/api/admin/users/|List users|Admin|
|POST|/api/admin/moderate/{id}/|Moderate job|Admin|
Full API documentation available via Postman collection (contact me).

## Testing
Run unit tests:
```
python manage.py test apps
```
Test coverage includes:
- Authentication flows
- Duplicate application prevention
- Role-based access validation
- Job posting moderation workflow

## License
This project is licensed under the MIT License.

## Contact
Phuoc - GitHub
Project Link: https://github.com/PTPhuoc/total_job_BE
