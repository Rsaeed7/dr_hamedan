# Server Deployment Guide

This guide will help you deploy the Dr. Turn project to your production server.

## Server Information
- **Hostname**: Dr. Turn Server
- **IP**: 62.60.198.172
- **Username**: root
- **Password**: 06q8t
- **Project Path**: /home/siavash-rahimi/Desktop/dr_hamedan

## Quick Fix for Current Issues

If you're experiencing the logging directory error, run these commands on your server:

```bash
# SSH into your server
ssh root@62.60.198.172
# Password: 06q8t

# Navigate to project directory
cd /home/siavash-rahimi/Desktop/dr_hamedan

# Activate virtual environment
source env/bin/activate

# Create missing directories
mkdir -p logs static media data

# Set proper permissions
chmod 755 logs static media data

# Run the fix script
python fix_server.py
```

## Complete Deployment Process

### 1. Connect to Server
```bash
ssh root@62.60.198.172
# Password: 06q8t
```

### 2. Navigate to Project
```bash
cd /home/siavash-rahimi/Desktop/dr_hamedan
```

### 3. Activate Virtual Environment
```bash
source env/bin/activate
```

### 4. Set Environment to Production
```bash
python manage_env.py production
```

### 5. Create/Update .env File
```bash
# Create .env file if it doesn't exist
python manage_env.py init

# Edit .env file with production settings
nano .env
```

Add these production settings to your `.env` file:
```bash
DJANGO_ENVIRONMENT=production
SECRET_KEY=your-production-secret-key-here
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@louhandicrafts.com
ADMIN_EMAIL=admin@louhandicrafts.com
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
```

### 6. Install Dependencies
```bash
# Install dependencies
pip install -r requirements.txt
```

### 7. Database Setup (SQLite)
```bash
# SQLite database will be created automatically
# No additional setup required
```

### 8. Run Django Commands
```bash
# Check for issues
python manage.py check

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser (if needed)
python manage.py createsuperuser
```

### 9. Set Up Nginx (if not already configured)
```bash
# Check nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 10. Set Up Gunicorn (if using)
```bash
# Install gunicorn
pip install gunicorn

# Test gunicorn
gunicorn --bind 0.0.0.0:8000 dr_turn.wsgi:application
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Logging Directory Error
```bash
# Create logs directory
mkdir -p logs
chmod 755 logs
```

#### 2. Static Files Not Found
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check nginx configuration for static files
sudo nano /etc/nginx/nginx.conf
```

#### 3. Database Connection Error
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connection
python manage.py dbshell
```

#### 4. Permission Issues
```bash
# Set proper ownership
sudo chown -R www-data:www-data /home/siavash-rahimi/Desktop/dr_hamedan

# Set proper permissions
sudo chmod -R 755 /home/siavash-rahimi/Desktop/dr_hamedan
```

#### 5. Environment Variables Not Loading
```bash
# Check if .env file exists
ls -la .env

# Check environment
python manage_env.py status
```

## Monitoring and Maintenance

### Check Application Status
```bash
# Check Django status
python manage.py check

# Check logs
tail -f logs/django.log
tail -f logs/error.log
```

### Backup Database
```bash
# Backup SQLite (if using)
cp data/db.sqlite3 data/db.sqlite3.backup

# Backup PostgreSQL (if using)
pg_dump dr_turn_production_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Update Application
```bash
# Pull latest changes
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart application
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## Security Checklist

- [ ] DEBUG = False in production settings
- [ ] Strong SECRET_KEY
- [ ] HTTPS enabled
- [ ] Database password is secure
- [ ] Email credentials are secure
- [ ] Stripe keys are production keys
- [ ] File permissions are correct
- [ ] Firewall is configured
- [ ] Regular backups are scheduled

## Support

If you encounter issues:

1. Check the logs: `tail -f logs/error.log`
2. Run the fix script: `python fix_server.py`
3. Check Django status: `python manage.py check`
4. Verify environment: `python manage_env.py status` 