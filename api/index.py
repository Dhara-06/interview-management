"""
Vercel serverless function for Django AI Interviewer
"""
import os
import sys
from django.core.wsgi import get_wsgi_application

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_production')

# Get WSGI application
application = get_wsgi_application()

# Vercel serverless handler
def handler(request):
    return application(request.environ, lambda status, headers: None)
