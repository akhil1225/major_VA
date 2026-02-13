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
    QListWidget,
    QListWidgetItem,
    QMenu,
    QInputDialog,
)
from PySide6.QtCore import (  # type: ignore
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    Signal,
)
from PySide6.QtGui import QFont, QAction  # type: ignore


from core.assistant_controller import AssistantController
from core.speech_engine import toggle_mute, stop_speaking, replay_last


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
            "#ff5252",
            "#ffb000",
            "#00c853",
            "#40c4ff",
            "#7c4dff",
        ]

        for bar, color in zip(self.bars, colors):
            bar.setStyleSheet(
                f"""
                background-color: {color};
                border-radius: 3px;
            """
            )

        for group in self._animations:
            group.start()

    def stop(self):
        self._active = False
        for group in self._animations:
            group.stop()
        for bar in self.bars:
            bar.setMinimumHeight(8)
            bar.setMaximumHeight(8)
            bar.setStyleSheet(
                """
                background-color: #333;
                border-radius: 3px;
            """
            )


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
            label.setStyleSheet(
                """
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
            """
            )
            layout.addStretch()
            layout.addWidget(label)
        else:
            label.setStyleSheet(
                """
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
            """
            )
            layout.addWidget(label)
            layout.addStretch()


class OrbitOS(QWidget):
    voiceResult = Signal(str, str)

    def __init__(self):
        super().__init__()

        self.controller = AssistantController()
        self.current_mode = "assistant"
        self.current_ai_chat_id: str | None = None
        self.sidebar_collapsed = False
        self.sidebar_expanded_width = 220
        self.theme = "dark"

        self.controller.bridge.voiceResult.connect(
            lambda heard, reply: self.voiceResult.emit(heard, reply)
        )

        self.controller.on_state_change = lambda s: self.ui_safe(
            lambda: self.on_state_change(s)
        )
        self.controller.on_directory_change = lambda: self.ui_safe(
            self._update_directory
        )
        self.controller.on_message = (
            lambda text: self.ui_safe(lambda: self.add_assistant_message(text))
        )

        self.voiceResult.connect(self._on_voice_result)

        self.ui_safe(self._update_directory)

        self.setWindowTitle("OrbitOS – Intelligent System Agent")
        self.resize(820, 720)
        self.setMinimumSize(520, 620)

        self._apply_theme()
        self._build_ui()
        self.ui_safe(self._update_directory)
        self.on_state_change("idle")

    # THEME

    def _apply_theme(self):
        if self.theme == "dark":
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

                QWidget#Sidebar {
                    border: 1px solid #333;
                    border-radius: 8px;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                QWidget {
                    background-color: #f5f5f5;
                    color: #222;
                    font-family: Segoe UI;
                }

                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 8px 14px;
                    font-size: 12px;
                }

                QPushButton:hover {
                    background-color: #f0f0f0;
                    border-color: #0078d4;
                }

                QLineEdit {
                    background-color: #ffffff;
                    border: 1px solid #ccc;
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
                    background: #cccccc;
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

                QWidget#Sidebar {
                    border: 1px solid #ccc;
                    border-radius: 8px;
                }
                """
            )

    def _toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self._apply_theme()

    # CORE UI

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
        self.visualizer.start()
        QTimer.singleShot(duration_ms, self.visualizer.stop)

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(10)

        #
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("Sidebar")
        self.sidebar_widget.setMinimumWidth(50)
        self.sidebar_widget.setMaximumWidth(self.sidebar_expanded_width)
        sidebar_layout = QVBoxLayout(self.sidebar_widget)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(10)

        
        self.toggle_sidebar_btn = QPushButton("◀️")
        self.toggle_sidebar_btn.setFixedSize(40, 40)
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)
        self.toggle_sidebar_btn.setToolTip("Collapse/expand sidebar")

        self.assistant_mode_btn = QPushButton("🤖 Assistant")
        self.ai_mode_btn = QPushButton("💡 AI Mode")

        self.assistant_mode_btn.setCheckable(True)
        self.ai_mode_btn.setCheckable(True)
        self.assistant_mode_btn.setChecked(True)

        self.assistant_mode_btn.clicked.connect(lambda: self.set_mode("assistant"))
        self.ai_mode_btn.clicked.connect(lambda: self.set_mode("ai"))

        sidebar_layout.addWidget(self.toggle_sidebar_btn, alignment=Qt.AlignLeft)
        sidebar_layout.addWidget(self.assistant_mode_btn)
        sidebar_layout.addWidget(self.ai_mode_btn)
        sidebar_layout.addStretch()

        root.addWidget(self.sidebar_widget, 0)

        
        main_col = QVBoxLayout()
        main_col.setContentsMargins(0, 0, 0, 0)
        main_col.setSpacing(10)

     
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(8)

        self.title_label = QLabel("OrbitOS")
        self.title_label.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.title_label.setStyleSheet("color: #0078d4;")

        self.status = QLabel("Listening for wake word…")
        self.status.setStyleSheet("font-size: 11px; color: #888;")

        top_bar_left = QVBoxLayout()
        top_bar_left.setContentsMargins(0, 0, 0, 0)
        top_bar_left.setSpacing(2)
        top_bar_left.addWidget(self.title_label)
        top_bar_left.addWidget(self.status)

        top_bar_left_widget = QWidget()
        top_bar_left_widget.setLayout(top_bar_left)

        top_bar.addWidget(top_bar_left_widget)
        top_bar.addStretch()

      
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.setFixedSize(100, 32)
        self.settings_btn.setToolTip("⚙️ Settings")
        self.settings_btn.clicked.connect(self._show_settings_menu)
        top_bar.addWidget(self.settings_btn)

        main_col.addLayout(top_bar)

       
        self.main = QVBoxLayout()
        self.main.setContentsMargins(0, 0, 0, 0)
        self.main.setSpacing(14)
        main_col.addLayout(self.main, 1)

        root.addLayout(main_col, 1)

       
        self.assistant_container = QWidget()
        assistant_layout = QVBoxLayout(self.assistant_container)
        assistant_layout.setContentsMargins(0, 0, 0, 0)
        assistant_layout.setSpacing(14)

        self.visualizer = VisualizerWidget()
        assistant_layout.addWidget(self.visualizer, 0, Qt.AlignCenter)

    
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none;")

        self.chat_host = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_host)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()

        self.scroll.setWidget(self.chat_host)
        assistant_layout.addWidget(self.scroll, 1)

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
        assistant_layout.addLayout(toolbar)

     
        assistant_input_row = QHBoxLayout()
        self.assistant_input = QLineEdit()
        self.assistant_input.setPlaceholderText('⌨️ Type a command or say "Orbit"…')
        self.assistant_input.returnPressed.connect(self.on_enter_pressed)

        assistant_voice_btn = QPushButton("🎤 Voice")
        assistant_voice_btn.setFixedSize(90, 32)
        assistant_voice_btn.clicked.connect(self.run_voice)

        assistant_input_row.addWidget(self.assistant_input, 1)
        assistant_input_row.addWidget(assistant_voice_btn)
        assistant_layout.addLayout(assistant_input_row)

  
        footer = QHBoxLayout()
        self.dir_label = QLabel("")
        self.dir_label.setStyleSheet("font-size: 10px; color: #666;")

        browse_btn = QPushButton("📁 Browse")
        browse_btn.clicked.connect(self.browse)

        footer.addWidget(self.dir_label)
        footer.addStretch()
        footer.addWidget(browse_btn)
        assistant_layout.addLayout(footer)

        self.main.addWidget(self.assistant_container)

   
        self.ai_container_widget = QWidget()
        ai_outer = QVBoxLayout(self.ai_container_widget)
        ai_outer.setContentsMargins(0, 0, 0, 0)
        ai_outer.setSpacing(8)

  
        ai_header = QHBoxLayout()
        ai_header.setContentsMargins(0, 0, 0, 0)
        ai_header.setSpacing(6)

        ai_title = QLabel("🤖 AI Chat")
        ai_title.setFont(QFont("Segoe UI", 16, QFont.Bold))

        ai_subtitle = QLabel("Ask anything, keep multiple chats, rename and manage them.")
        ai_subtitle.setStyleSheet("font-size: 11px; color: #888;")

        ai_header_text_layout = QVBoxLayout()
        ai_header_text_layout.setContentsMargins(0, 0, 0, 0)
        ai_header_text_layout.setSpacing(2)
        ai_header_text_layout.addWidget(ai_title)
        ai_header_text_layout.addWidget(ai_subtitle)

        ai_header_text_widget = QWidget()
        ai_header_text_widget.setLayout(ai_header_text_layout)

        ai_header.addWidget(ai_header_text_widget)
        ai_header.addStretch()

        ai_outer.addLayout(ai_header)

        ai_root = QHBoxLayout()
        ai_root.setContentsMargins(0, 0, 0, 0)
        ai_root.setSpacing(8)

    
        self.ai_sidebar = QListWidget()
        self.ai_sidebar.setFixedWidth(220)
        self.ai_sidebar.itemClicked.connect(self._on_ai_chat_selected)
        self.ai_sidebar.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ai_sidebar.customContextMenuRequested.connect(
            self._on_ai_sidebar_context_menu
        )

        self.ai_new_chat_btn = QPushButton("➕ New Chat")

        self.ai_new_chat_btn.clicked.connect(self._create_new_ai_chat)

        ai_left_layout = QVBoxLayout()
        ai_left_layout.setContentsMargins(0, 0, 0, 0)
        ai_left_layout.setSpacing(6)

        ai_chats_label = QLabel("📜 Chats")
        ai_chats_label.setStyleSheet("font-size: 11px; color: #888;")

        ai_left_layout.addWidget(ai_chats_label)
        ai_left_layout.addWidget(self.ai_new_chat_btn)
        ai_left_layout.addWidget(self.ai_sidebar)

        ai_left_widget = QWidget()
        ai_left_widget.setLayout(ai_left_layout)


        self.ai_scroll = QScrollArea()
        self.ai_scroll.setWidgetResizable(True)
        self.ai_scroll.setStyleSheet("border: none;")

        self.ai_chat_host = QWidget()
        self.ai_chat_layout = QVBoxLayout(self.ai_chat_host)
        self.ai_chat_layout.setSpacing(8)
        self.ai_chat_layout.addStretch()

        self.ai_scroll.setWidget(self.ai_chat_host)

        ai_root.addWidget(ai_left_widget)
        ai_root.addWidget(self.ai_scroll, 1)

     
        ai_input_row = QHBoxLayout()
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("💬 Ask anything…")
        self.ai_input.returnPressed.connect(self.send_ai_message)

        self.ai_send_btn = QPushButton("📨 Send")
        self.ai_send_btn.setFixedHeight(32)
        self.ai_send_btn.clicked.connect(self.send_ai_message)

        ai_input_row.addWidget(self.ai_input, 1)
        ai_input_row.addWidget(self.ai_send_btn)

        ai_outer.addLayout(ai_root, 1)
        ai_outer.addLayout(ai_input_row)

        self.main.addWidget(self.ai_container_widget)
        self.ai_container_widget.hide()

        
        self.sidebar_anim = QPropertyAnimation(self.sidebar_widget, b"maximumWidth")
        self.sidebar_anim.setDuration(220)
        self.sidebar_anim.setEasingCurve(QEasingCurve.InOutCubic)

   

    def add_user_message(self, text: str):
        print(f"🗣️ ADDING VOICE: {text}")
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

    def on_enter_pressed(self):
        text = self.assistant_input.text().strip()
        if not text:
            return
        if self.current_mode == "assistant":
            self.run_text()
        else:
            return

    def run_text(self):
        text = self.assistant_input.text().strip()
        if not text:
            return
        self.add_user_message(f"[Text] {text}")
        self.assistant_input.clear()
        self._pulse_visualizer()
        result = self.controller.handle_text_command(text)
        if result:
            self.add_assistant_message(result)

    def send_ai_message(self):
        text = self.ai_input.text().strip()
        if not text:
            return
        self.ai_input.clear()
        self.run_ai_text_with_text(text)

    def run_ai_text_with_text(self, text: str):
        if not self.current_ai_chat_id:
            self._create_new_ai_chat()
        assert self.current_ai_chat_id is not None
        chat_id = self.current_ai_chat_id
        self._add_ai_message(text, is_user=True)
        reply = self.controller.run_ai_chat(chat_id, text, model=None)
        self._add_ai_message(reply, is_user=False)

    def run_ai_text(self):
        text = self.ai_input.text().strip()
        if not text:
            return
        self.ai_input.clear()
        self.run_ai_text_with_text(text)

    def run_voice(self):
        if self.current_mode == "ai":
            self.controller.pause_wake_word()
            self._pulse_visualizer()

            def voice_callback(heard, reply):
                if heard:
                    self.set_mode("ai")
                    self.ai_input.setText(heard)
                    self.send_ai_message()
                QTimer.singleShot(0, self.controller.resume_wake_word)

            self.controller.handle_voice_command_async(voice_callback)
            return

        self.controller.pause_wake_word()
        self._pulse_visualizer()

        def voice_callback(heard, reply):
            print("VOICE CALLBACK RAW:", heard, "||", reply)
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

    def _show_settings_menu(self):
        menu = QMenu(self)

        theme_action = QAction(
            "Switch to Light Mode" if self.theme == "dark" else "Switch to Dark Mode",
            self,
        )
        theme_action.triggered.connect(self._toggle_theme)

        llm_action = QAction("LLM Settings (coming soon)", self)
        llm_action.setEnabled(False)

        menu.addAction(theme_action)
        menu.addSeparator()
        menu.addAction(llm_action)

        menu.exec_(self.settings_btn.mapToGlobal(self.settings_btn.rect().bottomRight()))

   

    def toggle_sidebar(self):
        start = self.sidebar_widget.maximumWidth()
        if not self.sidebar_collapsed:
            end = 40
            self.toggle_sidebar_btn.setText("▶️")
        else:
            end = self.sidebar_expanded_width
            self.toggle_sidebar_btn.setText("◀️")
        self.sidebar_collapsed = not self.sidebar_collapsed

        self.sidebar_anim.stop()
        self.sidebar_anim.setStartValue(start)
        self.sidebar_anim.setEndValue(end)
        self.sidebar_anim.start()

    def set_mode(self, mode: str):
        if mode == self.current_mode:
            return
        self.current_mode = mode

        self.assistant_mode_btn.setChecked(mode == "assistant")
        self.ai_mode_btn.setChecked(mode == "ai")

        if mode == "assistant":
            self.assistant_container.show()
            self.ai_container_widget.hide()
            self.visualizer.show()
        else:
            self.assistant_container.hide()
            self.ai_container_widget.show()
            self.visualizer.hide()
            self._load_ai_sidebar()

    def _load_ai_sidebar(self):
        self.ai_sidebar.clear()
        for chat in self.controller.ai_store.chats:
            item = QListWidgetItem(chat.title)
            item.setData(Qt.UserRole, chat.id)
            self.ai_sidebar.addItem(item)

        if self.controller.ai_store.chats and not self.current_ai_chat_id:
            first = self.controller.ai_store.chats[0]
            self.current_ai_chat_id = first.id
            self._load_ai_chat(first.id)

    def _create_new_ai_chat(self):
        chat = self.controller.ai_store.create_chat("New chat")
        self.current_ai_chat_id = chat.id
        self._load_ai_sidebar()
        self._load_ai_chat(chat.id)

    def _load_ai_chat(self, chat_id: str):
        chat = self.controller.ai_store.get_chat(chat_id)
        if not chat:
            return

        while self.ai_chat_layout.count() > 1:
            item = self.ai_chat_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        for msg in chat.messages:
            self.ai_chat_layout.insertWidget(
                self.ai_chat_layout.count() - 1,
                ChatBubble(msg.content, is_user=(msg.role == "user")),
            )
        QTimer.singleShot(0, self._scroll_ai_to_bottom)

    def _add_ai_message(self, text: str, is_user: bool):
        self.ai_chat_layout.insertWidget(
            self.ai_chat_layout.count() - 1,
            ChatBubble(text, is_user),
        )
        QTimer.singleShot(0, self._scroll_ai_to_bottom)

    def _scroll_ai_to_bottom(self):
        self.ai_chat_host.adjustSize()
        bar = self.ai_scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _on_ai_chat_selected(self, item: QListWidgetItem):
        chat_id = item.data(Qt.UserRole)
        self.current_ai_chat_id = chat_id
        self._load_ai_chat(chat_id)

    def _on_ai_sidebar_context_menu(self, pos):
        item = self.ai_sidebar.itemAt(pos)
        if not item:
            return
        chat_id = item.data(Qt.UserRole)

        menu = QMenu(self)
        rename_action = menu.addAction("✏️ Rename")
        delete_action = menu.addAction("🗑️ Delete")
        action = menu.exec_(self.ai_sidebar.mapToGlobal(pos))

        if action == rename_action:
            new_title, ok = QInputDialog.getText(
                self, "Rename chat", "Title:", text=item.text()
            )
            if ok and new_title.strip():
                self.controller.ai_store.rename_chat(chat_id, new_title.strip())
                self._load_ai_sidebar()
        elif action == delete_action:
            self.controller.ai_store.delete_chat(chat_id)
            if self.current_ai_chat_id == chat_id:
                self.current_ai_chat_id = None
            self._load_ai_sidebar()
            self._clear_ai_messages()

    def _clear_ai_messages(self):
        while self.ai_chat_layout.count() > 1:
            item = self.ai_chat_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()


def launch_ui():
    app = QApplication(sys.argv)
    win = OrbitOS()
    win.show()
    sys.exit(app.exec())
