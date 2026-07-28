from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap


MENU_ICON_COLOR = QColor("#4d9df6")


def menu_icon(name: str) -> QIcon:
    """Return a small, dependency-free icon for a main menu."""
    pixmap = QPixmap(18, 18)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(MENU_ICON_COLOR, 1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)

    drawers = {
        "file": _draw_file,
        "settings": _draw_settings,
        "view": _draw_view,
        "help": _draw_help,
    }
    try:
        drawers[name](painter)
    except KeyError as error:
        painter.end()
        raise ValueError(f"Unknown menu icon: {name}") from error

    painter.end()
    return QIcon(pixmap)


def _draw_file(painter: QPainter) -> None:
    folder = QPainterPath()
    folder.moveTo(2.5, 5.0)
    folder.lineTo(7.0, 5.0)
    folder.lineTo(8.5, 7.0)
    folder.lineTo(15.5, 7.0)
    folder.lineTo(15.5, 14.5)
    folder.lineTo(2.5, 14.5)
    folder.closeSubpath()
    painter.drawPath(folder)
    painter.drawLine(QPointF(2.5, 7.0), QPointF(8.5, 7.0))


def _draw_settings(painter: QPainter) -> None:
    controls = ((5.5, 4.5), (11.5, 9.0), (7.5, 13.5))
    for control_x, line_y in controls:
        painter.drawLine(QPointF(2.5, line_y), QPointF(15.5, line_y))
        painter.setBrush(MENU_ICON_COLOR)
        painter.drawEllipse(QPointF(control_x, line_y), 1.6, 1.6)
        painter.setBrush(Qt.BrushStyle.NoBrush)


def _draw_view(painter: QPainter) -> None:
    eye = QPainterPath()
    eye.moveTo(2.0, 9.0)
    eye.cubicTo(5.0, 4.5, 13.0, 4.5, 16.0, 9.0)
    eye.cubicTo(13.0, 13.5, 5.0, 13.5, 2.0, 9.0)
    painter.drawPath(eye)
    painter.setBrush(MENU_ICON_COLOR)
    painter.drawEllipse(QPointF(9.0, 9.0), 2.0, 2.0)


def _draw_help(painter: QPainter) -> None:
    painter.drawEllipse(QRectF(2.5, 2.5, 13.0, 13.0))
    question = QPainterPath()
    question.moveTo(6.6, 6.6)
    question.cubicTo(6.9, 4.7, 11.5, 4.8, 11.5, 7.0)
    question.cubicTo(11.5, 8.5, 9.0, 8.5, 9.0, 10.5)
    painter.drawPath(question)
    painter.setBrush(MENU_ICON_COLOR)
    painter.drawEllipse(QPointF(9.0, 13.0), 0.8, 0.8)
