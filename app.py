# 📁 server.py -----

import json
import requests
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify
#import logging

# 👆 We're continuing from the steps above. Append this to your server.py file.

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# 👆 We're continuing from the steps above. Append this to your server.py file.

app = Flask(__name__, template_folder="templates")
app.secret_key = env.get("APP_SECRET_KEY")
#logging.basicConfig(filename='app_error.log', level=logging.ERROR)

# 👆 We're continuing from the steps above. Append this to your server.py file.

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

# 👆 We're continuing from the steps above. Append this to your server.py file.

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

# 👆 We're continuing from the steps above. Append this to your server.py file.

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

# 👆 We're continuing from the steps above. Append this to your server.py file.

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

# 👆 We're continuing from the steps above. Append this to your server.py file.

@app.route("/")
def home():
    return render_template("index.html", session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

@app.route("/newsfeed", methods=["GET", "POST"])
def news():
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"

    response = requests.get(url)
    
    if response.status_code == 200:
        data  = response.json()

        """ Commented Sections below are HTML implementation """
        stories_dicts = [] #dict of stories in dictionary/json format

        for ID in data[:30]: #iterate through news
            url = ('https://hacker-news.firebaseio.com/v0/item/'+str(ID)+'.json?print=pretty')
            the_story = requests.get(url) #get the story by ID using url
            the_story_dict = the_story.json() #set story to json format
            stories_dicts.append(the_story_dict) #add story to list
        return jsonify(stories_dicts)
    else: 
        #data = []
        return jsonify({"error": "Failed to fetch data from the Hacker News API"}), 500
    #return render_template("newsfeed.html", session=session.get('user'), stories=stories_dicts)

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=env.get("PORT", 3000), debug=True)
