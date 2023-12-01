"""
A Flask-based web application for news management and user interaction.

This application serves as a platform for users to view, like, and dislike news stories. 
It uses a SQLite database to store news items and user interactions (likes/dislikes). 
The application integrates with Auth0 for user authentication and authorization,
allowing for different levels of access, with special privileges for admin users. 
Admin users can manage news items, user accounts, and user-generated likes/dislikes.

Key Features:
- User authentication and profile management via Auth0.
- Admin-specific functionalities to manage news items and user accounts.
- Display of news items with options for users to like or dislike.
- Pagination for efficient navigation through news items.
- Secure handling of user sessions and database interactions.

Routes:
- Home, Login, and Logout routes for user authentication and session management.
- Profile, Admin, and Newsfeed routes for user-specific and admin-specific interactions.
- API endpoints for liking/disliking news stories, managing user accounts, and managing news items.

The application uses Flask as its web framework, SQLite for database operations, and OAuth for
authentication.
"""


import json
import sqlite3
from urllib.parse import quote_plus, urlencode
from os import environ as env
import math

# import requests
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
from login import login_required, admin_required

class TestingConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///testing.db'

ITEMS_PER_PAGE = 10

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__, template_folder="templates")
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


@app.route("/login")
def login():
    """
    Initiates the login process using Auth0.

    Redirects the user to the Auth0 login page. Upon successful authentication,
    the user is redirected back to the application's callback endpoint.
    """
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )


@app.route("/new_user")
def prompt():
    """
    Displays a prompt for new users.

    Renders a template to inform users about the login process.
    Returns a rendered HTML page.
    """
    return render_template("no_login.html")


@app.route("/callback", methods=["GET", "POST"])
def callback():
    """
    Handles the callback from Auth0 after user authentication.

    Retrieves the user's access token and stores it in the session.
    Inserts new user information into the database.
    Redirects the user to the home page after successful login.
    """
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    data = session.get("user")

    insert_user_into_db(data)  # insert to db

    return redirect("/")


def insert_user_into_db(data):
    """
    Inserts new user information into the database.

    Checks if the user already exists in the database to avoid duplicates.
    Extracts user information from the session and inserts it into the 'users' table.
    Commits changes to the database and closes the connection.
    """
    #data = session.get("user")
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    # Check if the user already exists in the table
    cursor.execute(
        "SELECT * FROM users WHERE email = ?",
        (data.get("userinfo", {}).get("email"),),
    )
    existing_user = cursor.fetchone()

    if not existing_user:
        # Insert the user into the "users" table
        cursor.execute(
            """
            INSERT INTO users (email, name, nickname, picture)
            VALUES (?, ?, ?, ?)
            """,
            (
                data.get("userinfo", {}).get("email", ""),
                data.get("userinfo", {}).get("name", ""),
                data.get("userinfo", {}).get("nickname", ""),
                data.get("userinfo", {}).get("picture", ""),
            ),
        )

    connection.commit()
    connection.close()


@app.route("/logout")
def logout():
    """
    Logs the user out and clears the session.

    Redirects the user to the Auth0 logout URL, ensuring the user is logged out from Auth0 as well.
    Returns a redirect response to the home page.
    """
    session.clear()
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@app.route("/")
def home():
    """
    Renders the home page of the application.

    Displays a welcome message and user session details if logged in.
    Returns a rendered HTML template for the home page.
    """
    return render_template(
        "index.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@app.route("/profile")
@login_required
def profile():
    """
    Renders the profile page for the logged-in user.

    Retrieves and displays the user's liked stories from the database.
    Converts database results into a list of dictionaries for easy rendering.
    Returns a rendered HTML template for the user's profile page.
    """
    user_info = session.get("user", {}).get("userinfo", {})
    user_email = user_info.get("email")

    # Connect to the database.
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    # Retrieve liked stories by the user
    cursor.execute("SELECT * FROM story_likes WHERE user_email = ?", (user_email,))
    liked_stories = cursor.fetchall()

    # Convert the results to a list of dictionaries.
    liked_feed = []
    for item in liked_stories:
        liked_feed.append(
            {
                "by": item[4],
                "descendants": item[9],
                "id": item[0],
                "score": item[5],
                "text": item[11],
                "time": item[6],
                "title": item[7],
                "type": item[10],
                "url": item[8],
                "liked": item[2],
                "disliked": item[3],
            }
        )

    # Close the database connection.
    connection.close()

    # Render the profile template with the liked stories
    return render_template("profile.html", user_info=user_info, liked_feed=liked_feed)


@app.route("/admin")
@login_required
@admin_required
def admin():
    """
    Renders the admin dashboard page.

    Only accessible by users with admin privileges.
    Returns a rendered HTML template for the admin dashboard.
    """
    return render_template("admin.html")


@app.route("/admin/items")
@login_required
@admin_required
def admin_items():
    """
    Fetches and renders liked/disliked stories for admin view.

    Retrieves all stories with likes/dislikes from the database.
    Converts the results into a list of dictionaries for rendering.
    Returns a rendered HTML template for the admin items management page.
    """
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()
    # Fetch all liked/disliked stories for admin view
    cursor.execute("SELECT * FROM story_likes")
    stories = cursor.fetchall()

    # Convert the results to a list of dictionaries.
    stories_feed = []
    for item in stories:
        stories_feed.append(
            {
                "by": item[4],
                "descendants": item[9],
                "id": item[0],
                "score": item[5],
                "text": item[11],
                "time": item[6],
                "title": item[7],
                "type": item[10],
                "url": item[8],
                "liked": item[2],
                "disliked": item[3],
                "user_email": item[1],
            }
        )

    # Close the database connection.
    connection.close()

    # Render the admin template with the stories feed
    return render_template("admin_items.html", stories_feed=stories_feed)


@app.route("/admin/users")
@login_required
@admin_required
def admin_users():
    """
    Renders the admin page for user management.

    Fetches all users from the database and presents them in a list.
    Returns a rendered HTML template for managing users from the admin perspective.
    """
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()
    # Fetch all users from the database
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    user_list = []
    for user in users:
        user_list.append({"email": user[1], "name": user[2]})
    connection.close()

    return render_template("admin_users.html", users=user_list)


@app.route("/admin/news", methods=["GET"])
@login_required
@admin_required
def admin_news():
    """
    Renders the admin page for news item management.

    Implements pagination to manage and display news items effectively.
    Fetches news items from the database based on the current page.
    Returns a rendered HTML template for managing news items.
    """
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    page = request.args.get("page", 1, type=int)
    start_index = (page - 1) * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE

    # Fetch news items for the current page
    cursor.execute("SELECT * FROM new_stories")
    results = cursor.fetchall()

    news_feed = []
    for item in results[start_index:end_index]:
        item_id = item[1]
        like_count, dislike_count = get_likes_dislikes_db(item_id)
        news_feed.append(
            {
                "by": item[0],
                "descendants": item[6],
                "id": item[1],
                "score": item[2],
                "text": item[8],
                "time": item[3],
                "title": item[4],
                "type": item[7],
                "url": item[5],
                "like_count": like_count,
                "dislike_count": dislike_count,
            }
        )

    total_pages = math.ceil(len(results) / ITEMS_PER_PAGE)

    connection.close()
    return render_template(
        "admin_news.html",
        news_feed=news_feed,
        current_page=page,
        total_pages=total_pages,
    )


@app.route("/newsfeed", methods=["GET", "POST"])
def news():
    """
    Retrieves the most recent news items from the database and returns them as JSON.

    Connects to the database and fetches the latest 30 news items.
    Converts the database results into a list of dictionaries.
    Closes the database connection.
    Returns the news feed as a JSON string.
    """
    # Connect to the database.
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    # Retrieve the 30 most recent items from the database.
    cursor.execute("SELECT * FROM new_stories")
    results = cursor.fetchall()

    # Convert the results to a list of dictionaries.
    news_feed = []
    for item in results[:30]:
        news_feed.append(
            {
                "by": item[0],
                "descendants": item[6],
                "id": item[1],
                #'kids': item[3],
                "score": item[2],
                "text": item[8],
                "time": item[3],
                "title": item[4],
                "type": item[7],
                "url": item[5],
            }
        )

    # Close the database connection.
    connection.close()

    # Return the news feed as JSON.
    json_news = json.dumps(news_feed, indent=4)
    return json_news
    # return jsonify(news_feed)


@app.route("/news", methods=["GET", "POST"])
@login_required
def display():
    """
    Renders the news page with pagination.

    Retrieves news items from the database based on the current page number.
    Implements pagination to manage the display of news items.
    Converts the results into a list of dictionaries for rendering.
    Calculates the total number of pages needed for pagination.
    Returns a rendered HTML template for the news page with pagination.
    """
    page = request.args.get("page", 1, type=int)

    # Connect to the database.
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    # Calculate the start and end indices for the current page
    if page < 0:
        start_index = 0
        end_index = 10
    else:
        start_index = (page - 1) * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE

    # Retrieve the 30 most recent items from the database.
    cursor.execute("SELECT * FROM new_stories")
    results = cursor.fetchall()

    # Convert the results to a list of dictionaries.
    news_feed = []
    for item in results[start_index:end_index]:
        item_id = item[1]
        like_count, dislike_count = get_likes_dislikes_db(item_id)
        news_feed.append(
            {
                "by": item[0],
                "descendants": item[6],
                "id": item[1],
                "score": item[2],
                "text": item[8],
                "time": item[3],
                "title": item[4],
                "type": item[7],
                "url": item[5],
                "like_count": like_count,
                "dislike_count": dislike_count,
            }
        )

    # Close the database connection.
    connection.close()

    # calculate the number of pages needed
    total_pages = math.ceil(len(results) / ITEMS_PER_PAGE)

    # Render the news template with the news feed.
    return render_template(
        "news.html", news_feed=news_feed, current_page=page, total_pages=total_pages
    )


@app.route("/like_story", methods=["POST"])
@login_required
def like_story():
    """
    Handles the 'like' action for a news story.

    Receives the story ID from the request and checks if the user has already liked or disliked it.
    Updates or inserts a new record in the 'story_likes' table with 'liked' status.
    Returns a JSON response indicating the success of the operation and updated like/dislike counts.
    """
    user_email = session.get("user", {}).get("userinfo", {}).get("email")
    story_id = request.json.get("story_id")

    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    # Check if the user has already liked or disliked this story
    cursor.execute("SELECT * FROM new_stories WHERE id = ?", (story_id,))
    story_record = cursor.fetchone()

    if story_record:
        story_data = {
            "by": story_record[0],
            "id": story_record[1],
            "score": story_record[2],
            "time": story_record[3],
            "title": story_record[4],
            "url": story_record[5],
            "descendants": story_record[6],
            "type": story_record[7],
            "text": story_record[8],
        }

        # Check if there's already an entry for this story and user
        cursor.execute(
            "SELECT liked, disliked FROM story_likes WHERE story_id = ? AND user_email = ?",
            (story_id, user_email),
        )
        record = cursor.fetchone()

        if record:
            # Update the like/dislike status and story information for the existing record
            cursor.execute(
                """
                UPDATE story_likes
                SET liked = ?, 
                    disliked = ?, 
                    by = ?, 
                    score = ?, 
                    time = ?, 
                    title = ?, 
                    url = ?, 
                    descendants = ?, 
                    type = ?, 
                    text = ?
                WHERE story_id = ? AND user_email = ?
            """,
                (
                    True,
                    False,
                    story_data["by"],
                    story_data["score"],
                    story_data["time"],
                    story_data["title"],
                    story_data["url"],
                    story_data["descendants"],
                    story_data["type"],
                    story_data["text"],
                    story_id,
                    user_email,
                ),
            )
        else:
            # Insert a new record with the like/dislike status and story information
            cursor.execute(
                """
                INSERT INTO story_likes (story_id, 
                                         user_email, 
                                         liked, 
                                         disliked, 
                                         by, 
                                         score, 
                                         time, 
                                         title, 
                                         url, 
                                         descendants, 
                                         type, 
                                         text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    story_id,
                    user_email,
                    True,
                    False,
                    story_data["by"],
                    story_data["score"],
                    story_data["time"],
                    story_data["title"],
                    story_data["url"],
                    story_data["descendants"],
                    story_data["type"],
                    story_data["text"],
                ),
            )

        # Commit changes and close connection
        connection.commit()
        connection.close()
    else:
        connection.close()
        return jsonify({"status": "error", "message": "Story not found"}), 404

    like_count, dislike_count = get_likes_dislikes_db(story_id)

    return jsonify(
        {"status": "success", "like_count": like_count, "dislike_count": dislike_count}
    )


@app.route("/dislike_story", methods=["POST"])
@login_required
def dislike_story():
    """
    Handles the 'dislike' action for a news story.

    Receives the story ID from the request and checks if the user has already liked or disliked it.
    Updates or inserts a new record in the 'story_likes' table with 'disliked' status.
    Returns a JSON response indicating the success of the operation and updated like/dislike counts.
    """
    user_email = session.get("user", {}).get("userinfo", {}).get("email")
    story_id = request.json.get("story_id")

    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    # Check if the user has already liked or disliked this story
    cursor.execute("SELECT * FROM new_stories WHERE id = ?", (story_id,))
    story_record = cursor.fetchone()

    if story_record:
        story_data = {
            "by": story_record[0],
            "id": story_record[1],
            "score": story_record[2],
            "time": story_record[3],
            "title": story_record[4],
            "url": story_record[5],
            "descendants": story_record[6],
            "type": story_record[7],
            "text": story_record[8],
        }

        # Check if there's already an entry for this story and user
        cursor.execute(
            "SELECT liked, disliked FROM story_likes WHERE story_id = ? AND user_email = ?",
            (story_id, user_email),
        )
        record = cursor.fetchone()

        if record:
            # Update the like/dislike status and story information for the existing record
            cursor.execute(
                """
                UPDATE story_likes
                SET liked = ?, 
                    disliked = ?, 
                    by = ?, 
                    score = ?, 
                    time = ?, 
                    title = ?, 
                    url = ?, 
                    descendants = ?, 
                    type = ?, 
                    text = ?
                WHERE story_id = ? AND user_email = ?
            """,
                (
                    False,
                    True,
                    story_data["by"],
                    story_data["score"],
                    story_data["time"],
                    story_data["title"],
                    story_data["url"],
                    story_data["descendants"],
                    story_data["type"],
                    story_data["text"],
                    story_id,
                    user_email,
                ),
            )
        else:
            # Insert a new record with the like/dislike status and story information
            cursor.execute(
                """
                INSERT INTO story_likes (story_id, 
                                         user_email, 
                                         liked, 
                                         disliked, 
                                         by, 
                                         score, 
                                         time, 
                                         title, 
                                         url, 
                                         descendants, 
                                         type, 
                                         text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    story_id,
                    user_email,
                    False,
                    True,
                    story_data["by"],
                    story_data["score"],
                    story_data["time"],
                    story_data["title"],
                    story_data["url"],
                    story_data["descendants"],
                    story_data["type"],
                    story_data["text"],
                ),
            )

        # Commit changes and close connection
        connection.commit()
        connection.close()
    else:
        connection.close()
        return jsonify({"status": "error", "message": "Story not found"}), 404

    like_count, dislike_count = get_likes_dislikes_db(story_id)

    return jsonify(
        {"status": "success", "like_count": like_count, "dislike_count": dislike_count}
    )


def get_likes_dislikes_db(story_id):
    """
    Retrieves the counts of likes and dislikes for a given story from the database.

    Connects to the database and executes queries to count likes and dislikes 
    for the specified story ID.
    Closes the database connection after retrieving the counts.
    Returns the counts of likes and dislikes as a tuple.
    """
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    # Get the count of likes
    cursor.execute(
        "SELECT COUNT(*) FROM story_likes WHERE story_id = ? AND liked = True",
        (story_id,),
    )
    likes_count = cursor.fetchone()[0]

    # Get the count of dislikes
    cursor.execute(
        "SELECT COUNT(*) FROM story_likes WHERE story_id = ? AND disliked = True",
        (story_id,),
    )
    dislikes_count = cursor.fetchone()[0]

    connection.close()

    return likes_count, dislikes_count


@app.route("/delete", methods=["POST"])
@login_required
def delete_like_dislike():
    """
    Deletes a like or dislike entry from the database.

    Based on the provided story ID and user email, it removes the corresponding like/dislike.
    Ensures that the operation is performed by the correct user.
    Returns a JSON response indicating the success or failure of the operation.
    """
    data = request.json
    story_id = data.get("story_id")
    user_email = session.get("user", {}).get("userinfo", {}).get("email")

    # Connect to the database
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    # Check if the user is an admin
    cursor.execute("SELECT admin FROM users WHERE email = ?", (user_email,))
    user_admin = cursor.fetchone()[0]

    if user_admin:
        # If user is an admin, delete any entry with the story_id
        cursor.execute("DELETE FROM story_likes WHERE story_id = ?", (story_id,))
    else:
        # If user is not an admin, delete only their own like/dislike entry
        cursor.execute(
            "DELETE FROM story_likes WHERE story_id = ? AND user_email = ?",
            (story_id, user_email),
        )

    connection.commit()
    connection.close()

    return jsonify({"status": "success"})


@app.route("/delete_user", methods=["POST"])
@login_required
@admin_required
def delete_user():
    """
    Deletes a user and their associated likes/dislikes from the database.

    Only accessible by admin users.
    Removes user data and associated interactions from the database.
    Returns a JSON response indicating the success or failure of the operation.
    """
    data = request.json
    user_email = data.get("email")

    # Connect to the database
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    # Delete the user's likes/dislikes
    cursor.execute("DELETE FROM story_likes WHERE user_email = ?", (user_email,))

    # Delete the user
    cursor.execute("DELETE FROM users WHERE email = ?", (user_email,))

    connection.commit()
    connection.close()

    return jsonify({"status": "success"})


@app.route("/delete_news_item", methods=["POST"])
@login_required
@admin_required
def delete_news_item():
    """
    Deletes a news item and its associated likes/dislikes from the database.

    Accessible only by admin users.
    Removes the specified news item and its interactions from the database.
    Returns a JSON response indicating the success or failure of the deletion.
    """
    data = request.json
    news_id = data.get("news_id")

    # Connect to the database
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    # Delete the news item's likes/dislikes
    cursor.execute("DELETE FROM story_likes WHERE story_id = ?", (news_id,))

    # Delete the news item
    cursor.execute("DELETE FROM new_stories WHERE id = ?", (news_id,))

    connection.commit()
    connection.close()

    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000), debug=True)
