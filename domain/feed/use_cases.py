from core.database import DBManager
import feedparser
import requests

class FeedUseCase:
    def __init__(self,db:DBManager):
        self.db=db

    def add_single_feed(self,xml_url:str):
        print(f"正在下载并解析: {xml_url} ...")
        try:
            res = requests.get(xml_url, timeout=10)
            feed_data = feedparser.parse(res.text)
            
            if feed_data.bozo: # feedparser 的解析错误标志
                print("RSS 源格式可能有误，但仍尝试解析。")
                
            feed_title = feed_data.feed.get("title", xml_url)
            html_url = feed_data.feed.get("link", "")
            
            feed_id = self.db.add_feed(feed_title, xml_url, html_url)
            self.db.save_articles(feed_id, feed_data.entries)
            print(f"成功添加订阅源: {feed_title}，抓取了 {len(feed_data.entries)} 篇文章。")
        except Exception as e:
            print(f"添加失败: {e}")
        pass
    
    def refresh_all(self):
        feeds = self.db.get_all_feeds()
        print(f"开始刷新全部 {len(feeds)} 个订阅源...")
        for feed_id, title, xml_url in feeds:
            try:
                res = requests.get(xml_url, timeout=10)
                feed_data = feedparser.parse(res.text)
                self.db.save_articles(feed_id, feed_data.entries)
                print(f"🔄 已更新: {title}")
            except Exception as e:
                print(f"❌ 更新失败 [{title}]: {e}")
        pass
    
    def remove_feed_by_id(self, feed_id: int) -> dict:
        """
        【新功能】根据 ID 删除订阅源业务用例
        返回状态字典，完美适配未来的 PySide6 异步信号回传
        """
        print(f"正在尝试删除订阅源 ID: {feed_id} ...")
        
        # 调用底层的数据库删除
        success = self.db.delete_feed(feed_id)
        
        if success:
            print(f"✅ 成功删除了订阅源 [ID: {feed_id}] 及其关联的所有文章内容。")
            return {"success": True, "message": "订阅源已成功取消订阅。"}
        else:
            print(f"❌ 删除失败，未找到 ID 为 {feed_id} 的订阅源。")
            return {"success": False, "message": "删除失败：未找到该订阅源或数据库异常。"}
