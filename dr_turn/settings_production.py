from .settings import *
import os

# Production settings
DEBUG = False
SERVERE = True

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
ALLOWED_HOSTS = [
    'drhmd.ir',
    'www.drhmd.ir',
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    '*',
]

CSRF_TRUSTED_ORIGINS = [
    'https://drhmd.ir',
    'https://www.drhmd.ir',
    'http://localhost',
    'http://127.0.0.1',
]

# Redis configuration for Docker
REDIS_HOST = os.environ.get('REDIS_HOST', 'lo