from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from mercury.agents import SummaryOptions, SummarySource
from mercury.domain import (
    SummaryDetail,
    SummaryErrorCode,
    SummaryResult,
    SummaryStatus,
)
from mercury.i18n import Translator


SummaryGenerator = Callable[[SummarySource, SummaryOptions], SummaryResult]
SummaryResultLoader = Callable[[str], SummaryResult | None]


class _SummaryWorkerSignals(QObject):
    completed = Signal(int, object)
    failed = Signal(int)


class _SummaryWorker(QRunnable):
    def __init__(
        self,
        token: int,
        generator: SummaryGenerator,
        source: SummarySource,
        options: SummaryOptions,
    ) -> None:
        super().__init__()
        self.setAutoDelete(False)
        self.token = token
        self.generator = generator
        self.source = source
        self.options = options
        self.signals = _SummaryWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.generator(self.source, self.options)
        except Exception:
            self.signals.failed.emit(self.token)
            return

        self.signals.completed.emit(self.token, result)


class SummaryPanel(QFrame):
    """Asynchronous summary controls that never replace the article body."""

    settings_requested = Signal()
    generation_completed = Signal(object)
    generation_failed = Signal()

    _LANGUAGES = (
        ("summary.language.same", "Same as source"),
        ("summary.language.zh_cn", "Simplified Chinese"),
        ("summary.language.en_us", "English"),
    )
    _DETAILS = (
        ("summary.detail.brief", SummaryDetail.BRIEF),
        ("summary.detail.standard", SummaryDetail.STANDARD),
        ("summary.detail.detailed", SummaryDetail.DETAILED),
    )
    _ERROR_KEYS = {
        SummaryErrorCode.INVALID_INPUT: "summary.error.invalid_input",
        SummaryErrorCode.PROVIDER_NOT_CONFIGURED: (
            "summary.error.provider_not_configured"
        ),
        SummaryErrorCode.PROVIDER_FAILURE: "summary.error.provider_failure",
        SummaryErrorCode.EMPTY_RESPONSE: "summary.error.empty_response",
        SummaryErrorCode.STORAGE_FAILURE: "summary.status.storage_warning",
    }

    def __init__(
        self,
        translator: Translator,
        generator: SummaryGenerator | None = None,
        result_loader: SummaryResultLoader | None = None,
        thread_pool: QThreadPool | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("SummaryPanel")
        self._translator = translator
        self._generator = generator
        self._result_loader = result_loader
        self._thread_pool = thread_pool or QThreadPool(self)
        self._current_source: SummarySource | None = None
        self._displayed_result: SummaryResult | None = None
        self._result_cache: dict[str, SummaryResult] = {}
        self._workers: dict[int, _SummaryWorker] = {}
        self._generation_token = 0
        self._active_token = 0
        self._is_running = False
        self._state = "no_article"
        self._last_error_code: SummaryErrorCode | None = None

        self.language_label = QLabel()
        self.language_label.setObjectName("SummaryFieldLabel")
        self.language_combo = QComboBox()
        self.language_combo.setObjectName("SummaryControl")

        self.detail_label = QLabel()
        self.detail_label.setObjectName("SummaryFieldLabel")
        self.detail_combo = QComboBox()
        self.detail_combo.setObjectName("SummaryControl")

        self.prompt_label = QLabel()
        self.prompt_label.setObjectName("SummaryFieldLabel")
        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setObjectName("SummaryPrompt")
        self.prompt_edit.setFixedHeight(58)

        self.generate_button = QPushButton()
        self.generate_button.setObjectName("SummaryActionButton")
        self.generate_button.clicked.connect(self.generate_summary)

        self.configure_button = QPushButton()
        self.configure_button.setObjectName("SummarySecondaryButton")
        self.configure_button.clicked.connect(self.settings_requested.emit)

        self.status_label = QLabel()
        self.status_label.setObjectName("SummaryStatus")
        self.status_label.setWordWrap(True)

        self.timestamp_label = QLabel()
        self.timestamp_label.setObjectName("SummaryTimestamp")

        self.summary_content = QPlainTextEdit()
        self.summary_content.setObjectName("SummaryContent")
        self.summary_content.setReadOnly(True)
        self.summary_content.setMinimumHeight(90)

        controls_layout = QGridLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setHorizontalSpacing(8)
        controls_layout.setVerticalSpacing(6)
        controls_layout.addWidget(self.language_label, 0, 0)
        controls_layout.addWidget(self.language_combo, 0, 1)
        controls_layout.addWidget(self.detail_label, 0, 2)
        controls_layout.addWidget(self.detail_combo, 0, 3)
        controls_layout.addWidget(self.prompt_label, 1, 0)
        controls_layout.addWidget(self.prompt_edit, 1, 1, 1, 3)
        controls_layout.setColumnStretch(1, 1)
        controls_layout.setColumnStretch(3, 1)

        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)
        action_layout.addWidget(self.generate_button)
        action_layout.addWidget(self.configure_button)
        action_layout.addWidget(self.status_label, 1)
        action_layout.addWidget(self.timestamp_label)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        layout.addLayout(controls_layout)
        layout.addLayout(action_layout)
        layout.addWidget(self.summary_content)

        self.set_translator(translator)
        self.clear_article()

    @property
    def current_article_id(self) -> str | None:
        if self._current_source is None:
            return None

        return self._current_source.article_id

    @property
    def is_running(self) -> bool:
        return self._is_running

    def set_article(self, source: SummarySource) -> None:
        self._invalidate_active_generation()
        self._current_source = source
        self._last_error_code = None

        result = self._result_cache.get(source.article_id)
        if result is None and self._result_loader is not None:
            try:
                result = self._result_loader(source.article_id)
            except Exception:
                self._displayed_result = None
                self.summary_content.clear()
                self._state = "load_failed"
                self._render_state()
                return

        if result is not None and result.has_summary:
            self._result_cache[source.article_id] = result
            self._show_result(result)
            return

        self._displayed_result = None
        self.summary_content.clear()
        self._state = "ready" if self._generator is not None else "unavailable"
        self._render_state()

    def clear_article(self) -> None:
        self._invalidate_active_generation()
        self._current_source = None
        self._displayed_result = None
        self._last_error_code = None
        self._state = "no_article"
        self.summary_content.clear()
        self._render_state()

    def set_translator(self, translator: Translator) -> None:
        self._translator = translator
        self.language_label.setText(translator.text("summary.language"))
        self.detail_label.setText(translator.text("summary.detail"))
        self.prompt_label.setText(translator.text("summary.custom_prompt"))
        self.prompt_edit.setPlaceholderText(
            translator.text("summary.custom_prompt_placeholder")
        )
        self.summary_content.setPlaceholderText(
            translator.text("summary.content_placeholder")
        )
        self.configure_button.setText(
            translator.text("summary.configure_ai")
        )

        self._replace_combo_items(
            self.language_combo,
            [
                (translator.text(label_key), value)
                for label_key, value in self._LANGUAGES
            ],
            default_value="Same as source",
        )
        self._replace_combo_items(
            self.detail_combo,
            [
                (translator.text(label_key), detail.value)
                for label_key, detail in self._DETAILS
            ],
            default_value=SummaryDetail.STANDARD.value,
        )
        self._render_state()

    @Slot()
    def generate_summary(self) -> None:
        if (
            self._current_source is None
            or self._generator is None
            or self._is_running
        ):
            return

        options = SummaryOptions(
            language=str(self.language_combo.currentData()),
            detail_level=SummaryDetail(
                str(self.detail_combo.currentData())
            ),
            custom_prompt=self.prompt_edit.toPlainText(),
        )
        self._generation_token += 1
        token = self._generation_token
        self._active_token = token
        self._is_running = True
        self._state = "running"
        self._render_state()

        worker = _SummaryWorker(
            token,
            self._generator,
            self._current_source,
            options,
        )
        worker.signals.completed.connect(self._handle_completed)
        worker.signals.failed.connect(self._handle_failed)
        self._workers[token] = worker
        self._thread_pool.start(worker)

    @Slot(int, object)
    def _handle_completed(self, token: int, value: object) -> None:
        self._workers.pop(token, None)

        if token != self._active_token or self._current_source is None:
            return

        self._is_running = False
        if not isinstance(value, SummaryResult):
            self._state = "unexpected_failure"
            self._render_state()
            self.generation_failed.emit()
            return

        result = value
        if result.article_id != self._current_source.article_id:
            self._state = "unexpected_failure"
            self._render_state()
            self.generation_failed.emit()
            return

        if result.has_summary:
            self._result_cache[result.article_id] = result
            self._show_result(result)
        else:
            self._last_error_code = result.error_code
            self._state = "result_failure"
            self._render_state()

        self.generation_completed.emit(result)

    @Slot(int)
    def _handle_failed(self, token: int) -> None:
        self._workers.pop(token, None)

        if token != self._active_token or self._current_source is None:
            return

        self._is_running = False
        self._last_error_code = None
        self._state = "unexpected_failure"
        self._render_state()
        self.generation_failed.emit()

    def _show_result(self, result: SummaryResult) -> None:
        self._displayed_result = result
        self.summary_content.setPlainText(result.text)
        self._last_error_code = result.error_code
        self._state = (
            "storage_warning"
            if result.status is SummaryStatus.GENERATED_NOT_SAVED
            else "generated"
        )
        self._render_state()

    def _render_state(self) -> None:
        state_keys = {
            "no_article": "summary.status.no_article",
            "unavailable": "summary.status.unavailable",
            "ready": "summary.status.ready",
            "running": "summary.status.running",
            "generated": "summary.status.generated",
            "storage_warning": "summary.status.storage_warning",
            "load_failed": "summary.error.load_failed",
            "unexpected_failure": "summary.error.unexpected",
        }

        if self._state == "result_failure":
            key = self._ERROR_KEYS.get(
                self._last_error_code,
                "summary.error.unexpected",
            )
        else:
            key = state_keys.get(self._state, "summary.error.unexpected")

        self.status_label.setText(self._translator.text(key))
        self.generate_button.setText(
            self._translator.text(
                "summary.regenerate"
                if self._displayed_result is not None
                else "summary.generate"
            )
        )
        self.generate_button.setEnabled(
            self._current_source is not None
            and self._generator is not None
            and not self._is_running
        )

        if self._displayed_result is None:
            self.timestamp_label.clear()
            return

        generated_at = self._displayed_result.generated_at.astimezone()
        self.timestamp_label.setText(
            self._translator.text("summary.generated_at").format(
                time=generated_at.strftime("%Y-%m-%d %H:%M"),
            )
        )

    def _replace_combo_items(
        self,
        combo: QComboBox,
        items: list[tuple[str, str]],
        default_value: str,
    ) -> None:
        current_data = combo.currentData()
        selected_data = (
            str(current_data)
            if current_data is not None
            else default_value
        )
        combo.clear()

        for label, value in items:
            combo.addItem(label, value)

        index = combo.findData(selected_data)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _invalidate_active_generation(self) -> None:
        self._generation_token += 1
        self._active_token = self._generation_token
        self._is_running = False
