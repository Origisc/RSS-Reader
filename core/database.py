import sqlite3
import threading
from datetime import datetime

class DBManager:
    def __init__(self, db_path="database.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        with self._lock, self.conn:
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
                    original_html TEXT,
                    fetched_at TEXT,
                    fetch_status TEXT DEFAULT 'pending',
                    fetch_error TEXT,
                    cleaned_html TEXT,
                    cleaned_markdown TEXT,
                    cleaned_at TEXT,
                    clean_status TEXT DEFAULT 'pending',
                    clean_error TEXT,
                    is_starred INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(feed_id) REFERENCES feeds(id) ON DELETE CASCADE
                )
            """)
            try:
                self.conn.execute(
                    "ALTER TABLE articles ADD COLUMN original_html TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute(
                    "ALTER TABLE articles ADD COLUMN fetched_at TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute(
                    "ALTER TABLE articles "
                    "ADD COLUMN fetch_status TEXT DEFAULT 'pending'"
                )
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute(
                    "ALTER TABLE articles ADD COLUMN fetch_error TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute("ALTER TABLE articles ADD COLUMN cleaned_html TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute("ALTER TABLE articles ADD COLUMN cleaned_markdown TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute("ALTER TABLE articles ADD COLUMN cleaned_at TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute("ALTER TABLE articles ADD COLUMN clean_status TEXT DEFAULT 'pending'")
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute("ALTER TABLE articles ADD COLUMN clean_error TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute("ALTER TABLE articles ADD COLUMN translated_text TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute("ALTER TABLE articles ADD COLUMN translated_at TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute("ALTER TABLE articles ADD COLUMN translate_status TEXT DEFAULT 'pending'")
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute("ALTER TABLE articles ADD COLUMN translate_error TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute("ALTER TABLE articles ADD COLUMN target_language TEXT DEFAULT 'zh'")
            except sqlite3.OperationalError:
                pass
            try:
                self.conn.execute(
                    "ALTER TABLE articles "
                    "ADD COLUMN is_starred INTEGER NOT NULL DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass
            self.conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_articles_starred_published
                ON articles (is_starred, published DESC, id DESC)
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    created_at TEXT NOT NULL
                )
                """
            )
            self.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS article_tags (
                    article_id INTEGER NOT NULL,
                    tag_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (article_id, tag_id),
                    FOREIGN KEY(article_id)
                        REFERENCES articles(id) ON DELETE CASCADE,
                    FOREIGN KEY(tag_id)
                        REFERENCES tags(id) ON DELETE CASCADE
                )
                """
            )
            self.conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_article_tags_tag_article
                ON article_tags (tag_id, article_id)
                """
            )

    def add_feed(self, title, xml_url, html_url=""):
        try:
            with self._lock, self.conn:
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
        with self._lock:
            cursor = self.conn.execute("SELECT id, title, xml_url FROM feeds")
            return cursor.fetchall()

    def save_articles(self, feed_id, entries):
        with self._lock, self.conn:
            for entry in entries:
                title = entry.get("title", "No Title")
                link = entry.get("link", "")
                
                content = entry.get("content", [])
                if isinstance(content, list) and content:
                    content_dict = content[0]
                    description = content_dict.get("value", "")
                else:
                    description = entry.get("summary", entry.get("description", ""))
                
                published = entry.get("published", str(datetime.now()))
                
                try:
                    self.conn.execute(
                        "INSERT INTO articles (feed_id, title, link, description, published) VALUES (?, ?, ?, ?, ?)",
                        (feed_id, title, link, description, published)
                    )
                except sqlite3.IntegrityError:
                    # 链接去重，如果文章已存在则跳过
                    continue

    def get_articles_by_feed(self, feed_id):
        with self._lock:
            cursor = self.conn.execute(
                """
                SELECT id, title, published, is_starred
                FROM articles
                WHERE feed_id = ?
                ORDER BY id DESC
                """,
                (feed_id,),
            )
            return cursor.fetchall()

    def get_article_detail(self, article_id):
        with self._lock:
            cursor = self.conn.execute(
                "SELECT title, description, link FROM articles WHERE id = ?", (article_id,)
            )
            return cursor.fetchone()

    def get_article_full_detail(self, article_id):
        with self._lock:
            cursor = self.conn.execute(
                """
                SELECT
                    title,
                    description,
                    link,
                    original_html,
                    fetched_at,
                    fetch_status,
                    fetch_error,
                    cleaned_html,
                    cleaned_markdown,
                    cleaned_at,
                    clean_status,
                    clean_error,
                    translated_text,
                    translated_at,
                    translate_status,
                    translate_error,
                    target_language,
                    is_starred
                FROM articles
                WHERE id = ?
                """,
                (article_id,),
            )
            return cursor.fetchone()

    def get_starred_articles(self):
        """Return the global local starred collection in stable order."""
        with self._lock:
            cursor = self.conn.execute(
                """
                SELECT
                    articles.id,
                    articles.feed_id,
                    articles.title,
                    articles.link,
                    articles.published,
                    articles.is_starred,
                    COALESCE(feeds.title, feeds.xml_url, '')
                FROM articles
                LEFT JOIN feeds ON feeds.id = articles.feed_id
                WHERE articles.is_starred = 1
                ORDER BY
                    articles.published DESC,
                    articles.id DESC
                """
            )
            return cursor.fetchall()

    def count_starred_articles(self) -> int:
        with self._lock:
            cursor = self.conn.execute(
                "SELECT COUNT(*) FROM articles WHERE is_starred = 1"
            )
            row = cursor.fetchone()
            return int(row[0]) if row is not None else 0

    def set_article_starred(
        self,
        article_id: int,
        is_starred: bool,
    ) -> bool:
        """Persist user-owned starred state without touching feed data."""
        with self._lock, self.conn:
            cursor = self.conn.execute(
                "UPDATE articles SET is_starred = ? WHERE id = ?",
                (1 if is_starred else 0, article_id),
            )
            return cursor.rowcount > 0

    def create_or_get_tag(self, name: str):
        now = datetime.now().isoformat()
        with self._lock, self.conn:
            self.conn.execute(
                """
                INSERT OR IGNORE INTO tags (name, created_at)
                VALUES (?, ?)
                """,
                (name, now),
            )
            cursor = self.conn.execute(
                """
                SELECT id, name
                FROM tags
                WHERE name = ? COLLATE NOCASE
                """,
                (name,),
            )
            return cursor.fetchone()

    def list_tags(self):
        with self._lock:
            cursor = self.conn.execute(
                """
                SELECT
                    tags.id,
                    tags.name,
                    COUNT(article_tags.article_id)
                FROM tags
                LEFT JOIN article_tags ON article_tags.tag_id = tags.id
                GROUP BY tags.id, tags.name
                ORDER BY tags.name COLLATE NOCASE, tags.id
                """
            )
            return cursor.fetchall()

    def get_tag(self, tag_id: int):
        with self._lock:
            cursor = self.conn.execute(
                """
                SELECT
                    tags.id,
                    tags.name,
                    COUNT(article_tags.article_id)
                FROM tags
                LEFT JOIN article_tags ON article_tags.tag_id = tags.id
                WHERE tags.id = ?
                GROUP BY tags.id, tags.name
                """,
                (tag_id,),
            )
            return cursor.fetchone()

    def get_article_tags(self, article_id: int):
        with self._lock:
            cursor = self.conn.execute(
                """
                SELECT tags.id, tags.name
                FROM tags
                JOIN article_tags ON article_tags.tag_id = tags.id
                WHERE article_tags.article_id = ?
                ORDER BY tags.name COLLATE NOCASE, tags.id
                """,
                (article_id,),
            )
            return cursor.fetchall()

    def rename_tag(self, tag_id: int, new_name: str) -> bool:
        with self._lock, self.conn:
            cursor = self.conn.execute(
                "UPDATE tags SET name = ? WHERE id = ?",
                (new_name, tag_id),
            )
            return cursor.rowcount > 0

    def delete_tag(self, tag_id: int) -> bool:
        with self._lock, self.conn:
            cursor = self.conn.execute(
                "DELETE FROM tags WHERE id = ?",
                (tag_id,),
            )
            return cursor.rowcount > 0

    def add_article_tag(self, article_id: int, tag_id: int) -> bool:
        now = datetime.now().isoformat()
        with self._lock, self.conn:
            cursor = self.conn.execute(
                """
                INSERT OR IGNORE INTO article_tags (
                    article_id,
                    tag_id,
                    created_at
                )
                VALUES (?, ?, ?)
                """,
                (article_id, tag_id, now),
            )
            return cursor.rowcount > 0

    def remove_article_tag(self, article_id: int, tag_id: int) -> bool:
        with self._lock, self.conn:
            cursor = self.conn.execute(
                """
                DELETE FROM article_tags
                WHERE article_id = ? AND tag_id = ?
                """,
                (article_id, tag_id),
            )
            return cursor.rowcount > 0

    def get_articles_by_tag_ids(self, tag_ids: list[int]):
        if not tag_ids:
            return []

        placeholders = ", ".join("?" for _tag_id in tag_ids)
        query = f"""
            SELECT
                articles.id,
                articles.feed_id,
                articles.title,
                articles.link,
                articles.published,
                articles.is_starred,
                COALESCE(feeds.title, feeds.xml_url, '')
            FROM articles
            JOIN article_tags ON article_tags.article_id = articles.id
            LEFT JOIN feeds ON feeds.id = articles.feed_id
            WHERE article_tags.tag_id IN ({placeholders})
            GROUP BY
                articles.id,
                articles.feed_id,
                articles.title,
                articles.link,
                articles.published,
                articles.is_starred,
                feeds.title,
                feeds.xml_url
            HAVING COUNT(DISTINCT article_tags.tag_id) = ?
            ORDER BY articles.published DESC, articles.id DESC
        """
        with self._lock:
            cursor = self.conn.execute(
                query,
                (*tag_ids, len(tag_ids)),
            )
            return cursor.fetchall()

    def save_article_cleaned(self, article_id, cleaned_html, cleaned_markdown, cleaned_at, status="success", error=None):
        try:
            with self._lock, self.conn:
                self.conn.execute(
                    "UPDATE articles SET cleaned_html = ?, cleaned_markdown = ?, cleaned_at = ?, clean_status = ?, clean_error = ? WHERE id = ?",
                    (cleaned_html, cleaned_markdown, cleaned_at, status, error, article_id),
                )
                return True
        except Exception as e:
            print(f"保存文章清洗结果失败: {e}")
            return False

    def save_article_html(self, article_id, html_content, fetched_at, status="success", error=None):
        try:
            with self._lock, self.conn:
                self.conn.execute(
                    "UPDATE articles SET original_html = ?, fetched_at = ?, fetch_status = ?, fetch_error = ? WHERE id = ?",
                    (html_content, fetched_at, status, error, article_id),
                )
                return True
        except Exception as e:
            print(f"保存文章 HTML 失败: {e}")
            return False

    def save_article_translated(self, article_id, translated_text, translated_at, target_language, status="success", error=None):
        try:
            with self._lock, self.conn:
                self.conn.execute(
                    "UPDATE articles SET translated_text = ?, translated_at = ?, target_language = ?, translate_status = ?, translate_error = ? WHERE id = ?",
                    (translated_text, translated_at, target_language, status, error, article_id),
                )
                return True
        except Exception as e:
            print(f"保存文章翻译结果失败: {e}")
            return False

    def delete_feed(self, feed_id: int) -> bool:
        """
        根据 feed_id 从数据库中彻底删除某个订阅源。
        由于设置了外键级联删除 (ON DELETE CASCADE)，对应的文章会自动被清理。
        """
        try:
            with self._lock, self.conn:
                # 显式开启外键约束支持（SQLite 默认可能关闭外键级联，这行能确保级联生效）
                self.conn.execute("PRAGMA foreign_keys = ON")

                cursor = self.conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
                # rowcount 表示受影响的行数，如果大于 0 说明成功删除了记录
                return cursor.rowcount > 0
        except Exception as e:
            print(f"数据库删除 Feed 失败: {e}")
            return False
