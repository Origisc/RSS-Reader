import sqlite3
from datetime import datetime

class DBManager:
    def __init__(self, db_path="database.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            # 1. 订阅源表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS feeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    xml_url TEXT UNIQUE,
                    html_url TEXT
                )
            """)
            # 2. 文章表
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feed_id INTEGER,
                    title TEXT,
                    link TEXT UNIQUE,
                    description TEXT,
                    published TEXT,
                    FOREIGN KEY(feed_id) REFERENCES feeds(id) ON DELETE CASCADE
                )
            """)

    def add_feed(self, title, xml_url, html_url=""):
        try:
            with self.conn:
                cursor = self.conn.execute(
                    "INSERT INTO feeds (title, xml_url, html_url) VALUES (?, ?, ?)",
                    (title, xml_url, html_url)
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            # 说明已经存在该订阅源，直接返回已有的 ID
            cursor = self.conn.execute("SELECT id FROM feeds WHERE xml_url = ?", (xml_url,))
            return cursor.fetchone()[0]

    def get_all_feeds(self):
        cursor = self.conn.execute("SELECT id, title, xml_url FROM feeds")
        return cursor.fetchall()

    def save_articles(self, feed_id, entries):
        with self.conn:
            for entry in entries:
                # 提取文章核心信息
                title = entry.get("title", "No Title")
                link = entry.get("link", "")
                description = entry.get("summary", entry.get("description", ""))
                published = entry.get("published", str(datetime.now()))
                
                try:
                    self.conn.execute(
                        "INSERT INTO articles (feed_id, title, link, description, published) VALUES (?, ?, ?, ?, ?)",
                        (feed_id, link, title, description, published)
                    )
                except sqlite3.IntegrityError:
                    # 链接去重，如果文章已存在则跳过
                    continue

    def get_articles_by_feed(self, feed_id):
        cursor = self.conn.execute(
            "SELECT id, title, published FROM articles WHERE feed_id = ? ORDER BY id DESC", (feed_id,)
        )
        return cursor.fetchall()

    def get_article_detail(self, article_id):
        cursor = self.conn.execute(
            "SELECT title, description, link FROM articles WHERE id = ?", (article_id,)
        )
        return cursor.fetchone()
