import unittest
from core.database import DBManager
from domain.feed.use_cases import FeedUseCase


class TestDeleteFeature(unittest.TestCase):
    def setUp(self):
        # 1. 每次测试前，在内存中初始化一个完全干净的数据库
        self.db = DBManager(":memory:")
        self.use_case = FeedUseCase(self.db)

        # 2. 预埋测试数据：添加一个模拟订阅源
        self.feed_id = self.db.add_feed("待删除的测试源", "https://test-delete.com/feed")

        # 3. 预埋测试数据：为该订阅源模拟插入 2 篇文章
        mock_entries = [
            {"title": "测试文章 1", "link": "https://test-delete.com/1", "summary": "正文 1"},
            {"title": "测试文章 2", "link": "https://test-delete.com/2", "summary": "正文 2"}
        ]
        self.db.save_articles(self.feed_id, mock_entries)

    def test_delete_feed_success(self):
        """验证点 1：输入正确的 ID，应该成功删除订阅源，并且返回正确的状态"""
        # 执行删除业务逻辑
        result = self.use_case.remove_feed_by_id(self.feed_id)

        # 断言：业务返回的字典中 success 应当为 True
        self.assertTrue(result["success"])

        # 断言：此时再去查询所有订阅源，数量应当为 0
        all_feeds = self.db.get_all_feeds()
        self.assertEqual(len(all_feeds), 0)

    def test_cascade_delete_articles(self):
        """验证点 2：核心安全机制验证！删除 Feed 时，其下属文章必须被级联清理"""
        # 验证前置条件：删除前，确保文章确实成功存入了数据库（数量为 2）
        articles_before = self.db.get_articles_by_feed(self.feed_id)
        self.assertEqual(len(articles_before), 2)

        # 执行删除
        self.use_case.remove_feed_by_id(self.feed_id)

        # 断言：由于外键级联删除 (ON DELETE CASCADE) 生效，文章表里该 feed_id 的数据应当自动清空
        articles_after = self.db.get_articles_by_feed(self.feed_id)
        self.assertEqual(len(articles_after), 0)

    def test_delete_non_existent_feed(self):
        """验证点 3：容错性验证！尝试删除一个根本不存在的非法 ID 时，系统不会崩溃且会报错"""
        # 传入一个不存在的假 ID（例如 999）
        invalid_id = 999
        result = self.use_case.remove_feed_by_id(invalid_id)

        # 断言：业务层应当识别出失败，返回 success 为 False
        self.assertFalse(result["success"])
        # 断言：原有的合法订阅源不应该受到影响，依然完好损耗存在
        all_feeds = self.db.get_all_feeds()
        self.assertEqual(len(all_feeds), 1)

    def tearDown(self):
        self.db.conn.close()


if __name__ == "__main__":
    unittest.main()
