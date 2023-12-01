"""
Module: test_app.py

This module contains unit tests for the Flask web application. 
It tests various aspects of the application, including database connections, 
route responses, and specific functionalities like user insertion and like/dislike counts.

Functions:
- get_db_connection: Establishes and returns a connection to the SQLite database.
- add_admin: Inserts an admin user into the database for testing purposes.
- delete_admin: Deletes an admin user from the database after testing.
- app: A pytest fixture to create and configure a new Flask app instance for each test.
- test_client: A pytest fixture to create a test client for the Flask app.
- test_admin_user: A pytest fixture to set up an admin user in the database for testing.
- test_db_connection: Tests the database connection.
- test_home_page: Tests the home page route of the Flask application.
- test_newsfeed_route: Tests the '/newsfeed' route of the application.
- user_exists: Helper function to check if a user exists in the database.
- test_insert_user_into_db: Tests the insertion of a new user into the database.
- add_story_likes_for_testing: Helper function to add likes/dislikes to a story for testing.
- test_get_likes_dislikes_db: Tests the function that retrieves like/dislike counts from the
     database.
"""

import sqlite3
import os
import json
import pytest
from app import app as flask_app
from app import get_likes_dislikes_db, insert_user_into_db


def get_db_connection():
    """
    Establishes and returns a connection to the SQLite database specified by the
    environment variable.
    """
    db_path = os.getenv("/home/jose/project", "stories.db")
    return sqlite3.connect(db_path)


def add_admin():
    """
    Inserts an admin user into the database for testing purposes.
    Checks if the admin user already exists to avoid duplicates.
    """
    conn = sqlite3.connect("/home/jose/project/stories.db")
    cursor = conn.cursor()

    # Insert an admin user into the database
    cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        ("admin@example.com",),
    )
    existing_user = cursor.fetchone()

    if not existing_user:
        cursor.execute(
            "INSERT INTO users (email, name, admin) VALUES (?, ?, ?)",
            ("admin@example.com", "Admin User", 1),
        )
    conn.commit()
    conn.close()


def delete_admin():
    """
    Deletes the admin user from the database after testing is complete.
    """
    conn = sqlite3.connect("/home/jose/project/stories.db")
    cursor = conn.cursor()

    # delete user
    cursor.execute("DELETE FROM users WHERE email = ?", ("admin@example.com",))
    conn.commit()
    conn.close()


@pytest.fixture
def app():
    """
    Pytest fixture to create and configure a new Flask app instance for each test.
    Modifies the app configuration for testing purposes.
    """
    # Modify app.config here if flask_app doesn't use TestingConfig by default
    # flask_app.config.from_object('config.TestingConfig')  # If you use a separate config file
    # Or, directly set the config
    flask_app.config["TESTING"] = True
    flask_app.config["DATABASE"] = "sqlite:///stories.db"

    yield flask_app


@pytest.fixture
def test_client(app):
    """
    Pytest fixture to create a test client for the Flask app.
    Allows for testing of Flask routes without running the server.
    """
    return app.test_client()


# Fixture to set up an admin user in the database
@pytest.fixture(scope="module")
def test_admin_user():
    """
    Pytest fixture to set up an admin user in the database for module-scope tests.
    Adds an admin user at the beginning and cleans up by deleting the user after the tests.
    """
    # add admin to db
    add_admin()

    yield "admin@example.com"  # Yield the admin email for use in tests

    # Clean up: delete the admin user
    delete_admin()


def test_db_connection():
    """
    Tests connection to the stories database
    """
    conn = sqlite3.connect("/home/jose/project/stories.db")
    # Perform test operations
    conn.close()


def test_home_page(test_client):
    """
    GIVEN a Flask application
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get("/")
    assert response.status_code == 200


def test_newsfeed_route(test_client):
    """
    GIVEN a Flask application
    WHEN the '/newsfeed' route is requested (GET)
    THEN check that the response is valid and contains the expected JSON data
    """

    # Make a GET request to the '/newsfeed' route
    response = test_client.get("/newsfeed")

    # Check that the response status code is 200 (OK)
    assert response.status_code == 200

    # Parse the JSON data from the response
    data = json.loads(response.data)

    # Validate the structure and content of the JSON response
    assert isinstance(data, list)
    assert len(data) <= 30  # Assuming it should return up to 30 items


def user_exists(email):
    """
    Checks if a user exists in the database
    For tetsing user additions to db
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return False
    return True


def test_insert_user_into_db(test_client, app):
    """
    GIVEN a Flask application
    WHEN a new user logs into the website
    THEN check that the user was added correctly
    """
    with app.app_context():
        # Mock user data
        user_data = {
            "email": "test@example.com",
            "name": "Test User",
            "nickname": "Test",
            "picture": "http://example.com/test.jpg",
        }

        # Set the session for the mock user
        with test_client.session_transaction() as sess:
            sess["user"] = {"userinfo": user_data}

        data = sess.get("user", {})
        # Call the function to test

        insert_user_into_db(data)

        email = sess.get("user", {}).get("userinfo", {}).get("email", None)
        # Assert that the user was inserted
        assert user_exists(email)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email = ?", ("test@example.com",))
        conn.commit()
        conn.close()


def add_story_likes_for_testing(conn, story_id):
    """
    Helper function to add likes/dislikes to the story_likes table for testing.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM new_stories WHERE id = ?",
        (story_id,),
    )
    existing_story = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM story_likes WHERE user_email = ? AND liked = True",
        ("admin@example.com",),
    )
    existing_like = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM story_likes WHERE user_email = ? AND disliked = True",
        ("admin2@example.com",),
    )
    existing_dislike = cursor.fetchone()

    if not existing_story:
        cursor.execute(
            "INSERT INTO new_stories (by, id, score, time, title, url) VALUES (?, ?, 0, 0, ?, ?)",
            (
                "test",
                story_id,
                "TEST_ENTRY",
                "test",
            ),
        )

    if not existing_like:
        cursor.execute(
            "INSERT INTO story_likes (story_id, user_email, liked, disliked) VALUES (?, ?, 1, 0)",
            (
                story_id,
                "admin@example.com",
            ),
        )

    if not existing_dislike:
        cursor.execute(
            "INSERT INTO story_likes (story_id, user_email, liked, disliked) VALUES (?, ?, 0, 1)",
            (
                story_id,
                "admin2@example.com",
            ),
        )

    conn.commit()


def test_get_likes_dislikes_db():
    """
    Test the get_likes_dislikes_db function to ensure it correctly counts likes and dislikes.
    """
    conn = get_db_connection()

    # Setup test data
    test_story_id = 123  # Example story ID
    expected_likes = 1
    expected_dislikes = 1
    add_story_likes_for_testing(conn, test_story_id)

    # Call the function
    likes, dislikes = get_likes_dislikes_db(test_story_id)

    # Assert that the counts are correct
    assert likes == expected_likes
    assert dislikes == expected_dislikes

    # Cleanup: remove test data from the database
    cursor = conn.cursor()
    cursor.execute("DELETE FROM story_likes WHERE story_id = ?", (test_story_id,))
    cursor.execute("DELETE FROM new_stories WHERE id = ?", (test_story_id,))
    conn.commit()
    conn.close()
