from PySide6.QtGui import QFont


THEME_CODES = ("system", "light", "dark")
UI_FONT_FAMILIES = (
    "Segoe UI Variable Text",
    "Segoe UI",
    "Microsoft YaHei UI",
    "PingFang SC",
    "Noto Sans CJK SC",
    "Noto Sans",
    "Arial",
)


def preferred_ui_font(point_size: int = 10) -> QFont:
    """Return a readable cross-platform sans-serif application font."""

    font = QFont()
    font.setFamilies(list(UI_FONT_FAMILIES))
    font.setPointSize(point_size)
    return font

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

QToolButton#FeedAddButton,
QToolButton#FeedMenuButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    color: #34404b;
    font-size: 14px;
    font-weight: 700;
    padding: 1px 6px;
}

QToolButton#FeedAddButton {
    border-bottom-right-radius: 0;
    border-top-right-radius: 0;
}

QToolButton#FeedMenuButton {
    border-bottom-left-radius: 0;
    border-left: 0;
    border-top-left-radius: 0;
}

QToolButton#FeedAddButton:hover,
QToolButton#FeedAddButton:pressed,
QToolButton#FeedMenuButton:hover,
QToolButton#FeedMenuButton:pressed {
    background: #dde2e6;
    border-color: #c7cdd3;
}

QWidget#SidebarPanel,
QWidget#ArticleListPanel {
    background: #f3f3f1;
    border-right: 1px solid #d5d8dc;
}

QFrame#SidebarPage,
QStackedWidget#SidebarPages {
    background: transparent;
}

QLabel#PanelTitle,
QLabel#ReaderPanelTitle,
QLabel#TagPanelTitle {
    color: #1f2933;
    font-size: 12px;
    font-weight: 700;
}

QLabel#SidebarHint,
QLabel#PanelFooter,
QLabel#TagSectionTitle,
QLabel#TagEmpty {
    color: #68737d;
    font-size: 10px;
}

QPushButton#PrimarySegment,
QPushButton#SecondarySegment,
QPushButton#EntryFilterButton,
QPushButton#ReaderUtilityButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    color: #4f5d69;
    padding: 3px 9px;
}

QPushButton#PrimarySegment:checked,
QPushButton#SecondarySegment:checked,
QPushButton#EntryFilterButton:checked,
QPushButton#ReaderUtilityButton:checked {
    background: #d9e8ff;
    border-color: #9bbdea;
    color: #0f3d73;
}

QListWidget#FeedList,
QListWidget#SidebarTagList,
QListWidget#EntryList {
    background: #f3f3f1;
    border: 0;
    outline: 0;
}

QListWidget#FeedList::item,
QListWidget#SidebarTagList::item {
    border-bottom: 0;
    padding: 5px 10px;
}

QFrame#TagEditorPopover {
    background: #f7f9fb;
    border: 1px solid #c9d2dc;
    border-radius: 10px;
    margin: 8px;
}

QLineEdit#TagInput {
    background: #ffffff;
    border: 1px solid #c9ced4;
    border-radius: 5px;
    color: #1f2933;
    padding: 4px 7px;
}

QPlainTextEdit#TagSuggestionPrompt,
QListWidget#TagSuggestionList {
    background: #ffffff;
    border: 1px solid #c9ced4;
    border-radius: 5px;
    color: #1f2933;
    padding: 4px 7px;
}

QPushButton#TagSuggestionGenerateButton,
QPushButton#TagSuggestionConfigureButton,
QPushButton#TagSuggestionApplyButton,
QPushButton#TagSuggestionDismissButton {
    background: #ffffff;
    border: 1px solid #bfc6cd;
    border-radius: 4px;
    color: #1f2933;
    padding: 4px 7px;
}

QPushButton#TagSuggestionGenerateButton,
QPushButton#TagSuggestionApplyButton {
    background: #d9e8ff;
    border-color: #6b9de3;
    color: #0f3d73;
}

QLabel#TagSuggestionStatus {
    color: #68737d;
    font-size: 10px;
}

QToolButton#TagPanelCloseButton {
    background: transparent;
    border: 0;
    color: #68737d;
    font-size: 15px;
}

QLabel[chip="true"],
QPushButton[chip="true"] {
    background: #dcecf8;
    border: 1px solid #c4dae9;
    border-radius: 8px;
    color: #24445d;
    font-size: 10px;
    padding: 3px 6px;
}

QPushButton[chip="true"]:checked {
    background: #0f68d8;
    border-color: #0f68d8;
    color: #ffffff;
}

QStatusBar {
    background: #eeeeea;
}

QDialog QLabel {
    background: transparent;
    color: #1f2933;
}

QDialog QCheckBox {
    background: transparent;
    color: #25313c;
    spacing: 7px;
}

QDialog QCheckBox:disabled,
QDialog QLabel:disabled {
    color: #68737d;
}

QDialog#AgentsSettingsDialog,
QWidget#AgentSettingsPage,
QStackedWidget#AgentsSettingsPages {
    background: #f7f7f5;
}

QListWidget#AgentsSettingsList {
    background: #f0f1f2;
    border: 0;
    border-right: 1px solid #d7dbe0;
    border-radius: 0;
    color: #34404b;
    outline: 0;
    padding: 8px 10px;
}

QListWidget#AgentsSettingsList::item {
    border-radius: 7px;
    margin: 0;
    padding: 0 12px;
}

QListWidget#AgentsSettingsList::item:hover {
    background: #e2e6ea;
    color: #1f2933;
}

QListWidget#AgentsSettingsList::item:selected {
    background: #d9e8ff;
    color: #0f3d73;
}

QLabel#AgentsSettingsProperties {
    color: #1f2933;
    font-size: 13px;
    font-weight: 700;
}

QDialog QComboBox,
QDialog QSpinBox,
QDialog QDoubleSpinBox {
    background: #ffffff;
    border: 1px solid #c9ced4;
    border-radius: 4px;
    color: #1f2933;
    padding: 4px 32px 4px 6px;
}

QDialog QLineEdit {
    background: #ffffff;
    border: 1px solid #c9ced4;
    border-radius: 4px;
    color: #1f2933;
    padding: 4px 6px;
    selection-background-color: #d9e8ff;
    selection-color: #0f172a;
}

QDialog QLineEdit:disabled,
QDialog QComboBox:disabled,
QDialog QSpinBox:disabled,
QDialog QDoubleSpinBox:disabled {
    background: #eef1f4;
    border-color: #c9ced4;
    color: #68737d;
}

QDialog QComboBox::drop-down {
    border-left: 1px solid #c9ced4;
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 28px;
}

QDialog QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #bfc6cd;
    color: #1f2933;
    outline: 0;
    selection-background-color: #d9e8ff;
    selection-color: #0f172a;
}

QDialog QSpinBox::up-button,
QDialog QDoubleSpinBox::up-button {
    background: #eef1f4;
    border-bottom: 1px solid #c9ced4;
    border-left: 1px solid #c9ced4;
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 28px;
}

QDialog QSpinBox::down-button,
QDialog QDoubleSpinBox::down-button {
    background: #eef1f4;
    border-left: 1px solid #c9ced4;
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 28px;
}

QDialog QSpinBox::up-button:hover,
QDialog QSpinBox::down-button:hover,
QDialog QDoubleSpinBox::up-button:hover,
QDialog QDoubleSpinBox::down-button:hover {
    background: #d9e8ff;
}

QDialog QSpinBox::up-button:pressed,
QDialog QSpinBox::down-button:pressed,
QDialog QDoubleSpinBox::up-button:pressed,
QDialog QDoubleSpinBox::down-button:pressed {
    background: #c3d8f5;
}

QDialog QPushButton {
    background: #ffffff;
    border: 1px solid #bfc6cd;
    border-radius: 4px;
    color: #1f2933;
    min-width: 72px;
    padding: 5px 12px;
}

QDialog QPushButton:hover {
    background: #e7ebef;
}

QDialog QPushButton:disabled {
    background: #e7eaed;
    border-color: #c9ced4;
    color: #68737d;
}

QDialog QPushButton:default {
    background: #d9e8ff;
    border-color: #6b9de3;
    color: #0f3d73;
}

QDialog#ShortcutHelpDialog QLabel#ShortcutHelpIntro {
    background: transparent;
    color: #34404b;
}

QTableWidget#ShortcutTable {
    background: #ffffff;
    alternate-background-color: #f3f5f7;
    border: 1px solid #c9ced4;
    color: #1f2933;
    gridline-color: #d5d8dc;
}

QTableWidget#ShortcutTable QHeaderView::section {
    background: #e7ebef;
    border: 0;
    border-bottom: 1px solid #bfc6cd;
    border-right: 1px solid #bfc6cd;
    color: #1f2933;
    font-weight: 700;
    padding: 6px 8px;
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

QPushButton#ReaderUtilityButton {
    background: #ffffff;
    border-color: #c9ced4;
}

QFrame#SummarySection,
QFrame#SummaryPanel,
QFrame#TranslationPanel {
    background: #f7f7f5;
    border-top: 1px solid #d5d8dc;
}

QSplitter#ReaderSummarySplitter::handle {
    background: #c9ced4;
    height: 4px;
}

QFrame#SummarySectionTitleBar {
    background: #eeeeea;
    border-bottom: 1px solid #c9ced4;
}

QPushButton#SummarySectionToggleButton {
    background: transparent;
    border: 0;
    color: #34404b;
    font-weight: 700;
    padding: 3px 5px;
    text-align: left;
}

QPushButton#SummarySectionToggleButton:hover {
    color: #0f68d8;
}

QLabel#SummaryFieldLabel,
QLabel#SummaryStatus,
QLabel#SummaryTimestamp,
QLabel#TranslationFieldLabel,
QLabel#TranslationStatus,
QLabel#TranslationTimestamp,
QLabel#TranslationResultLocation {
    background: transparent;
    color: #25313c;
}

QLabel#SummaryStatus,
QLabel#SummaryTimestamp,
QLabel#TranslationStatus,
QLabel#TranslationTimestamp,
QLabel#TranslationResultLocation {
    color: #4f5d69;
    font-size: 11px;
}

QComboBox#SummaryControl,
QPlainTextEdit#SummaryPrompt,
QPlainTextEdit#SummaryContent,
QComboBox#TranslationControl,
QPlainTextEdit#TranslationPrompt {
    background: #ffffff;
    border: 1px solid #c9ced4;
    border-radius: 4px;
    color: #1f2933;
    padding: 4px 6px;
    selection-background-color: #d9e8ff;
    selection-color: #0f172a;
}

QComboBox#SummaryControl QAbstractItemView,
QComboBox#TranslationControl QAbstractItemView {
    background: #ffffff;
    border: 1px solid #bfc6cd;
    color: #1f2933;
    outline: 0;
    selection-background-color: #d9e8ff;
    selection-color: #0f172a;
}

QPushButton#SummaryActionButton,
QPushButton#SummarySecondaryButton,
QPushButton#TranslationActionButton,
QPushButton#TranslationSecondaryButton {
    background: #ffffff;
    border: 1px solid #bfc6cd;
    border-radius: 4px;
    color: #1f2933;
    padding: 5px 12px;
}

QPushButton#SummaryActionButton,
QPushButton#TranslationActionButton {
    background: #d9e8ff;
    border-color: #6b9de3;
    color: #0f3d73;
}

QPushButton#SummaryActionButton:disabled,
QPushButton#TranslationActionButton:disabled {
    background: #e0e5e9;
    border-color: #b8c1c9;
    color: #56636f;
}

QFrame#AppShell {
    background: #ffffff;
}

QFrame#AppHeader {
    background: #f7f7f5;
    border-bottom: 1px solid #d8dadd;
}

QLabel#AppBrand {
    background: transparent;
    color: #292b2f;
    font-size: 20px;
    font-weight: 700;
}

QToolButton#TopActionButton {
    background: #eceeed;
    border: 1px solid #d7dadd;
    border-radius: 9px;
    color: #34373b;
    min-height: 30px;
    min-width: 34px;
    padding: 2px;
}

QToolButton#TopActionButton:hover,
QToolButton#TopActionButton:pressed {
    background: #dfe3e6;
    border-color: #c7ccd1;
}

QWidget#SidebarPanel {
    background: #f4f4f2;
}

QWidget#ArticleListPanel {
    background: #fbfbfa;
}

QLabel#PanelTitle,
QLabel#ReaderPanelTitle {
    font-size: 15px;
}

QPushButton#PrimarySegment,
QPushButton#SecondarySegment {
    font-size: 14px;
    padding: 6px 12px;
}

QListWidget#FeedList,
QListWidget#SidebarTagList {
    background: #f4f4f2;
    font-size: 14px;
}

QListWidget#EntryList {
    background: #fbfbfa;
    border: 0;
}

QListWidget#FeedList::item,
QListWidget#SidebarTagList::item {
    border-radius: 7px;
    margin: 2px 8px;
    padding: 8px 10px;
}

QListWidget#FeedList::item:selected,
QListWidget#SidebarTagList::item:selected {
    background: #dedfdf;
    color: #202124;
}

QWidget#ReaderPanel,
QTextBrowser#ReaderContent {
    background: #ffffff;
}

QFrame#ReaderToolbar {
    background: #f8f8f7;
    border-bottom: 1px solid #e0e2e4;
}

QPushButton#ReaderViewButton,
QPushButton#ReaderUtilityButton,
QPushButton#EntryFilterButton {
    border-radius: 8px;
    min-height: 24px;
    padding: 4px 10px;
}

"""

DARK_STYLESHEET = """
QMainWindow#MercuryWindow,
QDialog {
    background: #0c1118;
    color: #d9e2ec;
}

QDialog QLabel {
    background: transparent;
    color: #e5edf5;
}

QDialog QCheckBox {
    background: transparent;
    color: #f3f6f9;
    spacing: 7px;
}

QDialog QCheckBox:disabled,
QDialog QLabel:disabled {
    color: #aeb9c4;
}

QDialog#AgentsSettingsDialog,
QWidget#AgentSettingsPage,
QStackedWidget#AgentsSettingsPages {
    background: #18181c;
}

QListWidget#AgentsSettingsList {
    background: #141519;
    border: 0;
    border-right: 1px solid #2d3036;
    border-radius: 0;
    color: #d9e2ec;
    outline: 0;
    padding: 8px 10px;
}

QListWidget#AgentsSettingsList::item {
    border-radius: 7px;
    margin: 0;
    padding: 0 12px;
}

QListWidget#AgentsSettingsList::item:hover {
    background: #252831;
    color: #f3f6f9;
}

QListWidget#AgentsSettingsList::item:selected {
    background: #1769c2;
    color: #ffffff;
}

QLabel#AgentsSettingsProperties {
    color: #f3f6f9;
    font-size: 13px;
    font-weight: 700;
}

QDialog QComboBox,
QDialog QSpinBox,
QDialog QDoubleSpinBox {
    background: #202833;
    border: 1px solid #465363;
    border-radius: 4px;
    color: #f3f6f9;
    padding: 4px 32px 4px 6px;
    selection-background-color: #0f68d8;
    selection-color: #ffffff;
}

QDialog QLineEdit {
    background: #202833;
    border: 1px solid #465363;
    border-radius: 4px;
    color: #f3f6f9;
    padding: 4px 6px;
    selection-background-color: #0f68d8;
    selection-color: #ffffff;
}

QDialog QLineEdit:disabled,
QDialog QComboBox:disabled,
QDialog QSpinBox:disabled,
QDialog QDoubleSpinBox:disabled {
    background: #252b33;
    border-color: #3f4853;
    color: #b8c2cc;
}

QDialog QComboBox::drop-down {
    border-left: 1px solid #465363;
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 28px;
}

QDialog QComboBox QAbstractItemView {
    background: #202833;
    border: 1px solid #526174;
    color: #f3f6f9;
    outline: 0;
    selection-background-color: #0f68d8;
    selection-color: #ffffff;
}

QDialog QSpinBox::up-button,
QDialog QDoubleSpinBox::up-button {
    background: #293442;
    border-bottom: 1px solid #465363;
    border-left: 1px solid #465363;
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 28px;
}

QDialog QSpinBox::down-button,
QDialog QDoubleSpinBox::down-button {
    background: #293442;
    border-left: 1px solid #465363;
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 28px;
}

QDialog QSpinBox::up-button:hover,
QDialog QSpinBox::down-button:hover,
QDialog QDoubleSpinBox::up-button:hover,
QDialog QDoubleSpinBox::down-button:hover {
    background: #3b4a5c;
}

QDialog QSpinBox::up-button:pressed,
QDialog QSpinBox::down-button:pressed,
QDialog QDoubleSpinBox::up-button:pressed,
QDialog QDoubleSpinBox::down-button:pressed {
    background: #0f68d8;
}

QDialog QPushButton {
    background: #2a323d;
    border: 1px solid #465363;
    border-radius: 4px;
    color: #e5edf5;
    min-width: 72px;
    padding: 5px 12px;
}

QDialog QPushButton:hover {
    background: #354150;
    border-color: #607084;
}

QDialog QPushButton:disabled {
    background: #252b33;
    border-color: #3f4853;
    color: #aeb9c4;
}

QDialog QPushButton:default {
    background: #0f68d8;
    border-color: #2487ff;
    color: #ffffff;
}

QDialog#ShortcutHelpDialog QLabel#ShortcutHelpIntro {
    background: transparent;
    color: #c1ccd6;
}

QTableWidget#ShortcutTable {
    background: #202833;
    alternate-background-color: #26313d;
    border: 1px solid #465363;
    color: #f3f6f9;
    gridline-color: #465363;
}

QTableWidget#ShortcutTable QHeaderView::section {
    background: #2a323d;
    border: 0;
    border-bottom: 1px solid #596878;
    border-right: 1px solid #596878;
    color: #f3f6f9;
    font-weight: 700;
    padding: 6px 8px;
}

QMenuBar,
QMenu,
QStatusBar {
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

QToolButton#FeedAddButton,
QToolButton#FeedMenuButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 4px;
    color: #b7c5d3;
    font-size: 14px;
    font-weight: 700;
    padding: 1px 6px;
}

QToolButton#FeedAddButton {
    border-bottom-right-radius: 0;
    border-top-right-radius: 0;
}

QToolButton#FeedMenuButton {
    border-bottom-left-radius: 0;
    border-left: 0;
    border-top-left-radius: 0;
}

QToolButton#FeedAddButton:hover,
QToolButton#FeedAddButton:pressed,
QToolButton#FeedMenuButton:hover,
QToolButton#FeedMenuButton:pressed {
    background: #2a323d;
    border-color: #3b4653;
}

QSplitter::handle {
    background: #27313b;
    width: 1px;
}

QSplitter#ReaderSummarySplitter::handle {
    background: #30333a;
    height: 4px;
}

QWidget#SidebarPanel,
QWidget#ArticleListPanel {
    background: #15161b;
    border-right: 1px solid #2a2d33;
}

QFrame#SidebarPage,
QStackedWidget#SidebarPages {
    background: transparent;
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
QLabel#SidebarHint,
QLabel#TagSectionTitle,
QLabel#TagEmpty,
QLabel#SummaryLabel {
    color: #8996a3;
    font-size: 11px;
}

QPushButton#PrimarySegment,
QPushButton#SecondarySegment,
QPushButton#EntryFilterButton,
QPushButton#ReaderUtilityButton,
QPushButton#TagAddButton {
    background: #22242a;
    border: 1px solid #303640;
    border-radius: 6px;
    color: #cdd6df;
    font-size: 12px;
    padding: 4px 10px;
}

QPushButton#PrimarySegment:checked,
QPushButton#SecondarySegment:checked,
QPushButton#EntryFilterButton:checked,
QPushButton#ReaderUtilityButton:checked {
    background: #0b78ff;
    border-color: #0b78ff;
    color: #ffffff;
}

QPushButton#TagAddButton:disabled {
    color: #65707c;
}

QListWidget#FeedList,
QListWidget#SidebarTagList,
QListWidget#EntryList {
    background: #15161b;
    border: 0;
    color: #d7dde5;
    outline: 0;
}

QListWidget#FeedList::item,
QListWidget#SidebarTagList::item {
    border-bottom: 0;
    padding: 5px 10px;
}

QListWidget#EntryList::item {
    border-bottom: 1px solid #282a30;
    padding: 8px 12px;
}

QListWidget#FeedList::item:selected,
QListWidget#SidebarTagList::item:selected,
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

QPushButton#ReaderUtilityButton {
    background: #15384d;
    border-color: #31556c;
}

QLabel#ReaderViewStatus {
    color: #92a8b8;
    font-size: 11px;
}

QFrame#TagEditorPopover {
    background: #112c3a;
    border: 1px solid #315064;
    border-radius: 10px;
    margin: 8px;
}

QLineEdit#TagInput {
    background: #1c2732;
    border: 1px solid #344759;
    border-radius: 6px;
    color: #e5edf5;
    padding: 5px 7px;
    selection-background-color: #0f68d8;
    selection-color: #ffffff;
}

QPlainTextEdit#TagSuggestionPrompt,
QListWidget#TagSuggestionList {
    background: #1c2732;
    border: 1px solid #344759;
    border-radius: 6px;
    color: #e5edf5;
    padding: 5px 7px;
    selection-background-color: #0f68d8;
    selection-color: #ffffff;
}

QPushButton#TagSuggestionGenerateButton,
QPushButton#TagSuggestionConfigureButton,
QPushButton#TagSuggestionApplyButton,
QPushButton#TagSuggestionDismissButton {
    background: #22242a;
    border: 1px solid #303640;
    border-radius: 5px;
    color: #cdd6df;
    padding: 4px 7px;
}

QPushButton#TagSuggestionGenerateButton,
QPushButton#TagSuggestionApplyButton {
    background: #0b78ff;
    border-color: #0b78ff;
    color: #ffffff;
}

QPushButton#TagSuggestionGenerateButton:disabled,
QPushButton#TagSuggestionApplyButton:disabled {
    background: #27313b;
    border-color: #303640;
    color: #65707c;
}

QLabel#TagSuggestionStatus {
    color: #8996a3;
    font-size: 11px;
}

QToolButton#TagPanelCloseButton {
    background: transparent;
    border: 0;
    color: #9eb0bf;
    font-size: 15px;
}

QToolButton#TagPanelCloseButton:hover {
    color: #ffffff;
}

QLabel[chip="true"],
QPushButton[chip="true"] {
    background: #1b4665;
    border: 1px solid #2b5d7f;
    border-radius: 9px;
    color: #d6e5f2;
    font-size: 11px;
    padding: 4px 8px;
}

QPushButton[chip="true"]:checked {
    background: #0f68d8;
    border-color: #3b8df0;
    color: #ffffff;
}

QFrame#SummarySection,
QFrame#SummaryPanel,
QFrame#TranslationPanel {
    background: #18181c;
    border-top: 1px solid #30333a;
}

QFrame#SummarySectionTitleBar {
    background: #18181c;
    border-bottom: 1px solid #30333a;
}

QPushButton#SummarySectionToggleButton {
    background: transparent;
    border: 0;
    color: #d9e2ec;
    font-weight: 700;
    padding: 3px 5px;
    text-align: left;
}

QPushButton#SummarySectionToggleButton:hover {
    color: #69aefc;
}

QLabel#SummaryFieldLabel,
QLabel#SummaryStatus,
QLabel#SummaryTimestamp,
QLabel#TranslationFieldLabel,
QLabel#TranslationStatus,
QLabel#TranslationTimestamp,
QLabel#TranslationResultLocation {
    background: transparent;
    color: #f3f6f9;
}

QLabel#SummaryStatus,
QLabel#SummaryTimestamp,
QLabel#TranslationStatus,
QLabel#TranslationTimestamp,
QLabel#TranslationResultLocation {
    color: #c1ccd6;
    font-size: 11px;
}

QComboBox#SummaryControl,
QPlainTextEdit#SummaryPrompt,
QPlainTextEdit#SummaryContent,
QComboBox#TranslationControl,
QPlainTextEdit#TranslationPrompt {
    background: #202833;
    border: 1px solid #465363;
    border-radius: 4px;
    color: #f3f6f9;
    padding: 4px 6px;
    selection-background-color: #0f68d8;
    selection-color: #ffffff;
}

QComboBox#SummaryControl QAbstractItemView,
QComboBox#TranslationControl QAbstractItemView {
    background: #202833;
    border: 1px solid #526174;
    color: #f3f6f9;
    outline: 0;
    selection-background-color: #0f68d8;
    selection-color: #ffffff;
}

QPushButton#SummaryActionButton,
QPushButton#SummarySecondaryButton,
QPushButton#TranslationActionButton,
QPushButton#TranslationSecondaryButton {
    background: #2a323d;
    border: 1px solid #465363;
    border-radius: 4px;
    color: #e5edf5;
    padding: 5px 12px;
}

QPushButton#SummaryActionButton,
QPushButton#TranslationActionButton {
    background: #0f68d8;
    border-color: #2487ff;
    color: #ffffff;
}

QPushButton#SummaryActionButton:disabled,
QPushButton#TranslationActionButton:disabled {
    background: #35414d;
    border-color: #596878;
    color: #d2dbe3;
}

QFrame#AppShell {
    background: #191b1f;
}

QFrame#AppHeader {
    background: #24272b;
    border-bottom: 1px solid #383c42;
}

QLabel#AppBrand {
    background: transparent;
    color: #f1f2f3;
    font-size: 20px;
    font-weight: 700;
}

QToolButton#TopActionButton {
    background: #30343a;
    border: 1px solid #41464e;
    border-radius: 9px;
    color: #eef1f3;
    min-height: 30px;
    min-width: 34px;
    padding: 2px;
}

QToolButton#TopActionButton:hover,
QToolButton#TopActionButton:pressed {
    background: #3b4047;
    border-color: #555c65;
}

QSplitter::handle {
    background: #373c43;
}

QWidget#SidebarPanel {
    background: #171a1d;
    border-right: 1px solid #34383e;
}

QWidget#ArticleListPanel {
    background: #22262a;
    border-right: 1px solid #3a3f45;
}

QLabel#PanelTitle,
QLabel#ReaderPanelTitle {
    color: #f0f1f2;
    font-size: 15px;
}

QPushButton#PrimarySegment,
QPushButton#SecondarySegment {
    font-size: 14px;
    padding: 6px 12px;
}

QListWidget#FeedList,
QListWidget#SidebarTagList {
    background: #171a1d;
    color: #e5e7e9;
    font-size: 14px;
}

QListWidget#EntryList {
    background: #22262a;
    border: 0;
}

QListWidget#FeedList::item,
QListWidget#SidebarTagList::item {
    border-radius: 7px;
    margin: 2px 8px;
    padding: 8px 10px;
}

QListWidget#FeedList::item:selected,
QListWidget#SidebarTagList::item:selected {
    background: #3a3d42;
    color: #ffffff;
}

QListWidget#SidebarTagList::indicator {
    width: 14px;
    height: 14px;
}

QListWidget#SidebarTagList::indicator:unchecked {
    background: transparent;
    border: 1px solid #ffffff;
    border-radius: 3px;
}

QListWidget#SidebarTagList::indicator:checked {
    background: #ffffff;
    border: 1px solid #ffffff;
    border-radius: 3px;
}

QWidget#ReaderPanel,
QTextBrowser#ReaderContent {
    background: #191b1f;
}

QFrame#ReaderToolbar {
    background: #24272b;
    border-bottom: 1px solid #383d43;
}

QPushButton#ReaderViewButton,
QPushButton#ReaderUtilityButton,
QPushButton#EntryFilterButton {
    background: #30343a;
    border: 1px solid #424850;
    border-radius: 8px;
    color: #d9dde1;
    min-height: 24px;
    padding: 4px 10px;
}

QFrame#SummarySectionTitleBar {
    background: #202327;
    border-bottom: 1px solid #383d43;
}

"""


def stylesheet_for_theme(theme: str) -> str:
    """Return the application stylesheet for a supported theme code."""

    if theme == "light":
        return LIGHT_STYLESHEET

    if theme in {"dark", "system"}:
        return DARK_STYLESHEET

    return ""
