from dataclasses import dataclass
from typing import Protocol


MIN_FONT_SIZE = 12
MAX_FONT_SIZE = 32
MIN_LINE_HEIGHT = 1.2
MAX_LINE_HEIGHT = 2.4
MIN_CONTENT_WIDTH = 480
MAX_CONTENT_WIDTH = 1200


@dataclass(frozen=True, slots=True)
class ReaderStyle:
    """Presentation-only reader settings owned by the UI layer."""

    font_size: int = 18
    line_height: float = 1.6
    content_width: int = 820

    def normalized(self) -> "ReaderStyle":
        return ReaderStyle(
            font_size=min(max(self.font_size, MIN_FONT_SIZE), MAX_FONT_SIZE),
            line_height=round(
                min(max(self.line_height, MIN_LINE_HEIGHT), MAX_LINE_HEIGHT),
                2,
            ),
            content_width=min(
                max(self.content_width, MIN_CONTENT_WIDTH),
                MAX_CONTENT_WIDTH,
            ),
        )


class ReaderStyleStore(Protocol):
    """Injection point for Member A's future local settings repository."""

    def load(self) -> ReaderStyle:
        ...

    def save(self, style: ReaderStyle) -> None:
        ...


class InMemoryReaderStyleStore:
    """Offline UI-development store; it performs no file or network I/O."""

    def __init__(self, initial_style: ReaderStyle | None = None) -> None:
        self._style = (initial_style or ReaderStyle()).normalized()

    def load(self) -> ReaderStyle:
        return self._style

    def save(self, style: ReaderStyle) -> None:
        self._style = style.normalized()
