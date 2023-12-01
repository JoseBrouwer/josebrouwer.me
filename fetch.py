"""
Module: fetch.py

This module is responsible for fetching and updating Hacker News stories data in a
local SQLite database.

It retrieves the latest news from Hacker News API, formats the data, 
and updates the local database with the new information.

The module includes functions to convert Unix epoch time to a human-readable format,
fetch news data from Hacker News API, and insert this data into a SQLite database.

Functions:
- convert_time(epoch_time): Converts Unix epoch time to a readable datetime string.
- get_hacker_news_data(): Fetches the latest news data from Hacker News API.
- insert_data_into_db(data): Inserts fetched news data into the SQLite database.

Usage:
This script can be run as a standalone script to update the local database with
the latest news from Hacker News.

Example:
python3 fetch.py
"""
import sqlite3
from datetime import datetime
from operator import itemgetter
import requests

def convert_time(epoch_time):
    """
    Converts Unix epoch time to a human-readable datetime string.

    Parameters:
    - epoch_time (int): The time in Unix epoch format.

    Returns:
    - str: A formatted time string in the format '%Y-%m-%d %H:%M:%S'.
    """
    # Convert Unix epoch time to datetime
    dt_object = datetime.fromtimestamp(epoch_time)

    # Format the datetime object as a string
    formatted_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")

    return formatted_time


def get_hacker_news_data():
    """
    Fetches the latest news data from Hacker News API.

    Retrieves top story IDs from Hacker News API and fetches individual story data. 
    Sorts the stories first by score in ascending order, then by time in descending order.

    Returns:
    - list: A list of dictionaries containing sorted news stories.
    """
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    response = requests.get(url, timeout=10)

    if response.status_code == 200:
        data = response.json()
        stories_dicts = []

        for x in data[0:]:
            url = f"https://hacker-news.firebaseio.com/v0/item/{x}.json"
            the_story = requests.get(url, timeout=10)
            the_story_dict = the_story.json()
            stories_dicts.append(the_story_dict)

        # First, sort the news items by 'score' in ascending order
        stories_dicts.sort(key=itemgetter("score"))

        # Then, sort by 'time' in descending order (newest first)
        sorted_news = sorted(stories_dicts, key=itemgetter("time"), reverse=True)

        print("retrieved news")
        return sorted_news
    return []


def insert_data_into_db(data):
    """
    Inserts fetched news data into the SQLite database.

    Parameters:
    - data (list): A list of news story dictionaries to be inserted into the database.

    Deletes existing records in the database and inserts new data.
    """
    connection = sqlite3.connect("stories.db")
    cursor = connection.cursor()

    # Truncate the table before inserting new data.
    cursor.execute("DELETE FROM new_stories")

    for item in data:
        epoch_time = item.get("time", "")  # get time
        time = convert_time(epoch_time)
        cursor.execute(
            """INSERT INTO new_stories (id, by, descendants, score, time, title, url, type, text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item.get("id", ""),
                item.get("by", ""),
                item.get("descendants", 0),
                item.get("score", ""),
                time,
                item.get("title", ""),
                item.get("url", ""),
                item.get("type", ""),
                item.get("text", ""),
            ),
        )

    connection.commit()
    connection.close()
    print("inserted news in db")


if __name__ == "__main__":
    news_data = get_hacker_news_data()
    insert_data_into_db(news_data)
