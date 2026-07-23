import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QGuiApplication, QTextCursor   
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QPushButton,QLineEdit  
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
        self.button_row = QHBoxLayout() 
        self.stop_button = QPushButton("Stop")                     
        self.stop_button.setStyleSheet(
            "background: rgba(239,68,68,0.3); color: white; border: none; "
            "border-radius: 6px; padding: 4px 10px; font-size: 11px;"
        )
        self.stop_button.clicked.connect(self._on_stop_clicked)       
        self.stop_button.hide()                                       

        self.followup_input = QLineEdit()                            
        self.followup_input.setPlaceholderText("Ask a follow-up... (Enter to send)")
        self.followup_input.setStyleSheet(
            "background: rgba(255,255,255,0.08); color: white; border: none; "
            "border-radius: 6px; padding: 6px; font-size: 12px;"
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
        self.response_view = QTextBrowser()

        self.response_view.setStyleSheet(
            "background: transparent; " \
            "color: white; " \
            "border: none;"
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
            btn.setStyleSheet(
                "background: rgba(124,58,237,0.3); color: white; "
                "border: none; border-radius: 6px; padding: 4px 10px; font-size: 11px;"
            )
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