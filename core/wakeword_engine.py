import speech_recognition as sr #type: ignore
import threading
import time
from typing import cast

WAKE_WORDS = ["orbit", "hey orbit", "ok orbit"]


class WakeWordEngine:
    """
    Continuously listens for wake word.
    Calls a callback when detected.
    """

    def __init__(self, on_wake_callback):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.on_wake_callback = on_wake_callback
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._listen_loop,
            daemon=True
        )
        self._thread.start()

    def stop(self):
        self._running = False

    def _listen_loop(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

            while self._running:
                try:
                    audio = self.recognizer.listen(
                        source,
                        timeout=None,
                        phrase_time_limit=3
                    )

                    # ---- TYPE CHECKER FIX ----
                    recognizer = cast(sr.Recognizer, self.recognizer)
                    text = recognizer.recognize_google(audio).lower()#type:ignore

                    for wake_word in WAKE_WORDS:
                        if wake_word in text:
                            self.on_wake_callback()
                            time.sleep(1)  # prevent double trigger
                            break

                except sr.UnknownValueError:
                    continue
                except sr.RequestError:
                    continue
                except Exception:
                    continue
