# PLASU Examination Management System

A comprehensive examination resource management and allocation system designed for Plateau State University (PLASU).

## Features

### Core Modules

1. **Authentication & User Management**
   - Multi-role system: Admin, Exam Officer, Invigilator, Student
   - Role-based dashboards and permissions
   - User profile management
   - Password management

2. **Academic Management**
   - Faculty and department management
   - Course creation and management
   - Student enrollment tracking
   - Program management

3. **Examination Scheduling**
   - Exam session management
   - Timetable creation
   - Conflict detection and resolution
   - Question paper management
   - Attendance tracking

4. **Venue Management**
   - Hall/venue management with capacity tracking
   - Facility management
   - Venue availability scheduling
   - Rating and feedback system
   - Layout management

5. **Smart Allocation Engine**
   - Automatic student seating allocation
   - Invigilator assignment
   - Seating plan generation
   - Conflict detection and resolution
   - Allocation rules engine

6. **Invigilator Management**
   - Invigilator profiles and availability
   - Performance tracking
   - Training records
   - Leave management
   - Notification system

7. **Reporting & Analytics**
   - PDF report generation
   - Exam timetables
   - Seating plans
   - Attendance reports
   - Performance analytics
   - Scheduled reports

## Installation

### Prerequisites

- Python 3.8+
- Django 4.2+
- PostgreSQL or SQLite (for development)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd plasu_exam_system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy the .env file and update with your settings
   # The .env file contains sensitive information and should not be committed to git
   # Update the following variables:
   # - SECRET_KEY: Generate a new secret key for production
   # - DEBUG: Set to False in production
   # - ALLOWED_HOSTS: Add your domain in production
   # - Database settings: Configure your database connection
   # - Email settings: Configure email for notifications
   ```

5. **Database setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**
   ```bash
   python manage.py collectstatic
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
plasu_exam_system/
├── manage.py
├── config/                  # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/            # Users, roles, auth
│   ├── academics/           # Faculty, dept, course, student
│   ├── exams/               # Exam schedule, timetable
│   ├── venues/              # Halls, rooms, capacity
│   ├── allocation/          # Smart allocation logic
│   ├── invigilators/        # Invigilator assignment
│   └── reports/             # PDF export, analytics
├── templates/
├── static/
└── requirements.txt
```

## Usage

### Admin Access

1. Access the admin panel at `/admin/`
2. Create faculties, departments, and courses
3. Set up exam sessions
4. Add venues and their layouts
5. Create user accounts with appropriate roles

### Exam Officer Workflow

1. Create exam sessions
2. Schedule exams with venues and invigilators
3. Generate seating plans automatically
4. Manage conflicts and allocations
5. Generate reports

### Invigilator Workflow

1. Complete profile setup
2. Update availability
3. Accept/reject assignments
4. View schedules
5. Track performance

### Student Workflow

1. View exam schedules
2. Check seating arrangements
3. Access timetables
4. View results (when published)

## Key Features

### Smart Allocation Engine

- **Automatic Seating**: Intelligently assigns students to seats based on department separation
- **Conflict Detection**: Automatically detects scheduling conflicts
- **Load Balancing**: Distributes workload evenly among invigilators
- **Flexible Rules**: Configurable allocation rules for different scenarios

### Reporting System

- **PDF Generation**: Professional PDF reports for timetables, seating plans, and analytics
- **Scheduled Reports**: Automated report generation and delivery
- **Custom Templates**: Customizable report templates
- **Export Options**: Multiple export formats available

### Notification System

- **Email Notifications**: Automated email alerts for assignments and updates
- **In-App Notifications**: Real-time notifications within the system
- **SMS Integration**: (Optional) SMS notifications for critical updates

## API Endpoints

The system provides RESTful APIs for:

- User authentication
- Exam management
- Venue booking
- Allocation management
- Report generation

## Security Features

- Role-based access control
- Secure file handling
- Input validation and sanitization
- CSRF protection
- SQL injection prevention

## Performance Optimization

- Database query optimization
- Efficient file handling
- Caching strategies
- Background task processing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and queries, please contact:
- Email: support@plasu.edu.ng
- Phone: +234 XXX XXX XXXX

## Changelog

### Version 1.0.0
- Initial release with core functionality
- User management and authentication
- Exam scheduling and allocation
- Reporting system
- Venue management
- Invigilator management
