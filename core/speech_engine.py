import threading
import queue
import re
import pythoncom
import win32com.client




_speech_queue = queue.Queue()
_last_spoken_text = ""
_muted = False
_stop_flag = threading.Event()



def _split_into_sentences(text: str):
    """
    Splits text into natural sentences for smooth speech.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s for s in sentences if s]




def _speech_worker():
    pythoncom.CoInitialize()
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")

        while True:
            text = _speech_queue.get()
            if text is None:
                break

            if _muted:
                _speech_queue.task_done()
                continue

            global _last_spoken_text
            _last_spoken_text = text

            _stop_flag.clear()

            sentences = _split_into_sentences(text)

            for sentence in sentences:
                if _stop_flag.is_set():
                    # flush current speech immediately
                    speaker.Speak("", 3)  # SVSFPurgeBeforeSpeak
                    break

                speaker.Speak(sentence, 0)

            _speech_queue.task_done()

    finally:
        pythoncom.CoUninitialize()



_thread = threading.Thread(target=_speech_worker, daemon=True)
_thread.start()



def speak(text: str):
    if not text or not text.strip():
        return
    _speech_queue.put(text)


def stop_speaking():
    _stop_flag.set()

    # Flush pending speech
    while not _speech_queue.empty():
        try:
            _speech_queue.get_nowait()
            _speech_queue.task_done()
        except queue.Empty:
            break



def toggle_mute() -> bool:
    global _muted
    _muted = not _muted

    if _muted:
        stop_speaking()

    return _muted


def replay_last():
    if _last_spoken_text:
        speak(_last_spoken_text)

