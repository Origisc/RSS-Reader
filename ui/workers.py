# ui/workers.py
from PySide6.QtCore import QThread, Signal
from domain.feed.use_cases import FeedUseCase

class RefreshFeedsWorker(QThread):
    # 定义信号：告诉前端什么时候开始，什么时候刷新结束
    started = Signal()
    finished = Signal(bool, str)  # 返回 (是否成功, 提示信息)

    def __init__(self, feed_use_case: FeedUseCase):
        super().__init__()
        self.feed_use_case = feed_use_case

    def run(self):
        self.started.emit()
        try:
            # 调用你之前写的核心后端刷新逻辑
            self.feed_use_case.refresh_all()
            self.finished.emit(True, "所有订阅源刷新成功！")
        except Exception as e:
            self.finished.emit(False, f"刷新失败: {str(e)}")
