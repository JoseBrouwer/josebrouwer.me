import pytest
from app import app as flask_app
import sqlite3
import os

def get_db_connection():
    db_path = os.getenv('/home/jose/project', 'testing.db')
    return sqlite3.connect(db_path)

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Modify app.config here if flask_app doesn't use TestingConfig by default
    #flask_app.config.from_object('config.TestingConfig')  # If you use a separate config file
    # Or, directly set the config
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///testing.db'
    
    yield flask_app

@pytest.fixture
def test_client(app):
    """A test client for the app."""
    return app.test_client()

# Fixture to set up an admin user in the database
@pytest.fixture(scope='module')
def test_admin_user():
    conn = sqlite3.connect('path/to/testing.db')
    cursor = conn.cursor()

    # Insert an admin user into the database
    cursor.execute("INSERT INTO users (email, name, admin) VALUES (?, ?, ?)", 
                   ("admin@example.com", "Admin User", True))
    conn.commit()

    yield "admin@example.com"  # Yield the admin email for use in tests

    # Clean up: delete the admin user
    cursor.execute("DELETE FROM users WHERE email = ?", ("admin@example.com",))
    conn.commit()
    conn.close()


def test_home_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get('/')
    assert response.status_code == 200

def test_admin_access(test_client, test_admin_user):
    """
    GIVEN a Flask application and an admin user in the database
    WHEN the '/admin' page is requested (GET)
    THEN check that the response is valid and the admin user has access
    """
    # Log in as the admin user (you might need to adjust this part based on your login mechanism)
    test_client.post('/login', data=dict(email=test_admin_user, password='password'), follow_redirects=True)
    
    # Request the admin page
    response = test_client.get('/admin')
    assert response.status_code == 200
    assert b"Admin Dashboard" in response.data

def test_some_db_function():
    conn = get_db_connection()
    # Perform test operations
    conn.close()

