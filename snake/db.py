import psycopg2
import sys
import os

DB_PARAMS = {
    "host": "localhost",
    "database": "phonebook_db", # using the same db from the user's config to be sure we have permissions
    "user": "postgres",
    "password": "SAVA"
}

def get_connection():
    try:
        return psycopg2.connect(**DB_PARAMS)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def init_db():
    conn = get_connection()
    if not conn: return
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS game_sessions (
            id SERIAL PRIMARY KEY,
            player_id INTEGER REFERENCES players(id),
            score INTEGER NOT NULL,
            level INTEGER NOT NULL,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

def get_or_create_player(username):
    conn = get_connection()
    if not conn: return 1
    cur = conn.cursor()
    cur.execute("SELECT id FROM players WHERE username = %s", (username,))
    row = cur.fetchone()
    if row:
        player_id = row[0]
    else:
        cur.execute("INSERT INTO players (username) VALUES (%s) RETURNING id", (username,))
        player_id = cur.fetchone()[0]
        conn.commit()
    cur.close()
    conn.close()
    return player_id

def save_game_session(username, score, level):
    conn = get_connection()
    if not conn: return
    player_id = get_or_create_player(username)
    cur = conn.cursor()
    cur.execute("INSERT INTO game_sessions (player_id, score, level) VALUES (%s, %s, %s)", (player_id, score, level))
    conn.commit()
    cur.close()
    conn.close()

def get_top_10():
    conn = get_connection()
    if not conn: return []
    cur = conn.cursor()
    cur.execute('''
        SELECT p.username, g.score, g.level 
        FROM game_sessions g
        JOIN players p ON p.id = g.player_id
        ORDER BY g.score DESC
        LIMIT 10
    ''')
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_personal_best(username):
    conn = get_connection()
    if not conn: return 0
    cur = conn.cursor()
    cur.execute('''
        SELECT MAX(g.score) 
        FROM game_sessions g
        JOIN players p ON p.id = g.player_id
        WHERE p.username = %s
    ''', (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row and row[0] is not None else 0
