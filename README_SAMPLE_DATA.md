# Sample Data Creation for Dr. Turn Project

This document explains how to create sample data for all models in the Dr. Turn Django project.

## Overview

The project includes a comprehensive Django management command that creates realistic sample data for all models across all apps. This is useful for:

- Development and testing
- Demonstrating the application's features
- Populating a fresh database with meaningful data
- Understanding the data structure and relationships

## Available Sample Data

The command creates sample data for the following models:

### Core Models
- **Users**: Admin, doctors, and patients with realistic Persian names
- **Cities**: Major Iranian cities
- **Specializations**: Medical specializations (داخلی, قلب و عروق, etc.)
- **Supplementary Insurances**: Iranian insurance companies

### Doctor Management
- **Doctors**: 10 doctors with profiles, specializations, and availability schedules
- **Doctor Availability**: Weekly schedules for each doctor
- **Doctor Comments**: Reviews and ratings from patients
- **Doctor Services**: Services offered by each doctor

### Patient Management
- **Patients**: 10 patients with medical histories and profiles
- **Patient Files**: Complete patient records

### Clinic Management
- **Clinics**: 3 sample clinics with addresses and contact information
- **Clinic Specialties**: Medical specialties offered by each clinic
- **Clinic Comments**: Patient reviews for clinics

### Appointment System
- **Reservation Days**: 30 days of available appointment slots
- **Reservations**: Sample appointments with various statuses
- **Reservation Comments**: Patient feedback on appointments

### Chat System
- **Chat Requests**: 20 chat requests between patients and doctors
- **Chat Rooms**: Active chat sessions
- **Messages**: Sample conversations in chat rooms

### Content Management
- **Posts**: Medical articles written by doctors
- **Articles**: Health-related articles with categories
- **Medical Lenses**: Medical content tags

### Financial System
- **Wallets**: User wallets with balances
- **Transactions**: Payment and withdrawal records
- **Payment Gateways**: Payment processing configurations

### Discount System
- **Discount Types**: Percentage, fixed amount, and buy-one-get-one
- **Discounts**: 5 active discounts with various conditions
- **Coupon Codes**: Unique discount codes
- **Discount Usage**: Records of discount applications

### Home Care Services
- **Service Categories**: Nursing, physiotherapy, etc.
- **Services**: 6 different home care services
- **Home Care Requests**: 10 service requests from patients

### SMS Reminders
- **SMS Settings**: System configuration for SMS reminders
- **SMS Templates**: Message templates for different reminder types
- **SMS Reminders**: 10 scheduled reminders for appointments

### Support System
- **Support Chat Rooms**: 5 customer support conversations
- **Support Messages**: Messages in support chats

### About Us Content
- **Contact Information**: Company contact details
- **About Us**: Company description and mission
- **FAQs**: Frequently asked questions
- **Team Members**: Company team information

## Usage

### Basic Usage

To create sample data without clearing existing data:

```bash
source env/bin/activate
python manage.py create_sample_data
```

### Clear and Create

To clear all existing data and create fresh sample data:

```bash
source env/bin/activate
python manage.py create_sample_data --clear
```

### Running the Command

1. **Activate your virtual environment**:
   ```bash
   source env/bin/activate
   ```

2. **Run the command**:
   ```bash
   python manage.py create_sample_data
   ```

3. **Monitor the output**:
   The command will show progress for each type of data being created.

## Sample Data Details

### Users and Authentication

**Admin User**:
- Phone: `09123456789`
- Password: `admin123`
- Email: `admin@drturn.ir`

**Doctor Users**:
- Phone: `09120000001` to `09120000010`
- Password: `doctor123`
- Emails: `doctor1@drturn.ir` to `doctor10@drturn.ir`

**Patient Users**:
- Phone: `09130000001` to `09130000010`
- Password: `patient123`
- Emails: `patient1@drturn.ir` to `patient10@drturn.ir`

### Sample Data Quantities

- **10 Doctors** with complete profiles and availability schedules
- **10 Patients** with medical histories
- **3 Clinics** with specialties and services
- **30 Reservation Days** (next 30 days)
- **Variable Reservations** (50% chance of being booked)
- **20 Chat Requests** with various statuses
- **15 Articles** in different categories
- **5 Discounts** with different types and conditions
- **6 Home Care Services** in different categories
- **10 SMS Reminders** for appointments

### Realistic Data

The sample data includes:
- **Persian names** for all users
- **Realistic Iranian cities** and addresses
- **Medical specializations** in Persian
- **Insurance companies** operating in Iran
- **Realistic consultation fees** (100,000 to 500,000 تومان)
- **Jalali dates** for all date fields
- **Persian content** for descriptions and notes

## Customization

You can modify the sample data by editing the `create_sample_data.py` file:

1. **Change quantities**: Modify the range values in loops
2. **Add more data**: Create additional entries in data arrays
3. **Modify content**: Change text content, names, or descriptions
4. **Adjust probabilities**: Change the random.choice() probabilities

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all apps are properly installed and migrated
2. **Database Errors**: Ensure the database is properly set up and migrations are applied
3. **Permission Errors**: Check file permissions for the management command

### Error Handling

The command uses database transactions, so if an error occurs:
- All changes will be rolled back
- No partial data will be saved
- Check the error message for specific issues

### Logs

The command provides detailed output showing:
- Number of records created for each model
- Success messages for each step
- Any errors that occur during creation

## Security Notes

- **Passwords**: All sample users have simple passwords for development
- **Personal Data**: Sample data uses fictional names and information
- **Production**: Never run this command on a production database

## Next Steps

After creating sample data:

1. **Test the application** with the sample data
2. **Explore different features** using the created accounts
3. **Modify data** as needed for specific testing scenarios
4. **Create additional data** for specific use cases

## Support

If you encounter issues with the sample data creation:

1. Check the Django logs for detailed error messages
2. Ensure all required dependencies are installed
3. Verify that all migrations have been applied
4. Check that the database is properly configured 