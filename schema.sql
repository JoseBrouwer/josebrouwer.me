CREATE TABLE story_kids (
    parent_id INTEGER,
    kid_id INTEGER,
    FOREIGN KEY (parent_id) REFERENCES stories (id)
);
CREATE TABLE new_stories (
    by TEXT NOT NULL,
    id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    time INTEGER NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    descendants INTEGER,
    type TEXT
, text TEXT);
CREATE TABLE users (
id INTEGER PRIMARY KEY AUTOINCREMENT, 
email TEXT NOT NULL,
name TEXT NOT NULL,
nickname TEXT, 
picture TEXT
, admin BOOLEAN DEFAULT 0);
CREATE TABLE story_likes (
    story_id INTEGER NOT NULL,
    user_email TEXT NOT NULL,
    liked BOOLEAN,
    disliked BOOLEAN,
    by TEXT,
    score INTEGER,
    time INTEGER,
    title TEXT,
    url TEXT,
    descendants INTEGER,
    type TEXT,
    text TEXT,
    PRIMARY KEY (story_id, user_email),
    FOREIGN KEY (user_email) REFERENCES users(email)
);
