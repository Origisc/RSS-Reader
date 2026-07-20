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
    def delete_feed(self, feed_id: int) -> bool:
        """
        根据 feed_id 从数据库中彻底删除某个订阅源。
        由于设置了外键级联删除 (ON DELETE CASCADE)，对应的文章会自动被清理。
        """
        try:
            with self.conn:
                # 显式开启外键约束支持（SQLite 默认可能关闭外键级联，这行能确保级联生效）
                self.conn.execute("PRAGMA foreign_keys = ON")

                cursor = self.conn.execute(
                    "DELETE FROM feeds WHERE id = ?",
                    (feed_id,),
                )
                # rowcount 表示受影响的行数，如果大于 0 说明成功删除了记录
                return cursor.rowcount > 0
        except Exception as e:
            print(f"数据库删除 Feed 失败: {e}")
            return False
