# Full-Stack Web Application by Jose Brouwer


## Features
- User authentication via Auth0.
- Admin dashboard for managing news items and user interactions.
- Ability to like or dislike news stories.
- Pagination for news stories.
- User profile management.

## Tech Stack
- **Frontend**: HTML, CSS
- **Backend**: Python (Flask)
- **Database**: SQLite
- **Testing**: pytest, coverage
- **Version Control**: Git

## Directory Structure
project/
│
├── app.py # The main Flask application.
├── login.py # Handles user login and admin access.
├── schema.sql # Database schema.
├── stories.db # The main database.
├── testing.db # Database for testing.
│
├── templates/ # HTML templates for the application.
├── static/ # Static files like CSS and JavaScript.
├── tests/ # Unit tests for the application.
│
├── run_pytest.sh* # Script to run pytest with the correct PYTHONPATH.
├── run_fetch.sh* # Script to fetch the latest news stories.
├── fetch.log # Log file for the fetch script.
├── fetch_log.txt # Alternate log file for the fetch script.
│
├── venv/ # Python virtual environment directory.
├── .env # Environment variables for the application.
├── .gitignore # Specifies intentionally untracked files to ignore.
├── README.md # The file you are currently reading.
└── wsgi.py # Entry point for WSGI servers.