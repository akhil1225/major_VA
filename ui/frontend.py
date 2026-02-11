import sys

from PySide6.QtWidgets import (  # type: ignore
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QFileDialog,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QGraphicsOpacityEffect
    
)
from PySide6.QtCore import (  # type: ignore
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    Signal
)
from PySide6.QtGui import QFont  # type: ignore

from core.assistant_controller import AssistantController
from core.speech_engine import toggle_mute, stop_speaking, replay_last



# css for widgetting


class _Bar(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(6)
        self.setMinimumHeight(8)
        self.setMaximumHeight(8)
        self.setStyleSheet(
            """
            background-color: #333;
            border-radius: 3px;
            """
        )


class VisualizerWidget(QWidget):
    """
    Animated voice visualizer.
    - Idle: subtle static bars
    - Speaking: animated wave bars
    """

    def __init__(self):
        super().__init__()
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)

        self.bars = [_Bar() for _ in range(5)]
        for bar in self.bars:
            layout.addWidget(bar)

        self._animations: list[QParallelAnimationGroup] = []
        self._active = False
        self._build_animations()

    def _build_animations(self):
        base_heights = [8, 14, 22, 14, 8]
        for i, bar in enumerate(self.bars):
            group = QParallelAnimationGroup(self)
            min_anim = QPropertyAnimation(bar, b"minimumHeight")
            max_anim = QPropertyAnimation(bar, b"maximumHeight")

            for anim in (min_anim, max_anim):
                anim.setDuration(420 + i * 40)
                anim.setStartValue(base_heights[i])
                anim.setEndValue(base_heights[i] + 24)
                anim.setEasingCurve(QEasingCurve.InOutSine)
                anim.setLoopCount(-1)

            group.addAnimation(min_anim)
            group.addAnimation(max_anim)
            self._animations.append(group)

    def start(self):
        if self._active:
            return
        self._active = True

        colors = [
            "#ff5252",  # red
            "#ffb000",  # orange
            "#00c853",  # green
            "#40c4ff",  # light blue
            "#7c4dff",  # purple
        ]

        for bar, color in zip(self.bars, colors):
            bar.setStyleSheet(f"""
                background-color: {color};
                border-radius: 3px;
            """)

        for group in self._animations:
            group.start()

    def stop(self):
        self._active = False
        for group in self._animations:
            group.stop()
        for bar in self.bars:
            bar.setMinimumHeight(8)
            bar.setMaximumHeight(8)
            bar.setStyleSheet("""
                background-color: #333;
                border-radius: 3px;
            """)


#bubbles in chat

class ChatBubble(QFrame):
    def __init__(self, text: str, is_user: bool):
        super().__init__()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        label.setMaximumWidth(
            self.parentWidget().width() * 0.7 if self.parentWidget() else 480
        )

        if is_user:
            label.setStyleSheet("""
                QLabel {
                    background-color: #0078d4;
                    color: white;
                    padding: 10px 14px;
                    border-radius: 8px;
                    font-size: 13px;
                }
                QLabel:hover {
                    background-color: #1490ff;
                }
                QLabel:pressed {
                    background-color: #005a9e;
                }
            """)
            layout.addStretch()
            layout.addWidget(label)
        else:
            label.setStyleSheet("""
                QLabel {
                    background-color: #2b2b2b;
                    color: #eaeaea;
                    padding: 10px 14px;
                    border-radius: 8px;
                    font-size: 13px;
                    border: 1px solid #3a3a3a;
                }
                QLabel:hover {
                    border-color: #4a8cff;
                }
            """)
            layout.addWidget(label)
            layout.addStretch()


# main window class

class OrbitOS(QWidget):
    voiceResult = Signal(str, str)
    def __init__(self):
        super().__init__()

       
        self.controller = AssistantController()


        # Connect controller's Qt signal to our own signal
        self.controller.bridge.voiceResult.connect(
            lambda heard, reply: self.voiceResult.emit(heard, reply)
        )

        # self.voiceResult.connect(self._on_voice_result)


       
        self.controller.on_state_change = lambda s: self.ui_safe(
            lambda: self.on_state_change(s)
        )
        # self.controller.on_speaking_start = lambda: self.ui_safe(
        #     self.visualizer.start
        # )
        # self.controller.on_speaking_end = lambda: self.ui_safe(
        #     self.visualizer.stop
        # )
        self.controller.on_directory_change = lambda: self.ui_safe(
            self._update_directory
        )
        
        self.controller.on_message = (
            lambda text: self.ui_safe(lambda: self.add_assistant_message(text))
        )

        self.voiceResult.connect(self._on_voice_result)

        self.ui_safe(self._update_directory)

       
        self.setWindowTitle("OrbitOS – Intelligent System Agent")
        self.resize(720, 720)
        self.setMinimumSize(460, 620)

        #css for global window
        self.setStyleSheet(
            """
            QWidget {
                background-color: #121212;
                color: #eaeaea;
                font-family: Segoe UI;
            }

            QPushButton {
                background-color: #1f1f1f;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 12px;
            }

            QPushButton:hover {
                background-color: #2a2a2a;
                border-color: #0078d4;
            }

            QLineEdit {
                background-color: #1c1c1c;
                border: 1px solid #333;
                border-radius: 18px;
                padding: 10px 14px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border-color: #0078d4;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 8px;
            }

            QScrollBar::handle:vertical {
                background: #3a3a3a;
                border-radius: 4px;
                min-height: 30px;
            }

            QScrollBar::handle:vertical:hover {
                background: #0078d4;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
            """
        )

        self._build_ui()
        self.ui_safe(self._update_directory)
        self.on_state_change("idle")

   

    def ui_safe(self, fn):
        QTimer.singleShot(0, fn)


    def _on_voice_result(self, heard: str, reply: str):

        if not heard:
            self.add_user_message("[Voice] Could not understand.")
        else:
            self.add_user_message(f"[Voice] {heard}")

        if reply:
            self.add_assistant_message(reply)


    def _pulse_visualizer(self, duration_ms: int = 1800):
        # start immediately
        self.visualizer.start()
        # stop after duration_ms
        QTimer.singleShot(duration_ms, self.visualizer.stop)




    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        title = QLabel("OrbitOS")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet("color: #0078d4;")

        self.status = QLabel("Listening for wake word…")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("font-size: 11px; color: #888;")

        self.visualizer = VisualizerWidget()

        root.addWidget(title)
        root.addWidget(self.status)
        root.addWidget(self.visualizer, 0, Qt.AlignCenter)

        # ---------------- Chat Area ----------------
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")

        self.chat_host = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_host)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()

        self.scroll.setWidget(self.chat_host)
        root.addWidget(self.scroll, 1)

        # ---------------- Toolbar ----------------
        toolbar = QHBoxLayout()
        self.mute_btn = QPushButton("🔇 Mute")
        stop_btn = QPushButton("⏹ Stop")
        replay_btn = QPushButton("🔁 Replay")

        self.mute_btn.clicked.connect(self.toggle_mute)
        stop_btn.clicked.connect(stop_speaking)
        replay_btn.clicked.connect(replay_last)

        toolbar.addWidget(self.mute_btn)
        toolbar.addWidget(stop_btn)
        toolbar.addWidget(replay_btn)
        toolbar.addStretch()

        root.addLayout(toolbar)

        # input box
        input_row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText('Type a command or say "Orbit"…')
        self.input.returnPressed.connect(self.run_text)

        voice_btn = QPushButton("🎤")
        voice_btn.setFixedSize(44, 44)
        voice_btn.clicked.connect(self.run_voice)

        input_row.addWidget(self.input, 1)
        input_row.addWidget(voice_btn)
        root.addLayout(input_row)

        
        footer = QHBoxLayout()
        self.dir_label = QLabel("")
        self.dir_label.setStyleSheet("font-size: 10px; color: #666;")

        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self.browse)

        footer.addWidget(self.dir_label)
        footer.addStretch()
        footer.addWidget(browse_btn)
        root.addLayout(footer)

  

    def add_user_message(self, text: str):
        print(f"🗣️ ADDING VOICE: {text}")  # debug
        self.chat_layout.insertWidget(
            self.chat_layout.count() - 1,
            ChatBubble(text, True),
        )
        QTimer.singleShot(0, self.scroll_to_bottom)

    def add_assistant_message(self, text: str):
        
        self.chat_layout.insertWidget(
            self.chat_layout.count() - 1,
            ChatBubble(text, False),
        )
        QTimer.singleShot(0, self.scroll_to_bottom)

        


    def scroll_to_bottom(self):
        self.chat_host.adjustSize()
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())



    def run_text(self):
        text = self.input.text().strip()
        if not text:
            return

 
        self.add_user_message(f"[Text] {text}")
        self.input.clear()

        self._pulse_visualizer()

      
        result = self.controller.handle_text_command(text)
        if result:
            self.add_assistant_message(result)

    def run_voice(self):
        self.controller.pause_wake_word()
        self._pulse_visualizer()

        def voice_callback(heard, reply):
            print("VOICE CALLBACK RAW:", heard, "||", reply)
            # emit through controller bridge (same as wake word)
            self.controller.bridge.voiceResult.emit(heard or "", reply or "")
            QTimer.singleShot(0, self.controller.resume_wake_word)

        self.controller.handle_voice_command_async(voice_callback)



  

    def on_state_change(self, state: str):
        states = {
            "idle": "Listening for wake word…",
            "wake": "Orbit activated",
            "listening": "Listening…",
            "processing": "Processing…",
        }
        self.status.setText(states.get(state, state))



    def toggle_mute(self):
        muted = toggle_mute()
        self.mute_btn.setText("🔊 Unmute" if muted else "🔇 Mute")

    def browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if path:
            self.controller.set_working_directory(path)
            self.dir_label.setText(
                f"Working Directory: {self.controller.get_working_directory()}"
            )

    def _update_directory(self):
        self.dir_label.setText(
            f"Working Directory: {self.controller.get_working_directory()}"
        )



def launch_ui():
    app = QApplication(sys.argv)
    win = OrbitOS()
    win.show()
    sys.exit(app.exec())
