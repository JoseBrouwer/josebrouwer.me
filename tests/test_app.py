import pytest
from app import app as flask_app
from app import get_likes_dislikes_db
import sqlite3
import os
import json


def get_db_connection():
    db_path = os.getenv("/home/jose/project", "stories.db")
    return sqlite3.connect(db_path)


def add_admin():
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
    conn = sqlite3.connect("/home/jose/project/stories.db")
    cursor = conn.cursor()

    # delete user
    cursor.execute("DELETE FROM users WHERE email = ?", ("admin@example.com",))
    conn.commit()
    conn.close()


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Modify app.config here if flask_app doesn't use TestingConfig by default
    # flask_app.config.from_object('config.TestingConfig')  # If you use a separate config file
    # Or, directly set the config
    flask_app.config["TESTING"] = True
    flask_app.config["DATABASE"] = "sqlite:///stories.db"

    yield flask_app


@pytest.fixture
def test_client(app):
    """A test client for the app."""
    return app.test_client()


# Fixture to set up an admin user in the database
@pytest.fixture(scope="module")
def test_admin_user():
    # add admin to db
    add_admin()

    yield "admin@example.com"  # Yield the admin email for use in tests

    # Clean up: delete the admin user
    delete_admin()


def test_db_connection():
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
    # Optional: Insert predefined news items into the database here

    # Make a GET request to the '/newsfeed' route
    response = test_client.get('/newsfeed')

    # Check that the response status code is 200 (OK)
    assert response.status_code == 200

    # Parse the JSON data from the response
    data = json.loads(response.data)

    # Validate the structure and content of the JSON response
    assert isinstance(data, list)
    assert len(data) <= 30  # Assuming it should return up to 30 items

def user_exists(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return False
    else:
        return True

def test_insert_user_into_db(test_client, app):
    with app.app_context():
        # Mock user data
        user_data = {
            'email': 'test@example.com',
            'name': 'Test User',
            'nickname': 'Test',
            'picture': 'http://example.com/test.jpg'
        }

        # Set the session for the mock user
        with test_client.session_transaction() as sess:
            sess['user'] = {'userinfo': user_data}

        data = sess.get('user', {})
        # Call the function to test
        from app import insert_user_into_db
        insert_user_into_db(data)

        email = sess.get('user', {}).get('userinfo', {}).get('email', None)
        # Assert that the user was inserted
        assert user_exists(email)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE email = ?", ('test@example.com',))
        conn.commit()
        conn.close()

def add_story_likes_for_testing(conn, story_id, likes, dislikes):
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
        ('admin@example.com',),
    )
    existing_like = cursor.fetchone()

    cursor.execute(
        "SELECT * FROM story_likes WHERE user_email = ? AND disliked = True",
        ('admin2@example.com',),
    )
    existing_dislike = cursor.fetchone()

    if not existing_story:
        cursor.execute("INSERT INTO new_stories (by, id, score, time, title, url) VALUES (?, ?, 0, 0, ?, ?)", ('test', story_id, 'TEST_ENTRY', 'test',))
    
    if not existing_like:
        cursor.execute("INSERT INTO story_likes (story_id, user_email, liked, disliked) VALUES (?, ?, 1, 0)", (story_id, 'admin@example.com',))
    
    if not existing_dislike:
        cursor.execute("INSERT INTO story_likes (story_id, user_email, liked, disliked) VALUES (?, ?, 0, 1)", (story_id, 'admin2@example.com',))
    
    conn.commit()

def test_get_likes_dislikes_db(test_client):
    """
    Test the get_likes_dislikes_db function to ensure it correctly counts likes and dislikes.
    """
    conn = get_db_connection()

    # Setup test data
    test_story_id = 123  # Example story ID
    expected_likes = 1
    expected_dislikes = 1
    add_story_likes_for_testing(conn, test_story_id, expected_likes, expected_dislikes)

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


# def test_admin_access(test_client, test_admin_user):
#     """
#     GIVEN a Flask application and an admin user in the database
#     WHEN the '/admin' page is requested (GET)
#     THEN check that the response is valid and the admin user has access
#     """
#     with test_client:
#         # Mock the login by setting the session manually
#         with test_client.session_transaction() as sess:
#             sess["user"] = {
#                 "access_token": "eyJhbGciOiJkaXIiLCJlbmMiOiJBMjU2R0NNIiwiaXNzIjoiaHR0cHM6Ly9kZXYtd\
#                 GVyY2FvajBsa3NpNnU1di51cy5hdXRoMC5jb20vIn0..cx9brb9zed6661pl.Qf2JuRWLldVmH02puUT1_\
#                 2dALz5uEjv_qhzuryFGf_mOU4JYCXt9BN-myVZv6NyUVXEftVBrOvMGfq5OU-bZ6ZfVYYJ521LI0i8-ucF\
#                 fyHvoAaS6ckbKNGkE4i1L_9bdzHuUh_2hn6duZPB2lb3RfnxVc4ahTg-B3sjqZsu9fzPbTgJOOaIWydORE\
#                 0o83FeBGNW-omigZQr13CcDdMzqzPX-rl7rGYuQJYTD_r6W-FkC2SwQiCyCUPZx30gvDitw8v-CEcUORxU\
#                 9gJ4GJYtXU-o8Lpmrs6bHmpSwIkRIPdH1qlm7OhlvOEllUK9Um-Qmh39ezkypv5_KpAI_Acb5ukJP.Y66K\
#                 0nCgyAaEBW1VPY1j2Q",  # Mock value
#                 "expires_at": 1701536759,
#                 "expires_in": 86400,
#                 "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6InJtTE9sV1RnelZ6c0VDRXBoM\
#                 k53TCJ9.eyJuaWNrbmFtZSI6ImFkbWluIiwibmFtZSI6ImFkbWluQGV4YW1wbGUuY29tIiwicGljdHVyZS\
#                 I6Imh0dHBzOi8vcy5ncmF2YXRhci5jb20vYXZhdGFyL2U2NGM3ZDg5ZjI2YmQxOTcyZWZhODU0ZDEzZDdk\
#                 ZDYxP3M9NDgwJnI9cGcmZD1odHRwcyUzQSUyRiUyRmNkbi5hdXRoMC5jb20lMkZhdmF0YXJzJTJGYWQucG\
#                 5nIiwidXBkYXRlZF9hdCI6IjIwMjMtMTItMDFUMTc6MDU6NTkuMDg4WiIsImVtYWlsIjoiYWRtaW5AZXhh\
#                 bXBsZS5jb20iLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsImlzcyI6Imh0dHBzOi8vZGV2LXRlcmNhb2owbG\
#                 tzaTZ1NXYudXMuYXV0aDAuY29tLyIsImF1ZCI6ImZuamwxVWkzTEZwRGtCS3RPREh4TTFDQlZSVm5rU0Za\
#                 IiwiaWF0IjoxNzAxNDUwMzU5LCJleHAiOjE3MDE0ODYzNTksInN1YiI6ImF1dGgwfDY1NmEwZGY1NmE4Mj\
#                 JmN2VlODM4NDMxZSIsInNpZCI6IjBpeFFQTzg5VVhyZmNoSG1UaTJlYi1PelhQTmJYMjlzIiwibm9uY2Ui\
#                 OiJMVVEzOEJ1UU1LbTJZWGlMV3ZkYiJ9.f2BWslYGBkZcdWlI_f5T8ra8yDMQNO7N0du8fHqn94e-cOg7M\
#                 yOlkxQhk2WlYnIgfXLODeUeVcU8btTvyjhTfLqfoDE66x4K9LIvF707gnWFQOwGdXcgtvzscR7uROfYgo7\
#                 G8HMBw-NFDju4VW57eFyXyEEjnVYTSm3ySpxxuisngFBgUlgUx-atzhiZDXegA2WJsgqI7I3z61REKvziJ\
#                 ViOXLcdi8uoDQSEnOcrJe8wCRgtlkJkO2sNIc-3DLAQR6dc4t__8KXRaSRz3QROQ-MsB4wbomktL2eeMWN\
#                 HAiXS4kId_VpmA1peJ2laESPzIrqAc00kqP1B54x9RUweJA",  # Mock value
#                 "scope": "openid profile email",
#                 "token_type": "Bearer",
#                 "userinfo": {
#                     "email": "admin@example.com",
#                     "name": "admin@example.com",
#                     "nickname": "admin",
#                     "picture": "https://example.com/avatar.jpg",
#                     "sub": "auth0|656a0df56a822f7ee838431e",
#                     "updated_at": "2023-12-01T17:05:59.088Z"
#                 },
#             }

#         # Request the admin page
#         response = test_client.get("/admin")
#         assert response.status_code == 200
#         # Add more assertions here to confirm the admin page loaded correctly
