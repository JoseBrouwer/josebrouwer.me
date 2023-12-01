"""
WSGI endpoint for running the Flask web application.

This script is used to start the Flask web server and serve the application defined in 'app.py'.
It imports the Flask application instance from the 'app' module and runs it,
allowing the application to handle incoming web requests.

The script should be executed directly to start the Flask development server. 

Usage:
Run this script directly to start the Flask development server:
`python wsgi.py`

For production, use a WSGI server like Gunicorn:
`gunicorn wsgi:app`

Attributes:
- app (Flask): The Flask application instance imported from 'app.py'.

Example:
To run the server on a local machine, execute:
`python wsgi.py`
"""
from app import app

if __name__ == "__main__":
    app.run()
