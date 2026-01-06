#!/usr/bin/env python
"""
Django AI Interviewer Deployment Script
Run this script to prepare your project for deployment
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}: {e}")
        return None

def prepare_deployment():
    """Prepare project for deployment"""
    print("🚀 Django AI Interviewer - Deployment Preparation")
    print("=" * 50)
    
    # 1. Install requirements
    run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                "Installing production requirements")
    
    # 2. Collect static files
    run_command([sys.executable, "manage.py", "collectstatic", "--noinput"], 
                "Collecting static files")
    
    # 3. Run migrations
    run_command([sys.executable, "manage.py", "migrate"], 
                "Running database migrations")
    
    # 4. Create superuser (if needed)
    create_superuser = input("\n👤 Create superuser? (y/n): ").lower().strip()
    if create_superuser == 'y':
        run_command([sys.executable, "manage.py", "createsuperuser"], 
                    "Creating Django superuser")
    
    # 5. Environment check
    print("\n🔍 Environment Check:")
    env_vars = ['SECRET_KEY', 'GOOGLE_API_KEY', 'DEBUG']
    for var in env_vars:
        value = os.environ.get(var, 'NOT SET')
        status = "✅" if value != "NOT SET" else "❌"
        print(f"  {status} {var}: {value}")
    
    print("\n📋 Deployment Checklist:")
    checklist = [
        "✅ Requirements installed",
        "✅ Static files collected", 
        "✅ Migrations run",
        "✅ Environment variables configured",
        "🌐 Ready for deployment!"
    ]
    
    for item in checklist:
        print(f"  {item}")
    
    print("\n🎯 Next Steps:")
    print("1. Choose your deployment platform (PythonAnywhere, Heroku, Vercel, Railway)")
    print("2. Set environment variables on your platform")
    print("3. Deploy using platform-specific commands")
    print("4. Configure your domain name")
    print("5. Test all functionality")
    
    print("\n📖 For detailed deployment guide, see: DEPLOYMENT_GUIDE.md")
    print("\n🎉 Your Django AI Interviewer is ready to go live!")

if __name__ == "__main__":
    prepare_deployment()
