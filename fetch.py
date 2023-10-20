import requests
import sqlite3

def get_hacker_news_data():
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

        return stories_dicts
    else:
        return []
def insert_data_into_db(data):
    connection = sqlite3.connect('stories.db')
    cursor = connection.cursor()

    # Truncate the table before inserting new data.
    cursor.execute('DELETE FROM new_stories;')

    for item in data:
        cursor.execute('''INSERT INTO new_stories (id, by, descendants, score, time, title, url, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (item.get('id', ''), item.get('by', ''), 
            item.get('descendants', 0), item.get('score', ''), item.get('time', ''), 
            item.get('title', ''), item.get('url', ''), item.get('type', ''))
        )    

    connection.commit()
    connection.close()

if __name__ == "__main__":
    news_data = get_hacker_news_data()
    insert_data_into_db(news_data)
