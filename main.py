# main.py
import sys
from PySide6.QtWidgets import QApplication
from core.database import DBManager
from domain.feed.use_cases import FeedUseCase
from ui.main_window import MainWindow

def main():
    # 1. 初始化后端核心
    db = DBManager("database.db")
    feed_services = FeedUseCase(db)
    
    # 2. 启动 PySide6 应用
    app = QApplication(sys.argv)
    
    # 3. 传入后端服务，实例化主窗口
    window = MainWindow(feed_services)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


