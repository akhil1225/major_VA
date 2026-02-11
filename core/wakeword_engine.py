# core/wakeword_engine.py

import threading
import time
from typing import Callable, cast

import speech_recognition as sr  # type: ignore

# You can say any of these
WAKE_WORDS = ["orbit", "hey orbit", "ok orbit"]


class WakeWordEngine:
    """
    Continuously listens for wake word using Google's online STT.
    Calls a callback when detected.
    """

    def __init__(self, on_wake_callback: Callable[[], None]):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.on_wake_callback = on_wake_callback

        self._running = False
        self._thread: threading.Thread | None = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._running = False

    def _listen_loop(self):
        with self.microphone as source:
            # One‑time calibration to the room noise
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            print("WakeWordEngine listening for wake word...")

            while self._running:
                try:
                    audio = self.recognizer.listen(
                        source,
                        timeout=None,
                        phrase_time_limit=3,
                    )

                    recognizer = cast(sr.Recognizer, self.recognizer)
                    try:
                        text = recognizer.recognize_google(audio, language="en-IN")
                    except sr.UnknownValueError:
                        continue
                    except sr.RequestError:
                        # Network / API error – wait and continue
                        time.sleep(1.0)
                        continue

                    text = text.lower().strip()
                    if not text:
                        continue

                    print("Things heard:", text)

                    if self._contains_wake_word(text):
                        print(f"Wake word detected in: '{text}'")
                        self.on_wake_callback()
                        time.sleep(1.0)  # prevent double trigger

                except Exception:
                    # Ignore random mic / timing errors and keep listening
                    continue

    def _contains_wake_word(self, text: str) -> bool:
        """
        Accepts exact wake phrases and close variants for 'orbit'.
        This makes wake word more robust against small recognition errors.
        """
        t = text.lower()

        # Exact phrases
        for wake in WAKE_WORDS:
            if wake in t:
                return True

        words = t.split()
        if "orbit" in words:
            return True

        # Very small fuzzy matching: common variants for 'orbit'
        fuzzy_bits = ["or bit", "or but", "hobbit", "orbit.", "orbit,"]
        for fb in fuzzy_bits:
            if fb in t:
                return True

        return False
