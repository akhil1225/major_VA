
import threading
import time
from typing import Callable, cast

import speech_recognition as sr  #type:ignore

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

       
        self.recognizer.dynamic_energy_threshold = True
       
        self.recognizer.energy_threshold = 200

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
        while self._running:
            try:
                with self.microphone as source:
                    # Re‑calibrate each time we successfully open a stream
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                    print("WakeWordEngine listening for wake word...")

                    while self._running:
                        try:
                            audio = self.recognizer.listen(
                                source,
                                timeout=None,
                                phrase_time_limit=4,
                            )

                            recognizer = cast(sr.Recognizer, self.recognizer)
                            try:
                                text = recognizer.recognize_google(
                                    audio,
                                    language="en-IN",
                                )
                            except sr.UnknownValueError:
                                continue
                            except sr.RequestError:
                                time.sleep(1.0)
                                continue

                            text = (text or "").lower().strip()
                            if not text:
                                continue

                            print("Things heard:", text)

                            if self._contains_wake_word(text):
                                print(f"Wake word detected in: '{text}'")
                                self.on_wake_callback()
                                time.sleep(1.2)

                        except OSError as e:
                            if e.errno == -9988:
                                print("WakeWordEngine: audio stream closed, will recreate mic.")
                                break  # break inner loop, re‑open mic in outer loop
                            else:
                                print("WakeWordEngine OS error:", repr(e))
                                continue
                        except Exception as e:
                            print("WakeWordEngine error:", repr(e))
                            continue

            except Exception as e:
                # Errors when opening the microphone itself; wait and retry
                print("WakeWordEngine mic open error:", repr(e))
                time.sleep(1.0)
                continue


    def _contains_wake_word(self, text: str) -> bool:
        """
        Accepts exact wake phrases and close variants for 'orbit'.
        This makes wake word more robust against small recognition errors.
        """
        t = text.lower()

        for wake in WAKE_WORDS:
            if wake in t:
                return True

        words = t.split()
        if "orbit" in words:
            return True

    
        fuzzy_bits = [
            "or bit",
            "or but",
            "hobbit",
            "orbit.",
            "orbit,",
            "orbit!",
            "orbit?",
            "hey orbit.",
            "hey orbit,",
            "ok orbit.",
            "ok orbit,",
        ]
        for fb in fuzzy_bits:
            if fb in t:
                return True


        if t.startswith("orbit ") or t.startswith("hey orbit ") or t.startswith("ok orbit "):
            return True

        return False
