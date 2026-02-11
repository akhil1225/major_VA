# core/voice_engine.py

import speech_recognition as sr  # type: ignore

def listen_once() -> str | None:
    """
    Listen from the default microphone once and return the recognized text
    using Google's online speech recognition.
    Returns None if nothing understandable is heard.
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        # Short noise calibration for current environment
        recognizer.adjust_for_ambient_noise(source, duration=0.8)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language="en-IN")  # adjust if needed
        text = text.strip()
        if not text:
            print("No speech recognized.")
            return None
        print("Heard (command):", text)
        return text
    except sr.UnknownValueError:
        print("Could not understand audio.")
        return None
    except sr.RequestError as e:
        print(f"Error with Google Speech Recognition service: {e}")
        return None
