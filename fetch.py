import requests
import sqlite3
from datetime import datetime
from operator import itemgetter

def convert_time(epoch_time):
    # Convert Unix epoch time to datetime
    dt_object = datetime.fromtimestamp(epoch_time)

    # Format the datetime object as a string
    formatted_time = dt_object.strftime('%Y-%m-%d %H:%M:%S')

    return formatted_time

def get_hacker_news_data():
    print("retrieved news")
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        stories_dicts = []

        for ID in data[0:]:
            url = f"https://hacker-news.firebaseio.com/v0/item/{ID}.json"
            the_story = requests.get(url)
            the_story_dict = the_story.json()
            stories_dicts.append(the_story_dict)

        # First, sort the news items by 'score' in ascending order
        stories_dicts.sort(key=itemgetter('score'))

        # Then, sort by 'time' in descending order (newest first)
        sorted_news = sorted(stories_dicts, key=itemgetter('time'), reverse=True)

        return sorted_news
    else:
        return []

def insert_data_into_db(data):
    print("inserted news in db")
    connection = sqlite3.connect('stories.db')
    cursor = connection.cursor()

    # Truncate the table before inserting new data.
    cursor.execute('DELETE FROM new_stories;')

    for item in data:
        epoch_time = item.get('time', '') #get time
        time = convert_time(epoch_time)
        cursor.execute('''INSERT INTO new_stories (id, by, descendants, score, time, title, url, type, text)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (item.get('id', ''), item.get('by', ''), 
            item.get('descendants', 0), item.get('score', ''), time, 
            item.get('title', ''), item.get('url', ''), item.get('type', ''), item.get('text', ''))
        )

    connection.commit()
    connection.close()

if __name__ == "__main__":
    news_data = get_hacker_news_data()
    insert_data_into_db(news_data)
