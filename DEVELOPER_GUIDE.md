# Dr. Turn - Developer Guide

## Project Overview

Dr. Turn is a comprehensive medical appointment booking system built with Django 5.2, designed specifically for Persian/Iranian healthcare providers. It supports the full workflow from doctor registration to patient consultations with Persian calendar integration.

## Key Features
- **Multi-role System**: Patients, Doctors, Clinic Admins, System Admins
- **Persian Calendar**: Full Jalali date support with django-jalali
- **Appointment Management**: Complex booking system with time slot management
- **Payment Integration**: Wallet-based payment system with transaction tracking
- **Real-time Chat**: WebSocket-based consultation system
- **Medical Records**: Comprehensive patient record management
- **SMS Integration**: Automated notifications via SMS.ir

## Technology Stack

### Backend
- **Django 5.2** - Main framework
- **Django REST Framework 3.16** - API endpoints
- **django-jalali 7.4.0** - Persian calendar support
- **Django Channels 4.2.2** - Real-time WebSocket support
- **Celery 5.5.2** - Background task processing
- **Redis** - Caching and message broker

### Frontend
- **Django Templates** - Server-side rendering
- **Tailwind CSS 4.0.1** - Utility-first CSS framework
- **Vanilla JavaScript** - Client-side interactions
- **CKEditor** - Rich text editing

### Infrastructure
- **SQLite** (development) / **PostgreSQL** (production)
- **SMS.ir** - SMS service integration
- **WeasyPrint** - PDF report generation

## Project Structure

```
dr_hamedan/
├── dr_turn/              # Main project configuration
├── user/                 # Custom user authentication
├── doctors/              # Doctor profiles and management
├── patients/             # Patient records and management
├── clinics/              # Clinic profiles and operations
├── reservations/         # Core appointment booking system
├── wallet/               # Payment and transaction system
├── chatmed/              # Real-time chat for consultations
├── medimag/              # Medical articles and blog
├── docpages/             # Doctor content management
├── homecare/             # Home healthcare services
├── support/              # Customer support system
├── discounts/            # Discount and promotion system
├── sms_reminders/        # SMS notification system
├── templates/            # Django templates
├── assets/               # Static files
└── utils/                # Shared utilities
```

## Quick Start

### Prerequisites
- Python 3.13+
- Redis server
- Git

### Installation

1. **Clone and Setup**
```bash
git clone <repository-url>
cd dr_hamedan
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
pip install -r requirements.txt
```

2. **Database Setup**
```bash
python manage.py migrate
python manage.py createsuperuser
```

3. **Start Services**
```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A dr_turn worker -l info

# Terminal 3: Redis (if not running as service)
redis-server
```

## Core Architecture

### User Authentication
- **Custom User Model**: Phone-based authentication with OTP verification
- **Multiple User Types**: Patients, Doctors, Clinic Admins, System Admins
- **Persian Support**: Full Persian name and UI support

### Appointment System
The booking system is the core of the application:

1. **ReservationDay**: Admin publishes available booking dates
2. **Doctor Availability**: Doctors set weekly availability schedules
3. **Time Slot Generation**: System creates 30-minute appointment slots
4. **Booking Process**: Patients select slots and pay through wallet system
5. **Status Management**: Tracks appointment lifecycle (available → pending → confirmed → completed)

### Payment System
- **Wallet-based**: Each user has a digital wallet
- **Multi-balance Types**: Active, pending, and frozen balances
- **Transaction Tracking**: Complete audit trail for all transactions
- **Automatic Processing**: Appointments confirmed automatically upon payment

## Development Guidelines

### Code Standards
- Follow PEP 8 and Django conventions
- Use Persian for UI text, English for code documentation
- Always use `jmodels.jDateTimeField` for datetime fields
- Include verbose_name in Persian for all model fields

### Model Pattern Example
```python
from django_jalali.db import models as jmodels

class YourModel(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام')
    created_at = jmodels.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    user = models.ForeignKey(User, on_delete=models.CASCADE, 
                           related_name='your_models', verbose_name='کاربر')
    
    class Meta:
        verbose_name = 'مدل شما'
        verbose_name_plural = 'مدل‌های شما'
        ordering = ['-created_at']
```

### Template Pattern Example
```django
{% load jformat %}
{{ appointment.created_at|jformat:"%Y/%m/%d" }}
{% csrf_token %}
```

### View Pattern Example
```python
@login_required
def your_view(request):
    # Always check user permissions
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Include proper error handling
    try:
        # Your logic here
        pass
    except Exception as e:
        messages.error(request, 'خطا در انجام عملیات')
        return redirect('error_page')
```

## Key Applications

### 1. Reservations (`reservations/`)
**Core appointment booking system**
- Manages available dates and time slots
- Handles booking workflow and payment integration
- Provides booking services and utilities

### 2. Doctors (`doctors/`)
**Doctor profile and management**
- Doctor profiles with specializations
- Weekly availability management
- Earnings tracking and reporting
- Inter-doctor messaging system

### 3. Patients (`patients/`)
**Patient management and medical records**
- Patient demographic information
- Medical history and visit records
- Report generation with image support

### 4. Wallet (`wallet/`)
**Payment and transaction management**
- Multi-balance wallet system
- Transaction processing and tracking
- Payment gateway integration support

### 5. User (`user/`)
**Authentication and user management**
- Custom phone-based authentication
- OTP verification system
- Multi-role user support

## Database Schema Overview

### Key Relationships
```
User (1:1) Doctor
User (1:1) PatientsFile
User (1:1) Wallet

Doctor (1:N) Reservation
Doctor (N:1) Clinic
Doctor (1:N) DoctorAvailability

PatientsFile (1:N) Reservation
Reservation (N:1) ReservationDay
```

## Common Tasks

### Adding New Features
1. Create models with proper Meta classes
2. Generate and apply migrations
3. Create views with permission checks
4. Add URL patterns with namespacing
5. Create templates with Persian date support
6. Write tests for new functionality

### Working with Dates
```python
# Always use Jalali fields
from django_jalali.db import models as jmodels

# Convert between calendars
import jdatetime
jalali_date = jdatetime.date.fromgregorian(date=gregorian_date)
gregorian_date = jalali_date.togregorian()

# Format in templates
{{ date_field|jformat:"%Y/%m/%d" }}
```

### Database Operations
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only)
python manage.py flush
```

## API Integration

### SMS Integration
Configure SMS settings in `settings.py`:
```python
SMS_API_KEY = 'your-sms-ir-api-key'
SMS_LINE_NUMBER = '30007487130094'
```

### Payment Gateway
The wallet system is designed to integrate with Iranian payment gateways:
- Zarinpal
- Mellat Bank
- Parsian Bank
- Custom gateway implementation

## Deployment

### Production Checklist
- [ ] Set `DEBUG = False`
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for production
- [ ] Configure proper static file serving
- [ ] Set up SSL/HTTPS
- [ ] Configure Celery with supervisor
- [ ] Set up monitoring and logging

### Environment Variables
```env
DEBUG=False
SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://user:pass@localhost/db_name
REDIS_URL=redis://localhost:6379/0
SMS_API_KEY=your-sms-api-key
```

## Testing

### Run Tests
```bash
# All tests
python manage.py test

# Specific app
python manage.py test doctors

# With coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Structure
```python
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

class YourTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phone='09123456789',
            first_name='احمد',
            last_name='محمدی'
        )
    
    def test_your_functionality(self):
        # Your test logic
        pass
```

## Performance Considerations

### Database Optimization
- Use `select_related()` and `prefetch_related()`
- Add database indexes for frequently queried fields
- Monitor query performance with Django Debug Toolbar

### Caching Strategy
- Redis for session and data caching
- Template fragment caching for expensive operations
- Database query result caching

## Security Guidelines

- Always validate user input
- Use CSRF protection for forms
- Implement proper permission checks
- Sanitize user-generated content
- Use HTTPS in production
- Keep dependencies updated

## Troubleshooting

### Common Issues
1. **Persian Date Issues**: Ensure `django-jalali` is properly configured
2. **Static Files**: Run `python manage.py collectstatic`
3. **Celery Not Working**: Check Redis connection and worker process
4. **SMS Not Sending**: Verify SMS.ir API credentials

### Debugging Tools
- Django Debug Toolbar for development
- Python debugger (`import pdb; pdb.set_trace()`)
- Django logging framework
- Celery monitoring tools

## Contributing

### Development Workflow
1. Create feature branch: `git checkout -b feature/feature-name`
2. Follow coding standards and write tests
3. Update documentation if needed
4. Create pull request with clear description

### Code Review Checklist
- [ ] Follows project coding standards
- [ ] Includes tests for new functionality
- [ ] Persian UI elements properly implemented
- [ ] Security considerations addressed
- [ ] Performance implications considered

## Resources

### Documentation
- [Django Documentation](https://docs.djangoproject.com/)
- [django-jalali Documentation](https://github.com/slashmili/django-jalali)
- [Django Channels Documentation](https://channels.readthedocs.io/)

### Tools
- Django Debug Toolbar for development debugging
- pgAdmin for PostgreSQL management
- Redis Desktop Manager for Redis monitoring
- Postman for API testing

This guide provides the essential information needed to understand, develop, and maintain the Dr. Turn application. For specific implementation details, refer to the code comments and individual application documentation. 