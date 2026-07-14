import xml.etree.ElementTree as ET
def import_opml(self, file_path):
        print(f"正在导入 OPML: {file_path}")
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # 寻找所有带有 xmlUrl 的 outline 标签
            count = 0
            for outline in root.findall(".//outline"):
                xml_url = outline.get("xmlUrl")
                if xml_url:
                    title = outline.get("text", outline.get("title", "未命名源"))
                    self.db.add_feed(title, xml_url)
                    count += 1
            print(f"成功从 OPML 导入 {count} 个订阅源！建议稍后执行刷新。")
        except Exception as e:
            print(f"OPML 导入失败: {e}")