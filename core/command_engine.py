import re
import joblib
from skills import file_control

model = joblib.load("core/intent_model.pkl")

def normalize_name(text: str) -> str:
    text = text.lower()

    replacements = {
        " dot ": ".",
        " underscore ": "_",
        " dash ": "-",
        " space ": "",
        " slash ": "/"
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    
    text = re.sub(
        r"\b(named|called|as|file|folder|directory|a|the|please|can you|could you)",
        "",
        text
    )

    text = re.sub(r"\s+", " ", text).strip()

    parts = text.split()
    if not parts:
        return ""

    return parts[-1]

def process_command(text: str) -> str:
  
    scores = model.decision_function([text])
    confidence = abs(scores).max()

    if confidence < 0.3:
        return "I am not sure what you mean. Please rephrase."

    intent = model.predict([text])[0]
    name = normalize_name(text)

    if intent in {"CREATE_FILE", "DELETE_FILE", "CREATE_FOLDER", "DELETE_FOLDER"} and not name:
        return "Please specify a file or folder name."

    if intent == "CREATE_FILE":
        return file_control.create_file(name)

    elif intent == "DELETE_FILE":
        return file_control.delete_file(name)

    elif intent == "CREATE_FOLDER":
        return file_control.create_folder(name)

    elif intent == "DELETE_FOLDER":
        return file_control.delete_folder(name)

    elif intent == "LIST_FILES":
        return file_control.list_items()

    else:
        return "Intent not recognized."
