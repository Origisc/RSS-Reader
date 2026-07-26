import unittest
import sqlite3

from core.database import DBManager

class TestDBManager(unittest.TestCase):
    def setUp(self):
        # 每个测试用例执行前，创建一个完全干净的内存数据库
        self.db = DBManager(":memory:")

    def tearDown(self):
        self.db.conn.close()

    def test_add_and_get_feed(self):
        """验证：能否正确添加并读取订阅源"""
        feed_id = self.db.add_feed("测试博客", "https://example.com/feed")
        
        # 验证返回的 ID 是否有效
        self.assertIsNotNone(feed_id)
        
        # 验证能否查出刚刚添加的数据
        feeds = self.db.get_all_feeds()
        self.assertEqual(len(feeds), 1)
        self.assertEqual(feeds[0][1], "测试博客")  # 验证标题

    def test_feed_url_uniqueness(self):
        """验证：相同 URL 的订阅源是否会自动去重"""
        id1 = self.db.add_feed("博客A", "https://unique.com/feed")
        id2 = self.db.add_feed("博客B", "https://unique.com/feed")
        
        # 两次添加相同的 URL，应该返回同一个 ID
        self.assertEqual(id1, id2)
        feeds = self.db.get_all_feeds()
        self.assertEqual(len(feeds), 1)

    def test_existing_article_schema_receives_processing_columns(self):
        import threading
        connection = sqlite3.connect(":memory:")
        connection.execute(
            """
            CREATE TABLE articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER,
                title TEXT,
                link TEXT UNIQUE,
                description TEXT,
                published TEXT
            )
            """
        )
        database = DBManager.__new__(DBManager)
        database.conn = connection
        database._lock = threading.Lock()

        database.create_tables()

        columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(articles)")
        }
        self.assertTrue(
            {
                "original_html",
                "fetched_at",
                "fetch_status",
                "fetch_error",
                "cleaned_html",
                "cleaned_markdown",
                "cleaned_at",
                "clean_status",
                "clean_error",
                "translated_text",
                "translated_at",
                "translate_status",
                "translate_error",
                "target_language",
                "is_starred",
            }.issubset(columns)
        )
        connection.execute(
            """
            INSERT INTO articles (title, link)
            VALUES ('Migrated article', 'https://example.com/migrated')
            """
        )
        self.assertEqual(
            connection.execute(
                "SELECT is_starred FROM articles"
            ).fetchone()[0],
            0,
        )
        indexes = {
            row[1]
            for row in connection.execute("PRAGMA index_list(articles)")
        }
        self.assertIn("idx_articles_starred_published", indexes)
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        self.assertTrue({"tags", "article_tags"}.issubset(tables))
        article_tag_indexes = {
            row[1]
            for row in connection.execute(
                "PRAGMA index_list(article_tags)"
            )
        }
        self.assertIn(
            "idx_article_tags_tag_article",
            article_tag_indexes,
        )
        connection.close()

    def test_repairs_legacy_swapped_title_link_without_losing_user_state(
        self,
    ):
        feed_id = self.db.add_feed(
            "Legacy feed",
            "https://example.com/feed",
        )
        with self.db.conn:
            cursor = self.db.conn.execute(
                """
                INSERT INTO articles (
                    feed_id,
                    title,
                    link,
                    description,
                    published,
                    fetched_at,
                    fetch_status,
                    fetch_error,
                    clean_status,
                    clean_error,
                    translated_text,
                    translate_status,
                    is_starred
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feed_id,
                    "https://example.com/legacy-article",
                    "Readable legacy title",
                    "<p>Feed summary</p>",
                    "Today",
                    "2026-07-26T12:00:00",
                    "failed",
                    "Invalid URL",
                    "failed",
                    "Fetch failed",
                    "保留的翻译",
                    "success",
                    1,
                ),
            )
            article_id = int(cursor.lastrowid)

        tag_id = int(self.db.create_or_get_tag("Keep tag")[0])
        self.db.add_article_tag(article_id, tag_id)

        self.db.create_tables()
        self.db.create_tables()

        repaired = self.db.conn.execute(
            """
            SELECT
                title,
                link,
                fetched_at,
                fetch_status,
                fetch_error,
                clean_status,
                clean_error,
                translated_text,
                translate_status,
                is_starred
            FROM articles
            WHERE id = ?
            """,
            (article_id,),
        ).fetchone()
        self.assertEqual(
            repaired,
            (
                "Readable legacy title",
                "https://example.com/legacy-article",
                None,
                "pending",
                None,
                "pending",
                None,
                "保留的翻译",
                "success",
                1,
            ),
        )
        self.assertEqual(
            self.db.get_article_tags(article_id),
            [(tag_id, "Keep tag")],
        )

    def test_does_not_swap_rows_when_title_and_link_are_both_urls(self):
        feed_id = self.db.add_feed(
            "URL titles",
            "https://example.com/url-feed",
        )
        with self.db.conn:
            cursor = self.db.conn.execute(
                """
                INSERT INTO articles (feed_id, title, link)
                VALUES (?, ?, ?)
                """,
                (
                    feed_id,
                    "https://example.com/title-as-text",
                    "https://example.com/real-link",
                ),
            )
            article_id = int(cursor.lastrowid)

        self.db.create_tables()

        self.assertEqual(
            self.db.get_article_detail(article_id),
            (
                "https://example.com/title-as-text",
                None,
                "https://example.com/real-link",
            ),
        )

    def test_legacy_swap_conflict_resets_retry_without_deleting_rows(
        self,
    ):
        feed_id = self.db.add_feed(
            "Duplicate legacy feed",
            "https://example.com/duplicate-feed",
        )
        article_url = "https://example.com/same-article"
        with self.db.conn:
            correct_cursor = self.db.conn.execute(
                """
                INSERT INTO articles (feed_id, title, link)
                VALUES (?, ?, ?)
                """,
                (feed_id, "Correct row", article_url),
            )
            correct_id = int(correct_cursor.lastrowid)
            legacy_cursor = self.db.conn.execute(
                """
                INSERT INTO articles (
                    feed_id,
                    title,
                    link,
                    fetch_status,
                    fetch_error,
                    clean_status,
                    clean_error,
                    is_starred
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feed_id,
                    article_url,
                    "Legacy duplicate title",
                    "failed",
                    "Invalid URL",
                    "failed",
                    "Fetch failed",
                    1,
                ),
            )
            legacy_id = int(legacy_cursor.lastrowid)

        self.db.create_tables()

        self.assertEqual(
            self.db.conn.execute(
                """
                SELECT id, title, link
                FROM articles
                WHERE id IN (?, ?)
                ORDER BY id
                """,
                (correct_id, legacy_id),
            ).fetchall(),
            [
                (correct_id, "Correct row", article_url),
                (
                    legacy_id,
                    article_url,
                    "Legacy duplicate title",
                ),
            ],
        )
        self.assertEqual(
            self.db.conn.execute(
                """
                SELECT
                    fetch_status,
                    fetch_error,
                    clean_status,
                    clean_error,
                    is_starred
                FROM articles
                WHERE id = ?
                """,
                (legacy_id,),
            ).fetchone(),
            ("pending", None, "pending", None, 1),
        )

if __name__ == "__main__":
    unittest.main()
