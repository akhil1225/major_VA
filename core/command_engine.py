import re
import pickle
import numpy as np
import tensorflow as tf  # type: ignore
from typing import Dict
from keras import models  # type: ignore

from tensorflow.keras.preprocessing.sequence import pad_sequences  # type: ignore

from skills import file_control


# ---------------- LOAD MODEL ----------------
model = tf.keras.models.load_model("core/intent_model_dl.keras")  #type:ignore

with open("core/tokenizer.pkl", "rb") as f:
    tokenizer = pickle.load(f)

with open("core/label_encoder.pkl", "rb") as f:
    label_encoder = pickle.load(f)

MAX_LEN = 25

#--------- folder name extract------
def extract_folder_name(text: str) -> str:
    text = text.lower()

    text = re.sub(
        r"\b(navigate|go|move|open|into|inside|in|to|the|folder|directory|please|can you|could you)\b",
        "",
        text
    )

    return re.sub(r"\s+", " ", text).strip()



# ---------------- FILENAME EXTRACTION ----------------
def extract_filename(text: str) -> str:
    text = text.lower()

    text = re.sub(
        r"\b(create|make|delete|remove|open|new|file|folder|directory|named|called|as|please|can you|could you|a|the)\b",
        "",
        text
    )

    text = re.sub(r"\b(dot|point|period)\b", ".", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = text.split()
    if not tokens:
        return ""

    joined = []
    buffer = []

    for t in tokens:
        if len(t) == 1 and t.isalpha():
            buffer.append(t)
        else:
            if buffer:
                joined.append("".join(buffer))
                buffer.clear()
            joined.append(t)

    if buffer:
        joined.append("".join(buffer))

    filename = " ".join(joined)
    filename = re.sub(r"\s*\.\s*", ".", filename)

    if filename.startswith("."):
        filename = "file" + filename

    return filename.strip()


# ---------------- APP NAME EXTRACTION ----------------
def extract_app_name(text: str) -> str:
    text = text.lower()
    text = re.sub(
        r"\b(open|close|launch|run|start|switch|to|the|app|application|program|please|can you|could you)\b",
        "",
        text
    )
    return re.sub(r"\s+", " ", text).strip()


# ---------------- INTENT PREDICTION ----------------
def predict_intent(text: str):
    seq = tokenizer.texts_to_sequences([text])
    padded = pad_sequences(seq, maxlen=MAX_LEN, padding="post")

    probs = model.predict(padded, verbose=0)[0]
    idx = np.argmax(probs)

    intent = label_encoder.inverse_transform([idx])[0]
    confidence = float(probs[idx])

    return intent, confidence


# ---------------- MAIN ROUTER ----------------
def process_command(text: str) -> Dict:
    intent, confidence = predict_intent(text)

    # DEBUG (keep while testing)
    print("DEBUG:", intent, confidence)

    if confidence < 0.6:
        return {"type": "unknown"}

    # ---------- TIME / DATE ----------
    if intent == "GET_TIME":
        return {"type": "get_time"}

    if intent == "GET_DATE":
        return {"type": "get_date"}

    # ---------- FILE SYSTEM ----------
    name = extract_filename(text)

    if intent == "CREATE_FILE":
        return {"type": "create_file", "name": name}

    if intent == "DELETE_FILE":
        return {"type": "delete_file", "name": name}

    if intent == "CREATE_FOLDER":
        return {"type": "create_folder", "name": name}

    if intent == "DELETE_FOLDER":
        return {"type": "delete_folder", "name": name}

    if intent == "LIST_FILES":
        return {"type": "list_files"}

    # ---------- APPLICATIONS ----------
    if intent == "OPEN_APPLICATION":
        return {"type": "open_application", "app": extract_app_name(text)}

    if intent == "CLOSE_APPLICATION":
        return {"type": "close_application", "app": extract_app_name(text)}

    if intent == "LIST_INSTALLED_APPLICATIONS":
        return {"type": "list_installed_apps"}
    
    if intent == "NAVIGATE_IN":
        return {
            "type": "navigate_in",
            "name": extract_folder_name(text)
        }

    if intent == "NAVIGATE_OUT":
        return {"type": "navigate_out"}


    # ---------- UNDO ----------
    if intent == "UNDO":
        return {"type": "undo"}

        # ---------- VOLUME ----------
    if intent == "SET_VOLUME":
        return {
            "type": "set_volume",
            "value": extract_number(text)
        }

    if intent == "INCREASE_VOLUME":
        return {"type": "increase_volume"}

    if intent == "DECREASE_VOLUME":
        return {"type": "decrease_volume"}

    if intent == "MUTE_VOLUME":
        return {"type": "mute_volume"}

    if intent == "UNMUTE_VOLUME":
        return {"type": "unmute_volume"}


    # ---------- POWER ----------
    if intent == "SHUTDOWN_SYSTEM":
        return {"type": "shutdown_system"}

    if intent == "RESTART_SYSTEM":
        return {"type": "restart_system"}

    if intent == "SLEEP_SYSTEM":
        return {"type": "sleep_system"}


    # ---------- ALARMS ----------
    if intent == "SET_ALARM":
        return {
            "type": "set_alarm",
            "time": extract_time(text)
        }

    if intent == "LIST_ALARMS":
        return {"type": "list_alarms"}
    


    # ---------- SYSTEM / NETWORK / PERFORMANCE / BATTERY ----------
    if intent == "SYSTEM_STATUS":
        return {"type": "get_system_status"}

    if intent == "NETWORK_STATUS":
        return {"type": "get_network_status"}

    if intent == "PERFORMANCE_STATUS":
        return {"type": "get_performance_status"}

    if intent == "BATTERY_STATUS":
        return {"type": "get_battery_status"}
    
        # ---------- SCREEN / VISION ----------
    if intent == "DESCRIBE_SCREEN":
        return {"type": "describe_screen"}

    if intent == "READ_SCREEN_TEXT":
        return {"type": "read_screen_text"}

    if intent == "FOREGROUND_WINDOW_INFO":
        return {"type": "foreground_window_info"}



    return {"type": "unknown"}





def extract_number(text: str):
    match = re.search(r"\b(\d{1,3})\b", text)
    return int(match.group(1)) if match else None


def extract_time(text: str):
    text = text.lower()
    match = re.search(r"(\d{1,2})(?:[: ](\d{2}))?", text)
    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)

    if hour > 23 or minute > 59:
        return None

    return f"{hour:02d}:{minute:02d}"
