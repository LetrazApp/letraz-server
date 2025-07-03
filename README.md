# Letraz Server

![Letraz Banner](https://i.imgur.com/pLMcA9a.png)

## Overview

Letraz Server is the backend API service that powers Letraz, an AI-powered platform that helps job seekers create tailored resumes for every job application effortlessly. The server provides robust APIs for user management, job posting analysis, resume creation and optimization, ensuring seamless integration with the frontend client.

This repository contains the server-side implementation of the Letraz application, built with Django, Django REST Framework, and PostgreSQL, featuring comprehensive user authentication, resume management, and job analysis capabilities.

## Core Features

* **User Profile Management**: Complete user profile system with personal information, contact details, and preferences
* **Resume Builder**: Advanced resume creation and management with sections for education, experience, skills, projects, and certifications
* **Job Analysis**: Job posting parsing and requirement extraction for tailored resume optimization
* **Waitlist Management**: Early access signup system with automated positioning
* **Skills Database**: Comprehensive skills catalog with categorization and proficiency levels
* **API Documentation**: Auto-generated OpenAPI documentation with interactive testing interface
* **Authentication**: Secure user authentication via Clerk integration
* **Data Validation**: Robust input validation and error handling

## Tech Stack

* **Django 5.1** - High-level Python web framework
* **Django REST Framework** - Powerful toolkit for building Web APIs
* **PostgreSQL** - Advanced open-source relational database (with SQLite fallback)
* **Clerk** - Authentication and user management platform
* **uv** - Fast Python package manager
* **Gunicorn** - Python WSGI HTTP Server for production
* **drf-spectacular** - OpenAPI 3.0 schema generation for DRF
* **Sentry** - Application monitoring and error tracking
* **Docker** - Containerized deployment support

## Getting Started

### Prerequisites

* Python 3.12 or later
* uv package manager
* PostgreSQL (optional - SQLite used as fallback)
* Docker (optional, for containerized deployment)

### Installation

1. **Install uv package manager**
   See [uv's official documentation](https://docs.astral.sh/uv/) for installation instructions.

2. **Clone the repository**
   ```bash
   git clone https://github.com/LetrazApp/letraz-server.git
   cd letraz-server
   ```

3. **Set up environment variables**
   Create a `.env` file and add the provided environment variables. If you are not part of the core team, check the `.env.example` file and obtain the environment variables from your side.
   
   Key environment variables:
   - `SECRET` - Django secret key
   - `ENV` - Environment (DEV/PROD)
   - `ALLOWED_HOSTS` - Semicolon-separated list of allowed hosts
   - `CLERK_SECRET_KEY` - Clerk authentication secret key
   - `CLERK_FRONTEND_API_URL` - Clerk frontend API URL
   - Database configuration (ENGINE, NAME, USER, PASSWORD, HOST, PORT)
   - `SENTRY_DSN` - Sentry error tracking DSN (optional)

4. **Create virtual environment**
   ```bash
   uv venv
   ```

5. **Activate the virtual environment**
   ```bash
   # Unix/MacOS
   source .venv/bin/activate
   
   # Windows
   .venv\Scripts\activate
   ```

6. **Install dependencies**
   ```bash
   uv sync
   ```

7. **Set up the database**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

8. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to create a local admin user.

9. **Run the development server**
   ```bash
   python manage.py runserver
   ```

10. **Access the application**
    - API Base: `http://localhost:8000` (you should see a 404 page as nothing is mounted on the `/` route by design)
    - Admin Panel: `http://localhost:8000/admin/` (login with superuser credentials to see and edit data in the DB)
    - API Documentation: `http://localhost:8000/api/v1/schema/swagger-ui/`

## Development Workflow

* **Development Server**: `uv run python manage.py runserver`
* **Database Migrations**: `uv run python manage.py makemigrations && uv run python manage.py migrate`
* **Collect Static Files**: `uv run python manage.py collectstatic`
* **Run Tests**: `uv run python manage.py test`
* **Shell Access**: `uv run python manage.py shell`
* **Docker Build**: `sudo docker build -t letraz-server:Django .`
* **Docker Run**: `sudo docker run --env-file .env --name letraz-server -p 8000:8000 -d letraz-server:Django`

## Project Structure

* `letraz_server/` - Main Django project configuration
  * `settings.py` - Django settings and configuration
  * `urls.py` - URL routing configuration
  * `contrib/` - Custom utilities, middlewares, and SDKs
* `CORE/` - Core application (waitlist, skills, countries)
* `PROFILE/` - User profile management
* `JOB/` - Job posting and analysis management
* `RESUME/` - Resume creation and management system
* `static/` - Static files (CSS, images)
* `media/` - User-uploaded media files
* `logs/` - Application logs
* `manage.py` - Django management script

## API Endpoints

The API is organized into the following main sections:

* **Core APIs** (`/api/v1/`) - Waitlist management, skills, countries
* **User APIs** (`/api/v1/user/`) - User profile management
* **Job APIs** (`/api/v1/job/`) - Job posting management
* **Resume APIs** (`/api/v1/resume/`) - Resume creation and management

### Authentication

All API endpoints (except public endpoints like waitlist signup) require authentication via Clerk. Include the authorization header in your requests:

```
Authorization: Bearer <your-clerk-token>
```

### API Documentation

Interactive API documentation is available at `/api/v1/schema/swagger-ui/` when running the development server.

## Environment Configuration

The application supports multiple environment configurations:

* **Development**: SQLite database, debug mode enabled
* **Production**: PostgreSQL database, debug mode disabled, additional security settings

Key environment variables:
- `ENV` - Set to "DEV" for development, "PROD" for production
- Database settings for PostgreSQL connection
- Clerk configuration for authentication
- CORS and CSRF settings for frontend integration

## Contributing

We are not currently accepting public contributions to this repository. However, if you're interested in joining our core development team, please reach out to us through our official channels.

## License

This project is licensed under the terms specified in the LICENSE file.

## Links

* [Frontend Repository](https://github.com/pingSubhajit/letraz) - Next.js client application  
* [Production API](https://api.letraz.app/api/v1/) - Live API endpoint
* [Website](https://letraz.app) - Official Letraz website
* [API Documentation](https://api.letraz.app/api/v1/schema/swagger-ui/) - Interactive API docs

