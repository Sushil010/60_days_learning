import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QGuiApplication, QTextCursor   
OVERLAY_WIDTH = 520
OVERLAY_HEIGHT = 400
OVERLAY_CORNER_RADIUS = 16
HOTKEY = os.getenv("HOTKEY", "ctrl+space")

class OverlayWindow(QWidget):
    token_received = Signal(str)
    stream_finished = Signal()         
    stream_error = Signal(str)          

    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(OVERLAY_WIDTH, OVERLAY_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        self.context_label = QLabel("Ready")
        self.response_view = QTextBrowser()

        self.response_view.setStyleSheet(
            "background: transparent; " \
            "color: white; " \
            "border: none;"
            )
        layout.addWidget(self.context_label)

        layout.addWidget(self.response_view)

        self.token_received.connect(self._append_token)
        self.stream_finished.connect(self._on_stream_done)     
        self.stream_error.connect(self._on_error)               

    def show_at(self, x: int, y: int, text: str = ""):
        screen = QGuiApplication.primaryScreen().geometry()
        if x + OVERLAY_WIDTH > screen.right():
            x -= OVERLAY_WIDTH
        if y + OVERLAY_HEIGHT > screen.bottom():
            y -= OVERLAY_HEIGHT
        self.move(x, y)

        if text:
            self.context_label.setText(text)
        self.show()
        self.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(),
                             OVERLAY_CORNER_RADIUS, OVERLAY_CORNER_RADIUS)
        painter.fillPath(path, QColor(18, 18, 24, 224))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.hide()
        super().keyPressEvent(event)

    def _append_token(self, token: str):
        cursor = self.response_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(token)
        self.response_view.setTextCursor(cursor)

    def _on_stream_done(self):         
        self.context_label.setText("Done — press Esc to dismiss")

    def _on_error(self, msg: str):     
        self.response_view.setPlainText(f"Error: {msg}")