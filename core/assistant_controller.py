import threading
from typing import Callable, Optional

import os

from core.command_engine import process_command
from core.voice_engine import listen_once
from core.speech_engine import speak
from core.wakeword_engine import WakeWordEngine
from core.dialog_state import DialogState, PendingAction

from skills import file_control
from skills import application_control
from skills.file_control import get_base_dir, set_base_dir
from skills import system_info
from skills import volume_control
from skills import power_control
from skills import alarm_control
from core.time_parser import extract_time
from skills import alarm_control

from PySide6.QtCore import QTimer  # type: ignore


class AssistantController:
    """
    Central brain:
    wake word → intent → dialog → execution
    """

    def __init__(self):
 
        self.on_state_change: Optional[Callable[[str], None]] = None
        self.on_message: Optional[Callable[[str], None]] = None
        self.on_speaking_start: Optional[Callable[[], None]] = None
        self.on_speaking_end: Optional[Callable[[], None]] = None
        self.on_directory_change: Optional[Callable[[], None]] = None
        self.on_user_input: Optional[Callable[[str], None]] = None

        self._busy = False
        self._input_source = "voice"

        self.dialog = DialogState()
        self.last_matches = []
        self.last_spoken: Optional[str] = None

        self.wake_engine = WakeWordEngine(self._on_wake_word)
        self.wake_engine.start()

        self._set_state("idle")



    def _set_state(self, state: str):
        if callable(self.on_state_change):
            self.on_state_change(state)

    def _speak(self, text: str):
      
        self.last_spoken = text

 
        if callable(self.on_speaking_start):
            self.on_speaking_start()

        def worker():
            speak(text)
            if callable(self.on_speaking_end):
                self.on_speaking_end()

        threading.Thread(target=worker, daemon=True).start()



    def _on_wake_word(self):
        if self._busy:
            return
        self._busy = True
        self._set_state("wake")
        self._speak("Yes?")
        self._listen_async()


    def _listen_async(self):
        def worker():
            try:
                self._set_state("listening")
                text = listen_once()
                if not text:
                    self._speak("I did not catch that.")
                    return
                self._input_source = "voice"
                self._handle_command(text)
                
            finally:
                self._busy = False
                self._set_state("idle")

        threading.Thread(target=worker, daemon=True).start()

    def pause_wake_word(self):
        if self.wake_engine:
            self.wake_engine.stop()

    def resume_wake_word(self):
        if self.wake_engine:
            self.wake_engine.start()


    def _handle_command(self, text: str):
        result = process_command(text)
        rtype = result.get("type")

        if rtype == "get_time":
            current_time = system_info.get_current_time()
            self._speak(f"The time is {current_time}.")
            return

        if rtype == "get_date":
            current_date = system_info.get_current_date()
            self._speak(f"Today is {current_date}.")
            return

        if self.dialog.pending:
            lower = text.lower()

            if "yes" in lower:
                self._speak(self.dialog.confirm())
                return

            if "no" in lower or "cancel" in lower:
                self._speak(self.dialog.cancel())
                return

            if lower.startswith(("first", "second", "third", "fourth", "fifth")):
                idx_map = {
                    "first": 0,
                    "second": 1,
                    "third": 2,
                    "fourth": 3,
                    "fifth": 4,
                }
                for key, idx in idx_map.items():
                    if key in lower:
                        self._speak(self.dialog.select(idx))
                        return

                self._speak("Please say yes, no, or choose an option.")
                return


        if rtype == "create_file":
            if self._input_source == "text":
                action = PendingAction(
                    f"create file {result['name']}",
                    lambda: file_control.create_file(result["name"]),
                    lambda: file_control.delete_file(result["name"]),
                )
                self.dialog.set_pending(action)
                self._speak(f"Should I create the file {result['name']}?")
            else:
   
                self._speak(file_control.create_file(result["name"]))
            return

        if rtype == "delete_file":
            if self._input_source == "text":
                action = PendingAction(
                    f"delete file {result['name']}",
                    lambda: file_control.delete_file(result["name"]),
                    lambda: file_control.create_file(result["name"]),
                )
                self.dialog.set_pending(action)
                self._speak(f"Are you sure you want to delete {result['name']}?")
            else:

                self._speak(file_control.delete_file(result["name"]))
            return

        if rtype == "create_folder":
            self._speak(file_control.create_folder(result["name"]))
            return

        if rtype == "delete_folder":
            self._speak(file_control.delete_folder(result["name"]))
            return

        if rtype == "list_files":
            listing = file_control.list_items()
            if not listing.strip():
                self._speak("The current folder is empty.")
            else:
                self._speak("Here are the files and folders in the current directory.")
                if callable(self.on_message):
                    # send each item to UI
                    for line in listing.splitlines():
                        self.on_message(line)
            return

        if rtype == "navigate_in":
            folder = result.get("name")
            if not folder:
                self._speak("Please specify a folder name.")
                return

            response = file_control.navigate_to_folder(folder)
            self._speak(response)

            if callable(self.on_state_change):
                self.on_state_change("idle")
            if callable(self.on_directory_change):
                self.on_directory_change()
            return

        if rtype == "navigate_out":
            response = file_control.go_back()
            self._speak(response)
            if callable(self.on_directory_change):
                self.on_directory_change()
            return


        if rtype == "open_application":
            query = result["app"]
            matches = application_control.find_app_candidates(query)
            self.last_matches = matches

            if not matches:
                self._speak(f"I couldn't find any application matching {query}.")
                return

            if len(matches) == 1:
                self._speak(application_control.open_application(query))
                return

            names = [m["name"] for m in matches[:5]]
            action = PendingAction(
                f"open {names[0]}",
                lambda: application_control.open_application(names[0]),
                None,
                options=names,
            )
            self.dialog.set_pending(action)

            msg = "I found multiple applications:\n"
            for i, name in enumerate(names, 1):
                msg += f"{i}. {name}\n"
            msg += "Which one should I open?"
            self._speak(msg)
            return

        if rtype == "close_application":
            self._speak(application_control.close_application(result["app"]))
            return

        if rtype == "list_installed_apps":
            data = application_control.list_installed_applications()
            self._speak(data["summary"])
            if callable(self.on_message):
                # send each app name to UI
                for item in data["items"]:
                    self.on_message(item)
            return

        if rtype == "refresh_apps":
            self._speak(application_control.refresh_applications())
            return

        if rtype == "undo":
            self._speak(self.dialog.undo())
            return

        if rtype == "set_volume":
            if result["value"] is None:
                self._speak("Please tell me a volume level.")
            else:
                self._speak(volume_control.set_volume(result["value"]))
            return

        if rtype == "increase_volume":
            self._speak(volume_control.increase_volume())
            return

        if rtype == "decrease_volume":
            self._speak(volume_control.decrease_volume())
            return

        if rtype == "mute_volume":
            self._speak(volume_control.mute())
            return

        if rtype == "unmute_volume":
            self._speak(volume_control.unmute())
            return

    
        if rtype == "set_alarm":
            parsed = extract_time(text)
            if not parsed:
                self._speak("Please tell me a valid time for the alarm.")
                return

            hour, minute = parsed

            def alarm_callback():
                QTimer.singleShot(0, lambda: self._speak("Your alarm is ringing."))

            self._speak(alarm_control.set_alarm(hour, minute, alarm_callback))
            return

        if rtype == "cancel_alarm":
            self._speak(alarm_control.cancel_alarm())
            return

        if rtype == "get_alarm":
            self._speak(alarm_control.get_alarm_status())
            return


        self._speak("Please try again,  akhil")


    def handle_text_command(self, text: str) -> str:
        self._input_source = "text"
        self._handle_command(text)
        # Return what was spoken (captured in _speak)
        return self.last_spoken or "Processing..."

 
 
    def handle_voice_command_async(
        self,
        callback: Callable[[Optional[str], Optional[str]], None],
    ):
        if self._busy:
            return

        def worker():
            try:
                self._busy = True
                self._set_state("listening")

                text = listen_once()
                if not text:
                    self._speak("I did not catch that.")
                    callback(None, None)
                    return

                self._input_source = "voice"
                self._handle_command(text)
                callback(text, self.get_last_response())

                # pass both heard text and last spoken reply
                
            finally:
                self._busy = False
                self._set_state("idle")

        threading.Thread(target=worker, daemon=True).start()



    def get_working_directory(self) -> str:
        return get_base_dir()

    def set_working_directory(self, path: str):
        set_base_dir(path)
        if callable(self.on_directory_change):
            self.on_directory_change()

    def get_last_response(self) -> Optional[str]:
        return self.last_spoken
