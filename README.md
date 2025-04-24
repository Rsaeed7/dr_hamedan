# Dr. Turn - Doctor Appointment Booking System

A Django application for managing doctor appointments and clinic operations.

## Features

### User Roles

1. **Patients**
   - Search for doctors by specialty, clinic, etc.
   - View doctor profiles with detailed information
   - Book appointments by selecting available time slots
   - Receive confirmation emails/notifications
   - View and manage appointments

2. **Doctors**
   - Personal dashboard with upcoming appointments
   - Define weekly availability with time ranges
   - View and filter appointments by status
   - Confirm, cancel, or mark appointments as completed
   - View earnings reports for selected periods

3. **Clinic Administrators**
   - Manage clinic profile (name, address, specialties, gallery)
   - Add or remove doctors affiliated with the clinic
   - View and manage all appointments for clinic doctors
   - Override doctor availability or appointment statuses

## Technical Stack

- **Backend**: Django, Django REST Framework
- **Frontend**: HTML, CSS (with Tailwind), JavaScript
- **Database**: SQLite (development), PostgreSQL (production recommended)
- **Calendar/Date**: Django Jalali Date for Persian calendar support
- **Payment**: Integrated wallet system (customizable for payment gateways)

## Installation

1. Clone the repository
   ```
   git clone https://github.com/yourusername/dr_turn.git
   cd dr_turn
   ```

2. Create a virtual environment and install dependencies
   ```
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   pip install -r requirements.txt
   ```

3. Apply migrations
   ```
   python manage.py migrate
   ```

4. Create a superuser
   ```
   python manage.py createsuperuser
   ```

5. Run the development server
   ```
   python manage.py runserver
   ```

## Project Structure

- **doctors**: Manages doctor profiles and availability
- **clinics**: Manages clinic profiles and doctor affiliations
- **patients**: Handles patient data and appointment history
- **reservations**: Core system for appointment booking and management
- **wallet**: Manages payments and transactions

## Key Workflows

### Appointment Booking

1. Patient searches for a doctor
2. Selects a date and available time slot
3. Enters contact/payment details
4. System creates a pending reservation
5. Upon successful payment, appointment is confirmed

### Doctor Management

1. Doctor defines weekly availability blocks
2. Views and manages upcoming appointments
3. Confirms, cancels, or completes appointments
4. Views earnings for selected periods

### Clinic Administration

1. Clinic admin manages clinic profile and specialties
2. Adds/removes doctors under the clinic
3. Views aggregate calendar of all doctors' bookings
4. Can override appointment statuses when needed

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 