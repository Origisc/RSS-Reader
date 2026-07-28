from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from mercury.agents import (
    TagSource,
    TagSuggestionErrorCode,
    TagSuggestionOptions,
    TagSuggestionResult,
)
from mercury.i18n import Translator


TagSuggestionGenerator = Callable[
    [TagSource, TagSuggestionOptions],
    TagSuggestionResult,
]


class _TagSuggestionWorkerSignals(QObject):
    completed = Signal(int, object)
    failed = Signal(int)


class _TagSuggestionWorker(QRunnable):
    def __init__(
        self,
        token: int,
        generator: TagSuggestionGenerator,
        source: TagSource,
        options: TagSuggestionOptions,
    ) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.token = token
        self.generator = generator
        self.source = source
        self.options = options
        self.signals = _TagSuggestionWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.generator(self.source, self.options)
        except Exception:
            self.signals.failed.emit(self.token)
            return
        self.signals.completed.emit(self.token, result)


class TagSuggestionPanel(QFrame):
    """Generate selectable suggestions without changing local tag data."""

    settings_requested = Signal()
    apply_requested = Signal(str, object)
    generation_completed = Signal(object)

    _ERROR_KEYS = {
        TagSuggestionErrorCode.INVALID_INPUT: "tag_agent.error.invalid_input",
        TagSuggestionErrorCode.PROVIDER_NOT_CONFIGURED: (
            "tag_agent.error.provider_not_configured"
        ),
        TagSuggestionErrorCode.PROVIDER_FAILURE: (
            "tag_agent.error.provider_failure"
        ),
        TagSuggestionErrorCode.EMPTY_RESPONSE: (
            "tag_agent.error.empty_response"
        ),
    }

    def __init__(
        self,
        translator: Translator,
        generator: TagSuggestionGenerator | None = None,
        thread_pool: QThreadPool | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("TagSuggestionPanel")
        self._translator = translator
        self._generator = generator
        self._thread_pool = thread_pool or QThreadPool(self)
        self._source: TagSource | None = None
        self._workers: dict[int, _TagSuggestionWorker] = {}
        self._generation_token = 0
        self._active_token = 0
        self._is_running = False
        self._state = "no_article"
        self._last_error_code: TagSuggestionErrorCode | None = None

        self.title_label = QLabel()
        self.title_label.setObjectName("TagSectionTitle")
        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setObjectName("TagSuggestionPrompt")
        self.prompt_edit.setFixedHeight(52)

        self.generate_button = QPushButton()
        self.generate_button.setObjectName("TagSuggestionGenerateButton")
        self.generate_button.clicked.connect(self.generate_suggestions)
        self.configure_button = QPushButton()
        self.configure_button.setObjectName("TagSuggestionConfigureButton")
        self.configure_button.clicked.connect(self.settings_requested.emit)

        generate_layout = QHBoxLayout()
        generate_layout.setContentsMargins(0, 0, 0, 0)
        generate_layout.setSpacing(5)
        generate_layout.addWidget(self.generate_button)
        generate_layout.addWidget(self.configure_button)

        self.status_label = QLabel()
        self.status_label.setObjectName("TagSuggestionStatus")
        self.status_label.setWordWrap(True)

        self.suggestion_list = QListWidget()
        self.suggestion_list.setObjectName("TagSuggestionList")
        self.suggestion_list.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection
        )
        self.suggestion_list.setMaximumHeight(108)
        self.suggestion_list.itemChanged.connect(self._update_apply_button)

        self.apply_button = QPushButton()
        self.apply_button.setObjectName("TagSuggestionApplyButton")
        self.apply_button.clicked.connect(self._request_apply)
        self.dismiss_button = QPushButton()
        self.dismiss_button.setObjectName("TagSuggestionDismissButton")
        self.dismiss_button.clicked.connect(self.clear_suggestions)

        apply_layout = QHBoxLayout()
        apply_layout.setContentsMargins(0, 0, 0, 0)
        apply_layout.setSpacing(5)
        apply_layout.addWidget(self.apply_button)
        apply_layout.addWidget(self.dismiss_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.title_label)
        layout.addWidget(self.prompt_edit)
        layout.addLayout(generate_layout)
        layout.addWidget(self.status_label)
        layout.addWidget(self.suggestion_list)
        layout.addLayout(apply_layout)

        self.set_translator(translator)
        self.clear_article()

    @property
    def current_article_id(self) -> str | None:
        return self._source.article_id if self._source is not None else None

    @property
    def is_running(self) -> bool:
        return self._is_running

    def set_article(self, source: TagSource) -> None:
        article_changed = self.current_article_id != source.article_id
        if article_changed:
            self._invalidate_generation()
            self.suggestion_list.clear()
        self._source = source
        self._last_error_code = None
        if article_changed or self.suggestion_list.count() == 0:
            self._state = (
                "ready" if self._generator is not None else "unavailable"
            )
        self._render_state()

    def update_tag_context(
        self,
        existing_tags: tuple[str, ...],
        assigned_tags: tuple[str, ...],
    ) -> None:
        if self._source is None:
            return
        self._source = replace(
            self._source,
            existing_tags=existing_tags,
            assigned_tags=assigned_tags,
        )
        assigned = {name.casefold() for name in assigned_tags}
        for row in reversed(range(self.suggestion_list.count())):
            if self.suggestion_list.item(row).text().casefold() in assigned:
                self.suggestion_list.takeItem(row)
        self._update_apply_button()

    def clear_article(self) -> None:
        self._invalidate_generation()
        self._source = None
        self._last_error_code = None
        self.suggestion_list.clear()
        self._state = "no_article"
        self._render_state()

    def clear_suggestions(self) -> None:
        self.suggestion_list.clear()
        if self._source is None:
            self._state = "no_article"
        else:
            self._state = (
                "ready" if self._generator is not None else "unavailable"
            )
        self._render_state()

    def set_translator(self, translator: Translator) -> None:
        self._translator = translator
        self.title_label.setText(translator.text("tag_agent.title"))
        self.prompt_edit.setPlaceholderText(
            translator.text("tag_agent.custom_prompt_placeholder")
        )
        self.configure_button.setText(
            translator.text("tag_agent.configure_ai")
        )
        self.apply_button.setText(translator.text("tag_agent.apply"))
        self.dismiss_button.setText(translator.text("tag_agent.dismiss"))
        self._render_state()

    @Slot()
    def generate_suggestions(self) -> None:
        if self._source is None or self._is_running:
            return
        if self._generator is None:
            self._state = "unavailable"
            self._render_state()
            self.settings_requested.emit()
            return

        self._generation_token += 1
        token = self._generation_token
        self._active_token = token
        self._is_running = True
        self._last_error_code = None
        self._state = "running"
        self._render_state()
        worker = _TagSuggestionWorker(
            token,
            self._generator,
            self._source,
            TagSuggestionOptions(
                custom_prompt=self.prompt_edit.toPlainText(),
            ),
        )
        worker.signals.completed.connect(self._handle_completed)
        worker.signals.failed.connect(self._handle_failed)
        self._workers[token] = worker
        self._thread_pool.start(worker)

    @Slot(int, object)
    def _handle_completed(self, token: int, value: object) -> None:
        self._workers.pop(token, None)
        if token != self._active_token or self._source is None:
            return
        self._is_running = False
        if (
            not isinstance(value, TagSuggestionResult)
            or value.article_id != self._source.article_id
        ):
            self._state = "unexpected_failure"
            self._render_state()
            return

        if value.has_suggestions:
            self._show_suggestions(value.suggestions)
            self._state = "generated"
        else:
            self._last_error_code = value.error_code
            self._state = "result_failure"
        self._render_state()
        self.generation_completed.emit(value)

    @Slot(int)
    def _handle_failed(self, token: int) -> None:
        self._workers.pop(token, None)
        if token != self._active_token or self._source is None:
            return
        self._is_running = False
        self._state = "unexpected_failure"
        self._render_state()

    def _show_suggestions(self, suggestions: tuple[str, ...]) -> None:
        self.suggestion_list.blockSignals(True)
        self.suggestion_list.clear()
        for suggestion in suggestions:
            item = QListWidgetItem(suggestion)
            item.setFlags(
                item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsEnabled
            )
            item.setCheckState(Qt.CheckState.Checked)
            self.suggestion_list.addItem(item)
        self.suggestion_list.blockSignals(False)

    def _request_apply(self) -> None:
        if self._source is None:
            return
        selected = tuple(
            self.suggestion_list.item(row).text()
            for row in range(self.suggestion_list.count())
            if self.suggestion_list.item(row).checkState()
            == Qt.CheckState.Checked
        )
        if not selected:
            return
        self.apply_requested.emit(self._source.article_id, selected)

    def _update_apply_button(self) -> None:
        self.apply_button.setEnabled(
            self._source is not None
            and not self._is_running
            and any(
                self.suggestion_list.item(row).checkState()
                == Qt.CheckState.Checked
                for row in range(self.suggestion_list.count())
            )
        )

    def _render_state(self) -> None:
        state_keys = {
            "no_article": "tag_agent.status.no_article",
            "unavailable": "tag_agent.status.unavailable",
            "ready": "tag_agent.status.ready",
            "running": "tag_agent.status.running",
            "generated": "tag_agent.status.generated",
            "unexpected_failure": "tag_agent.error.unexpected",
        }
        key = (
            self._ERROR_KEYS.get(
                self._last_error_code,
                "tag_agent.error.unexpected",
            )
            if self._state == "result_failure"
            else state_keys.get(self._state, "tag_agent.error.unexpected")
        )
        self.status_label.setText(self._translator.text(key))
        self.generate_button.setText(
            self._translator.text("tag_agent.generate")
        )
        self.generate_button.setEnabled(
            self._source is not None and not self._is_running
        )
        self.suggestion_list.setVisible(self.suggestion_list.count() > 0)
        self.dismiss_button.setVisible(self.suggestion_list.count() > 0)
        self._update_apply_button()

    def _invalidate_generation(self) -> None:
        self._generation_token += 1
        self._active_token = self._generation_token
        self._is_running = False
