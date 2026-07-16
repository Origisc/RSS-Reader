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

QToolBar QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    color: #1f2933;
    padding: 4px 8px;
}

QToolBar QToolButton:hover {
    background: #dde2e6;
    border-color: #c7cdd3;
}

QToolBar QToolButton:pressed,
QToolBar QToolButton:checked {
    background: #cdd9e5;
    border-color: #9fb2c4;
}

QToolBar QToolButton:disabled {
    color: #8a949e;
}

QStatusBar {
    background: #eeeeea;
}

QFrame#ReaderToolbar {
    background: #f1f3f5;
    border-bottom: 1px solid #d5d8dc;
}

QPushButton#ReaderViewButton {
    background: #ffffff;
    border: 1px solid #c9ced4;
    border-radius: 5px;
    color: #34404b;
    padding: 4px 10px;
}

QPushButton#ReaderViewButton:checked {
    background: #d9e8ff;
    border-color: #6b9de3;
    color: #0f3d73;
}

QLabel#ReaderViewStatus {
    color: #5d6975;
    font-size: 11px;
}
"""

DARK_STYLESHEET = """
QMainWindow#MercuryWindow,
QDialog {
    background: #0c1118;
    color: #d9e2ec;
}

QMenuBar,
QMenu,
QStatusBar,
QToolBar#AppToolbar {
    background: #18181c;
    color: #d9e2ec;
}

QMenuBar::item:selected,
QMenu::item:selected {
    background: #242b35;
}

QMenuBar::item,
QMenu::item {
    color: #d9e2ec;
}

QToolBar#AppToolbar {
    border-bottom: 1px solid #29313a;
    padding: 2px 8px;
    spacing: 6px;
}

QToolBar#AppToolbar QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    color: #e5edf5;
    padding: 4px 8px;
}

QToolBar#AppToolbar QToolButton:hover {
    background: #2a323d;
    border-color: #3b4653;
}

QToolBar#AppToolbar QToolButton:pressed,
QToolBar#AppToolbar QToolButton:checked {
    background: #0f68d8;
    border-color: #2487ff;
    color: #ffffff;
}

QToolBar#AppToolbar QToolButton:disabled {
    color: #707b87;
}

QToolBar#AppToolbar::separator {
    background: #3b4653;
    margin: 4px 6px;
    width: 1px;
}

QSplitter::handle {
    background: #27313b;
    width: 1px;
}

QWidget#SidebarPanel,
QWidget#ArticleListPanel {
    background: #15161b;
    border-right: 1px solid #2a2d33;
}

QWidget#ReaderPanel {
    background: #082435;
}

QLabel#PanelTitle,
QLabel#ReaderPanelTitle,
QLabel#TagPanelTitle {
    color: #e5edf5;
    font-size: 13px;
    font-weight: 700;
}

QLabel#PanelActionHint,
QLabel#PanelFooter,
QLabel#TagSectionTitle,
QLabel#TagEmpty,
QLabel#SummaryLabel {
    color: #8996a3;
    font-size: 11px;
}

QPushButton#PrimarySegment,
QPushButton#SecondarySegment,
QPushButton#CompactFilterButton,
QPushButton#TagAddButton {
    background: #22242a;
    border: 1px solid #303640;
    border-radius: 6px;
    color: #cdd6df;
    font-size: 12px;
    padding: 4px 10px;
}

QPushButton#PrimarySegment:checked {
    background: #0b78ff;
    border-color: #0b78ff;
    color: #ffffff;
}

QPushButton#SecondarySegment:disabled,
QPushButton#TagAddButton:disabled {
    color: #65707c;
}

QListWidget#FeedList,
QListWidget#EntryList {
    background: #15161b;
    border: 0;
    color: #d7dde5;
    outline: 0;
}

QListWidget#FeedList::item,
QListWidget#EntryList::item {
    border-bottom: 1px solid #282a30;
    padding: 8px 12px;
}

QListWidget#FeedList::item:selected,
QListWidget#EntryList::item:selected {
    background: #0f68d8;
    border-radius: 6px;
    color: #ffffff;
}

QTextBrowser#ReaderContent {
    background: #082435;
    border: 0;
}

QFrame#ReaderToolbar {
    background: #0f2a3d;
    border-bottom: 1px solid #294759;
}

QPushButton#ReaderViewButton {
    background: #15384d;
    border: 1px solid #31556c;
    border-radius: 5px;
    color: #b9cad7;
    padding: 4px 10px;
}

QPushButton#ReaderViewButton:checked {
    background: #0f68d8;
    border-color: #2487ff;
    color: #ffffff;
}

QLabel#ReaderViewStatus {
    color: #92a8b8;
    font-size: 11px;
}

QDockWidget#TagsDock,
QDockWidget#SummaryDock {
    background: #111a23;
    color: #d9e2ec;
    titlebar-close-icon: none;
}

QDockWidget#TagsDock::title,
QDockWidget#SummaryDock::title {
    background: #18181c;
    padding: 5px 8px;
}

QFrame#TagPanel {
    background: #112c3a;
    border: 1px solid #203d4b;
    border-radius: 8px;
}

QLabel#TagInputPlaceholder {
    background: #1c2732;
    border-radius: 6px;
    color: #8898a7;
    padding: 6px 8px;
}

QLabel[chip="true"] {
    background: #1b4665;
    border-radius: 9px;
    color: #d6e5f2;
    font-size: 11px;
    padding: 4px 8px;
}

QFrame#SummaryPanel {
    background: #18181c;
    border-top: 1px solid #30333a;
}
"""


def stylesheet_for_theme(theme: str) -> str:
    """Return the application stylesheet for a supported theme code."""

    if theme == "light":
        return LIGHT_STYLESHEET

    if theme in {"dark", "system"}:
        return DARK_STYLESHEET

    return ""
