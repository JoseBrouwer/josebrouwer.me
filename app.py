# 📁 server.py -----

import json
import requests
import sqlite3
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
from login import login_required
import math
#import logging

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
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/new_user")
def prompt():
    return render_template("no_login.html")

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    data = session.get('user')

    insert_user_into_db(data) #insert to db

    return redirect("/")

def insert_user_into_db(session):
    """
    This functions inputs new users into the db
    Params: session is the dictionary returned by Auth0
    Returns: None, commits to db
    """
    connection = sqlite3.connect('stories.db')
    cursor = connection.cursor()

    #Check if the user already exists in the table
    cursor.execute('SELECT * FROM users WHERE email = ?', (session.get('userinfo', {}).get('email'),))
    existing_user = cursor.fetchone()

    if not existing_user:
        # Insert the user into the "users" table
        cursor.execute(
            '''
            INSERT INTO users (email, name, nickname, picture)
            VALUES (?, ?, ?, ?)
            ''',
            (
                session.get('userinfo', {}).get('email', ''),
                session.get('userinfo', {}).get('name', ''),
                session.get('userinfo', {}).get('nickname', ''),
                session.get('userinfo', {}).get('picture', ''),
            )
        )

    connection.commit()
    connection.close()

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
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
    return render_template("index.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

@app.route("/profile")
@login_required
def profile():

    user_info = session.get('user', {}).get('userinfo', {})
    user_email = user_info.get('email')

    # Connect to the database.
    connection = sqlite3.connect('stories.db')
    cursor = connection.cursor()

    # Retrieve liked stories by the user
    cursor.execute('SELECT * FROM story_likes WHERE user_email = ?', (user_email,))
    liked_stories = cursor.fetchall()

    # Convert the results to a list of dictionaries.
    liked_feed = []
    for item in liked_stories:
        liked_feed.append({
            'by': item[4],
            'descendants': item[9],
            'id': item[0],
            'score': item[5],
            'text': item[11],
            'time': item[6],
            'title': item[7],
            'type': item[10],
            'url': item[8],
            'liked': item[2],  
            'disliked': item[3]  
        })

    # Close the database connection.
    connection.close()

    # Render the profile template with the liked stories
    return render_template("profile.html", user_info=user_info, liked_feed=liked_feed)

@app.route("/newsfeed", methods=["GET", "POST"])
def news():
    # Connect to the database.
    connection = sqlite3.connect('stories.db')
    cursor = connection.cursor()

    # Retrieve the 30 most recent items from the database.
    cursor.execute('SELECT * FROM new_stories')
    results = cursor.fetchall()

    # Convert the results to a list of dictionaries.
    news_feed = []
    for item in results[:30]:
        news_feed.append({
            'by': item[0],
            'descendants': item[6],
            'id': item[1],
            #'kids': item[3],
            'score': item[2],
            'text': item[8],
            'time': item[3],
            'title': item[4],
            'type': item[7], 
            'url': item[5]
        })

    # Close the database connection.
    connection.close()

    # Return the news feed as JSON.
    json_news = json.dumps(news_feed, indent=4)
    return json_news
    #return jsonify(news_feed)

@app.route("/news", methods=["GET", "POST"])
@login_required
def display():

    page = request.args.get('page', 1, type=int)

    # Connect to the database.
    connection = sqlite3.connect('stories.db')
    cursor = connection.cursor()

    # Calculate the start and end indices for the current page
    if page < 0: 
        start_index =0
        end_index = 10
    else:
        start_index = (page - 1) * ITEMS_PER_PAGE
        end_index = start_index + ITEMS_PER_PAGE

    # Retrieve the 30 most recent items from the database.
    cursor.execute('SELECT * FROM new_stories')
    results = cursor.fetchall()

    # Convert the results to a list of dictionaries.
    news_feed = []
    for item in results[start_index:end_index]:
        item_id = item[1]
        like_count, dislike_count = get_likes_dislikes_db(item_id)
        news_feed.append({
            'by': item[0],
            'descendants': item[6],
            'id': item[1],
            'score': item[2],
            'text': item[8],
            'time': item[3],
            'title': item[4],
            'type': item[7],
            'url': item[5],
            'like_count': like_count,
            'dislike_count': dislike_count
        })

    # Close the database connection.
    connection.close()

    #calculate the number of pages needed
    total_pages = math.ceil(len(results) / ITEMS_PER_PAGE)

    # Render the news template with the news feed.
    return render_template("news.html", news_feed=news_feed, current_page=page, total_pages=total_pages)

@app.route("/like_story", methods=["POST"])
@login_required
def like_story():
    user_email = session.get('user', {}).get('userinfo', {}).get('email')
    story_id = request.json.get('story_id')
    
    connection = sqlite3.connect('stories.db')
    cursor = connection.cursor()
    
    # Check if the user has already liked or disliked this story
    cursor.execute('SELECT * FROM new_stories WHERE id = ?', (story_id,))
    story_record = cursor.fetchone()

    if story_record:
        story_data = {
            'by': story_record[0],
            'id': story_record[1],
            'score': story_record[2],
            'time': story_record[3],
            'title': story_record[4],
            'url': story_record[5],
            'descendants': story_record[6],
            'type': story_record[7],
            'text': story_record[8]
        }

        # Check if there's already an entry for this story and user
        cursor.execute('SELECT liked, disliked FROM story_likes WHERE story_id = ? AND user_email = ?', (story_id, user_email))
        record = cursor.fetchone()

        if record:
            # Update the like/dislike status and story information for the existing record
            cursor.execute('''
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
            ''', (True, 
                  False, 
                  story_data['by'], 
                  story_data['score'], 
                  story_data['time'], 
                  story_data['title'], 
                  story_data['url'], 
                  story_data['descendants'], 
                  story_data['type'], 
                  story_data['text'], 
                  story_id, 
                  user_email))
        else:
            # Insert a new record with the like/dislike status and story information
            cursor.execute('''
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
            ''', (story_id, 
                  user_email, 
                  True, 
                  False, 
                  story_data['by'], 
                  story_data['score'], 
                  story_data['time'], 
                  story_data['title'], 
                  story_data['url'], 
                  story_data['descendants'], 
                  story_data['type'], 
                  story_data['text']))

        # Commit changes and close connection
        connection.commit()
        connection.close()
    else:
        connection.close()
        return jsonify({'status': 'error', 'message': 'Story not found'}), 404

    like_count, dislike_count = get_likes_dislikes_db(story_id)

    return jsonify({'status': 'success', 'like_count': like_count, 'dislike_count': dislike_count})

@app.route("/dislike_story", methods=["POST"])
@login_required
def dislike_story():
    user_email = session.get('user', {}).get('userinfo', {}).get('email')
    story_id = request.json.get('story_id')
    
    connection = sqlite3.connect('stories.db')
    cursor = connection.cursor()
    
    # Check if the user has already liked or disliked this story
    cursor.execute('SELECT * FROM new_stories WHERE id = ?', (story_id,))
    story_record = cursor.fetchone()

    if story_record:
        story_data = {
            'by': story_record[0],
            'id': story_record[1],
            'score': story_record[2],
            'time': story_record[3],
            'title': story_record[4],
            'url': story_record[5],
            'descendants': story_record[6],
            'type': story_record[7],
            'text': story_record[8]
        }

        # Check if there's already an entry for this story and user
        cursor.execute('SELECT liked, disliked FROM story_likes WHERE story_id = ? AND user_email = ?', (story_id, user_email))
        record = cursor.fetchone()

        if record:
            # Update the like/dislike status and story information for the existing record
            cursor.execute('''
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
            ''', (False, 
                  True, 
                  story_data['by'], 
                  story_data['score'], 
                  story_data['time'], 
                  story_data['title'], 
                  story_data['url'], 
                  story_data['descendants'], 
                  story_data['type'], 
                  story_data['text'], 
                  story_id, 
                  user_email))
        else:
            # Insert a new record with the like/dislike status and story information
            cursor.execute('''
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
            ''', (story_id, 
                  user_email, 
                  False, 
                  True, 
                  story_data['by'], 
                  story_data['score'], 
                  story_data['time'], 
                  story_data['title'], 
                  story_data['url'], 
                  story_data['descendants'], 
                  story_data['type'], 
                  story_data['text']))

        # Commit changes and close connection
        connection.commit()
        connection.close()
    else:
        connection.close()
        return jsonify({'status': 'error', 'message': 'Story not found'}), 404

    like_count, dislike_count = get_likes_dislikes_db(story_id)

    return jsonify({'status': 'success', 'like_count': like_count, 'dislike_count': dislike_count})

def get_likes_dislikes_db(story_id):
    connection = sqlite3.connect('stories.db')
    cursor = connection.cursor()

    # Get the count of likes
    cursor.execute('SELECT COUNT(*) FROM story_likes WHERE story_id = ? AND liked = True', (story_id,))
    likes_count = cursor.fetchone()[0]

    # Get the count of dislikes
    cursor.execute('SELECT COUNT(*) FROM story_likes WHERE story_id = ? AND disliked = True', (story_id,))
    dislikes_count = cursor.fetchone()[0]

    connection.close()

    return likes_count, dislikes_count

@app.route("/delete", methods=["POST"])
@login_required
def delete_like_dislike():
    data = request.json
    story_id = data.get('story_id')
    user_email = session.get('user', {}).get('userinfo', {}).get('email')

    # Connect to the database
    connection = sqlite3.connect('stories.db')
    cursor = connection.cursor()

    # Delete the like/dislike entry
    cursor.execute('DELETE FROM story_likes WHERE story_id = ? AND user_email = ?', (story_id, user_email))
    connection.commit()
    connection.close()

    return jsonify({'status': 'success'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000), debug=Tru   e)
