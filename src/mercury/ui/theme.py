THEME_CODES = ("system", "light", "dark")

LIGHT_STYLESHEET = """
QMainWindow,
QDialog,
QWidget {
    background: #f7f7f5;
    color: #1f2933;
}

QListWidget,
QTextBrowser,
QComboBox {
    background: #ffffff;
    border: 1px solid #d5d8dc;
    color: #1f2933;
}

QListWidget::item {
    padding: 6px;
}

QListWidget::item:selected {
    background: #d9e8ff;
    color: #0f172a;
}

QToolBar {
    background: #eeeeea;
    border-bottom: 1px solid #d5d8dc;
    spacing: 6px;
}

QStatusBar {
    background: #eeeeea;
}
"""

DARK_STYLESHEET = """
QMainWindow,
QDialog,
QWidget {
    background: #202124;
    color: #e8eaed;
}

QMenuBar,
QMenu,
QToolBar,
QStatusBar {
    background: #2b2c30;
    color: #e8eaed;
}

QMenu::item:selected {
    background: #3b4757;
}

QListWidget,
QTextBrowser,
QComboBox {
    background: #17181b;
    border: 1px solid #44474d;
    color: #e8eaed;
}

QListWidget::item {
    padding: 6px;
}

QListWidget::item:selected {
    background: #38506d;
    color: #ffffff;
}

QPushButton {
    background: #303134;
    border: 1px solid #5f6368;
    color: #e8eaed;
    padding: 5px 10px;
}

QPushButton:hover {
    background: #3c4043;
}
"""


def stylesheet_for_theme(theme: str) -> str:
    """Return the application stylesheet for a supported theme code."""

    if theme == "light":
        return LIGHT_STYLESHEET

    if theme == "dark":
        return DARK_STYLESHEET

    return ""
