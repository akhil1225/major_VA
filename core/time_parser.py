import re
from typing import Optional, Tuple


def extract_time(text: str) -> Optional[Tuple[int, int]]:
    """
    Extracts time from natural language.
    Supported:
    - 5 pm
    - 5:30 pm
    - 17 00
    - 17:00
    - 7 am
    """

    text = text.lower().strip()

    # 17:00 or 5:30
    match = re.search(r"\b(\d{1,2})[: ](\d{2})\b", text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
    else:
        # 5 pm / 7 am
        match = re.search(r"\b(\d{1,2})\b", text)
        if not match:
            return None
        hour = int(match.group(1))
        minute = 0

    # AM / PM
    if "pm" in text and hour < 12:
        hour += 12
    if "am" in text and hour == 12:
        hour = 0

    if hour > 23 or minute > 59:
        return None

    return hour, minute
