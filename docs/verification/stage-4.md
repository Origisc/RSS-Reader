# 第四阶段验收：星标收藏

当前第四阶段先交付星标收藏。标签、筛选和导出将在后续子任务完成；
笔记面板按项目约定暂缓。

## 自动验证

优先使用 `uv`：

```powershell
uv run python -m unittest tests.test_starred_entries -v
uv run python -m unittest discover -s tests -p "test_*.py" -q
```

如果当前 Windows 环境无法直接找到 `uv`，可使用项目虚拟环境：

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_starred_entries -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -q
```

自动测试不得使用真实 Feed 网络请求、真实 API Key 或在线 LLM。

## 人工验证

启动：

```powershell
uv run python main.py
```

1. 打开“全部文章”或任意 Feed。
2. 将鼠标移到一篇未星标文章上，确认右侧出现轮廓星。
3. 点击轮廓星：
   - 星形变为黄色实心；
   - 当前选中的文章不发生改变；
   - 侧栏“星标”数量立即增加。
4. 切换到侧栏“星标”，确认可以看到刚收藏的文章，标题显示“星标”。
5. 开启“仅未读”，确认星标集合可以与未读状态组合筛选。
6. 在星标列表准备至少三篇文章，取消中间当前文章的星标：
   - 该文章立即消失；
   - 自动选择下一篇；
   - 新选择不会因为系统接续被自动标记为已读。
7. 取消最后一篇当前文章的星标，确认自动选择上一篇。
8. 取消唯一剩余文章的星标，确认列表、选择和 Reader 被清空。
9. 关闭并重新启动应用，确认剩余星标状态仍然存在。
10. 刷新 Feed，确认已有星标不会被覆盖。
11. 切换英文/简体中文，确认“全部文章”“星标”、按钮提示和状态消息即时更新。

## 验收门

- 星标只保存在本地，不产生额外网络请求。
- 旧数据库迁移不丢失订阅源、文章或 AI 结果。
- 星标/取消星标不会误改文章选择。
- Feed 刷新、去重、抓取、清洗和翻译不会覆盖星标。
- 无 AI 配置时星标及基础阅读功能完整可用。
- 星标测试和全量测试全部通过。
