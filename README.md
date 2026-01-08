# Interview Management Project

*Demo (Link):* https://drive.google.com/file/d/1EMaKRDTNWxauGB0uLGBODeF33P6EJbKe/view?usp=sharing

# Interview Management Project

AI-powered platform for managing technical interviews, built with Django.

## Features

- **Role-based access:** HR and Candidate user flows
- **HR Dashboard:** Create, edit, and manage interviews
- **AI Question Generation:** Unique technical questions per interview using Google Gemini
- **Timed Interview Sessions:** Candidates answer questions with a countdown timer
- **AI Evaluation:** Automated scoring and feedback for each answer
- **Results Dashboard:** HR can review, aggregate, and delete results
- **Resume Upload:** Candidates can upload resumes during registration
- **Modern UI:** Responsive Bootstrap 5 interface

## Tech Stack

- Django 4.2
- Google Generative AI (Gemini)
- Bootstrap 5
- SQLite (default, easy local setup)
- Gunicorn & Whitenoise (for production)
- Vercel/Heroku/Railway compatible

## Quick Start

1. **Clone the repo:**
   ```sh
   git clone <your-repo-url>
   cd interview-management
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   - `GOOGLE_API_KEY` (required for AI features)
   - `SECRET_KEY`, `DEBUG`, etc.

4. **Run migrations:**
   ```sh
   python config/manage.py migrate
   ```

5. **Start the server:**
   ```sh
   python config/manage.py runserver
   ```

6. **Access the app:**
   - HR: Register as HR, create interviews, view results
   - Candidate: Register as Candidate, upload resume, take interviews

## File Structure

- `config/` – Django project settings and core config
- `accounts/` – User registration, login, profile, and roles
- `interviews/` – Interview models, AI logic, forms, and views
- `api/` – Vercel serverless entrypoint
- `media/` – Uploaded resumes and files

## Environment Variables

- `GOOGLE_API_KEY` – Google Gemini API key (required)
- `SECRET_KEY` – Django secret key
- `DEBUG` – Set to `False` in production
- See `config/settings_production.py` for more


---

*For more details, see the code.*
