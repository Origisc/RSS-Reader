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
            }.issubset(columns)
        )
        connection.close()

if __name__ == "__main__":
    unittest.main()
