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