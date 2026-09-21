import sqlite3

def init_db():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            movie_id INTEGER PRIMARY KEY,
            file_id TEXT NOT NULL,
            caption TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_movie(movie_id, file_id, caption):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO movies (movie_id, file_id, caption)
        VALUES (?, ?, ?)
    """, (movie_id, file_id, caption))
    conn.commit()
    conn.close()

def get_movie(movie_id):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT file_id, caption FROM movies WHERE movie_id = ?", (movie_id,))
    row = cursor.fetchone()
    conn.close()
    return row