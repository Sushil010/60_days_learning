import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QPushButton, QLineEdit
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QGuiApplication, QTextCursor, QLinearGradient, QPen, QBrush

OVERLAY_WIDTH = 520
OVERLAY_HEIGHT = 400
OVERLAY_CORNER_RADIUS = 16
HOTKEY = os.getenv("HOTKEY", "ctrl+space")

BUTTON_STYLE = """
QPushButton {
    background: rgba(124, 58, 237, 0.25);
    color: white;
    border: 1px solid rgba(124, 58, 237, 0.4);
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 500;
}
QPushButton:hover {
    background: rgba(124, 58, 237, 0.45);
}
QPushButton:pressed {
    background: rgba(124, 58, 237, 0.6);
}
"""

STOP_BUTTON_STYLE = """
QPushButton {
    background: rgba(239, 68, 68, 0.25);
    color: white;
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 11px;
}
QPushButton:hover {
    background: rgba(239, 68, 68, 0.45);
}
"""


class OverlayWindow(QWidget):
    token_received = Signal(str)
    stream_finished = Signal()
    stream_error = Signal(str)

    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.button_row = QHBoxLayout()

        self.stop_button = QPushButton("✕ Stop")
        self.stop_button.setStyleSheet(STOP_BUTTON_STYLE)          
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.hide()

        self.followup_input = QLineEdit()
        self.followup_input.setPlaceholderText("Ask a follow-up... (Enter to send)")
        self.followup_input.setStyleSheet(                          
            "QLineEdit { background: rgba(255,255,255,0.06); color: white; "
            "border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; "
            "padding: 8px 10px; font-size: 12px; } "
            "QLineEdit:focus { border: 1px solid rgba(124,58,237,0.6); }"
        )
        self.followup_input.returnPressed.connect(self._on_followup_submitted)
        self.followup_input.hide()

        self.current_task = None
        self.on_followup = None

        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(OVERLAY_WIDTH, OVERLAY_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.followup_input)

        self.context_label = QLabel("Ready")
        self.context_label.setStyleSheet(                           
            "color: rgba(196, 165, 255, 0.95); font-size: 11px; font-weight: 600; "
            "letter-spacing: 0.5px; padding-bottom: 4px;"
        )

        self.response_view = QTextBrowser()
        self.response_view.setStyleSheet(                           
            "QTextBrowser { background: transparent; color: rgba(255,255,255,0.92); "
            "border: none; font-size: 13px; font-family: 'Segoe UI', sans-serif; "
            "line-height: 1.5; padding: 4px 0px; } "
            "QScrollBar:vertical { width: 4px; background: transparent; } "
            "QScrollBar::handle:vertical { background: rgba(255,255,255,0.2); border-radius: 2px; }"
        )

        layout.addWidget(self.context_label)
        layout.addWidget(self.response_view)
        layout.addLayout(self.button_row)

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

        self.followup_input.hide()
        self.stop_button.show()
        self.show()
        self.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(),
                             OVERLAY_CORNER_RADIUS, OVERLAY_CORNER_RADIUS)

        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(28, 22, 42, 235))
        gradient.setColorAt(1, QColor(15, 15, 22, 235))
        painter.fillPath(path, gradient)

        # Thin gradient border for a subtle "glass edge" look
        border_gradient = QLinearGradient(0, 0, self.width(), self.height())
        border_gradient.setColorAt(0, QColor(124, 58, 237, 120))
        border_gradient.setColorAt(1, QColor(59, 130, 246, 60))
        pen = QPen(QBrush(border_gradient), 1.2)
        painter.setPen(pen)
        painter.drawPath(path)

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
        self.context_label.setText("Done press Esc to dismiss")
        self.stop_button.hide()
        self.followup_input.show()

    def _on_error(self, msg: str):
        self.response_view.setPlainText(f"Error: {msg}")

    def set_action_buttons(self, entities):
        while self.button_row.count():
            item = self.button_row.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for entity in entities:
            btn = QPushButton(entity.label)
            btn.setStyleSheet(BUTTON_STYLE)          
            btn.clicked.connect(lambda checked=False, e=entity: self._handle_action(e))
            self.button_row.addWidget(btn)

    def _handle_action(self, entity):
        import webbrowser
        import pyperclip

        if entity.kind == "url":
            webbrowser.open(entity.value)
        elif entity.kind in ("code", "list"):
            pyperclip.copy(entity.value)
            self.context_label.setText("Copied to clipboard!")

    def _on_stop_clicked(self):
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
        self.stop_button.hide()
        self.context_label.setText("Cancelled — press Esc to dismiss")

    def _on_followup_submitted(self):
        text = self.followup_input.text().strip()
        if text and self.on_followup:
            self.followup_input.clear()
            self.on_followup(text)