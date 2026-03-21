"""
OrbitOS – FastAPI backend
Wraps every skill from AssistantController / command_engine
and exposes them as REST + WebSocket endpoints for the React UI.

Run with:
uvicorn server:app --reload --port 8000
"""

import asyncio
import os
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

import pyautogui

pyautogui.FAILSAFE = True

from core.command_engine import process_command




from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Core ──────────────────────────────────────────────────────────────────────
from core.command_engine import process_command
from core.ai_chat_store import AIChatStore
from core.llm_client import LLMClient
from core.time_parser import extract_time
from core.speech_engine import speak, toggle_mute, stop_speaking, replay_last
from core.voice_engine import listen_once
from core.wakeword_engine import WakeWordEngine

# ── Skills ────────────────────────────────────────────────────────────────────
from skills import file_control
from skills import application_control
from skills import volume_control
from skills import power_control
from skills import alarm_control
from skills import screen_analyzer
from skills import wiki_skill
from skills import weather_skill
from skills import notes_skill
from skills import system_info
from skills.system_state import SystemState
from skills.file_control import get_base_dir, set_base_dir

# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="OrbitOS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singletons ────────────────────────────────────────────────────────────────
_working_dir = Path.cwd()
ai_store = AIChatStore(_working_dir)
llm: Optional[LLMClient] = None
system_state: Optional[SystemState] = None

# ── Dialog state (confirm / undo) ─────────────────────────────────────────────
from core.dialog_state import DialogState, PendingAction

dialog = DialogState()
last_spoken: Optional[str] = None

# ── WebSocket clients ─────────────────────────────────────────────────────────
ws_state_clients: List[WebSocket] = []
ws_wake_clients: List[WebSocket] = []

event_loop: Optional[asyncio.AbstractEventLoop] = None

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _speak_bg(text: str):
    """Fire-and-forget TTS in a background thread."""
    global last_spoken
    last_spoken = text
    threading.Thread(target=speak, args=(text,), daemon=True).start()


async def _broadcast_state(state: str):
    """Push state update to all connected /ws/state clients."""
    dead = []
    for ws in ws_state_clients:
        try:
            await ws.send_json({"state": state})
        except Exception:
            dead.append(ws)
    for ws in dead:
        ws_state_clients.remove(ws)


def _broadcast_state_sync(state: str):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(_broadcast_state(state), loop)
    except Exception:
        pass


async def _broadcast_wake_event(event: Dict[str, Any]):
    """Push wakeword events to /ws/wake clients."""
    print("[Wakeword] _broadcast_wake_event ->", event)
    dead: list[WebSocket] = []
    for ws in ws_wake_clients:
        try:
            await ws.send_json(event)
            print("[Wakeword]   sent to client", id(ws))
        except Exception as e:
            print("[Wakeword]   ERROR sending to client", id(ws), ":", repr(e))
            dead.append(ws)
    for ws in dead:
        try:
            ws_wake_clients.remove(ws)
        except ValueError:
            pass
    print("[Wakeword] _broadcast_wake_event done, clients:", len(ws_wake_clients))


def _broadcast_wake_event_sync(event: Dict[str, Any]):
    """Safe wrapper to call _broadcast_wake_event from non-async threads."""
    global event_loop
    try:
        loop = event_loop or asyncio.get_event_loop()
    except RuntimeError:
        print("[Wakeword] No event loop available for wake broadcast.")
        return

    if loop.is_running():
        asyncio.run_coroutine_threadsafe(_broadcast_wake_event(event), loop)
    else:
        print("[Wakeword] Event loop not running; cannot broadcast wake event.")

def get_system_state() -> SystemState:
    """Lazy initializer for SystemState."""
    global system_state
    if system_state is None:
        system_state = SystemState()
    return system_state

# ─────────────────────────────────────────────────────────────────────────────
# WebSockets
# ─────────────────────────────────────────────────────────────────────────────
@app.websocket("/ws/state")
async def ws_state(ws: WebSocket):
    await ws.accept()
    ws_state_clients.append(ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive ping from client
    except WebSocketDisconnect:
        if ws in ws_state_clients:
            ws_state_clients.remove(ws)


@app.websocket("/ws/wake")
async def ws_wake(ws: WebSocket):
    print("[WS /ws/wake] New client connecting...")
    await ws.accept()
    ws_wake_clients.append(ws)
    print("[WS /ws/wake] Client connected. Total:", len(ws_wake_clients))
    try:
        while True:
            msg = await ws.receive_text()  # keep alive
            print("[WS /ws/wake] Received from client:", repr(msg))
    except WebSocketDisconnect:
        print("[WS /ws/wake] Client disconnected.")
        if ws in ws_wake_clients:
            ws_wake_clients.remove(ws)
            print("[WS /ws/wake] Remaining clients:", len(ws_wake_clients))
    except Exception as e:
        print("[WS /ws/wake] ERROR:", repr(e))
        if ws in ws_wake_clients:
            ws_wake_clients.remove(ws)

# ─────────────────────────────────────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────────────────────────────────────
class CommandRequest(BaseModel):
    text: str


class AIChatRequest(BaseModel):
    chat_id: str
    message: str
    model: Optional[str] = None


class RenameRequest(BaseModel):
    title: str


class DirectoryRequest(BaseModel):
    path: str


class VolumeRequest(BaseModel):
    value: int  # 0–100


class AlarmRequest(BaseModel):
    time: str  # "HH:MM"


class WeatherRequest(BaseModel):
    city: str


class WikiRequest(BaseModel):
    query: str


class NoteRequest(BaseModel):
    text: str


class AppRequest(BaseModel):
    name: str  # app query string


class DialogReply(BaseModel):
    answer: str  # "yes" | "no" | "first" .. "fifth"

# ─────────────────────────────────────────────────────────────────────────────
# MAIN COMMAND ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/command")
async def run_command(req: CommandRequest):
    text = req.text.strip()
    result = process_command(text)
    rtype = result.get("type", "")

    await _broadcast_state("processing")

    reply = _dispatch(rtype, result, text)

    _speak_bg(reply)
    await _broadcast_state("idle")




    rtype = result.get("type", "")
    return {"reply": reply}


def _dispatch(rtype: str, result: dict, raw_text: str) -> str:
    """
    Mirror of AssistantController._handle_command but returns a string.
    """
    global _working_dir

    # Pending dialog
    if dialog.pending:
        lower = raw_text.lower()
        if "yes" in lower:
            return dialog.confirm()
        if "no" in lower or "cancel" in lower:
            return dialog.cancel()
        for key, idx in {
            "first": 0,
            "second": 1,
            "third": 2,
            "fourth": 3,
            "fifth": 4,
        }.items():
            if key in lower:
                return dialog.select(idx)
        return "Please say yes, no, or choose an option."

    # Time / Date
    if rtype == "get_time":
        return f"The time is {system_info.get_current_time()}."
    if rtype == "get_date":
        return f"Today is {system_info.get_current_date()}."

    # File system
    if rtype == "create_file":
        name = result.get("name", "")
        action = PendingAction(
            f"create file {name}",
            lambda: file_control.create_file(name),
            lambda: file_control.delete_file(name),
        )
        dialog.set_pending(action)
        return f"Should I create the file {name}?"

    if rtype == "delete_file":
        name = result.get("name", "")
        action = PendingAction(
            f"delete file {name}",
            lambda: file_control.delete_file(name),
        )
        dialog.set_pending(action)
        return f"Are you sure you want to delete {name}?"

    if rtype == "create_folder":
        name = result.get("name", "")
        action = PendingAction(
            f"create folder {name}",
            lambda: file_control.create_folder(name),
            lambda: file_control.delete_folder(name),
        )
        dialog.set_pending(action)
        return f"Should I create the folder {name}?"

    if rtype == "delete_folder":
        name = result.get("name", "")
        action = PendingAction(
            f"delete folder {name}",
            lambda: file_control.delete_folder(name),
        )
        dialog.set_pending(action)
        return f"Are you sure you want to delete the folder {name}?"

    if rtype == "list_files":
        return file_control.list_items()

    if rtype == "navigate_in":
        name = result.get("name", "")
        return file_control.navigate_to_folder(name)

    if rtype == "navigate_out":
        return file_control.go_back()

    # Applications
    if rtype == "open_application":
        query = result.get("app", "")
        matches = application_control.find_app_candidates(query)
        if not matches:
            return f"I couldn't find any application matching '{query}'."
        if len(matches) == 1:
            return application_control.open_application(query)
        names = [m["name"] for m in matches[:5]]
        action = PendingAction(
            f"open {names[0]}",
            lambda: application_control.open_application(names[0]),
            options=names,
        )
        dialog.set_pending(action)
        opts = "\n".join(f"{i+1}. {n}" for i, n in enumerate(names))
        return f"I found multiple apps:\n{opts}\nWhich one should I open?"

    if rtype == "close_application":
        return application_control.close_application(result.get("app", ""))

    if rtype == "list_installed_apps":
        data = application_control.list_installed_applications()
        items_str = ", ".join(data["items"][:30])
        return f"{data['summary']} Here are some: {items_str}."

    if rtype == "refresh_apps":
        return application_control.refresh_applications()

    # Undo
    if rtype == "undo":
        return dialog.undo()

    # Volume
    if rtype == "set_volume":
        val = result.get("value")
        if val is None:
            return "Please tell me a volume level between 0 and 100."
        return volume_control.set_volume(int(val))

    if rtype == "increase_volume":
        return volume_control.increase_volume()
    if rtype == "decrease_volume":
        return volume_control.decrease_volume()
    if rtype == "mute_volume":
        return volume_control.mute()
    if rtype == "unmute_volume":
        return volume_control.unmute()

    # Power
    if rtype == "shutdown_system":
        return power_control.shutdown_system()
    if rtype == "restart_system":
        return power_control.restart_system()
    if rtype == "sleep_system":
        return power_control.sleep_system()

    # Alarms
    if rtype == "set_alarm":
        parsed = extract_time(raw_text)
        if not parsed:
            return "Please tell me a valid time for the alarm, like 7:30 AM."
        hour, minute = parsed

        def alarm_callback():
            _speak_bg("Your alarm is ringing!")
            _broadcast_state_sync("wake")

        return alarm_control.set_alarm(hour, minute, alarm_callback)

    if rtype == "cancel_alarm":
        return alarm_control.cancel_alarm()
    if rtype == "list_alarms":
        return alarm_control.get_alarm_status()
    if rtype == "get_alarm":
        return alarm_control.get_alarm_status()

    # System status
    if rtype == "get_system_status":
        ss = get_system_state()
        ss.refresh()
        return ss.summary()
    if rtype == "get_network_status":
        ss = get_system_state()
        ss.refresh()
        return (
            "You are connected to the internet."
            if ss.online
            else "You are currently offline."
        )
    if rtype == "get_performance_status":
        ss = get_system_state()
        ss.refresh()
        return (
            f"CPU usage is {ss.cpu:.0f}% and "
            f"memory usage is {ss.memory['percent']:.0f}%."
        )
    if rtype == "get_battery_status":
        ss = get_system_state()
        ss.refresh()
        b = ss.battery
        if not b.get("available"):
            return "Battery information is not available on this system."
        pct = b.get("percent", 0)
        plugged = b.get("plugged_in", False)
        return (
            f"Battery is at {pct:.0f}% and "
            f"{'charging' if plugged else 'running on battery'}."
        )

    # Screen / vision
    if rtype == "describe_screen":
        return screen_analyzer.describe_current_screen()
    if rtype == "read_screen_text":
        return screen_analyzer.read_screen_text()
    if rtype == "foreground_window_info":
        return screen_analyzer.get_foreground_window_info()

    # Knowledge
    if rtype == "wiki_search":
        topic = result.get("query", "").strip() or raw_text
        return wiki_skill.wikipedia_summary(topic)
    if rtype == "weather_status":
        city = result.get("city", "").strip()
        if not city:
            return "Please tell me the city name for the weather."
        return weather_skill.get_weather(city)

    # Notes
    if rtype == "append_note":
        note_text = result.get("note_text", raw_text)
        return notes_skill.append_note(note_text, base_dir=str(_working_dir))
    if rtype == "read_notes":
        return notes_skill.read_notes(base_dir=str(_working_dir))

    # Unknown
    return "I didn't understand that. Could you please try again?"

# ─────────────────────────────────────────────────────────────────────────────
# AI chat
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/ai/chats")
def list_chats():
    return [{"id": c.id, "title": c.title} for c in ai_store.chats]


@app.post("/ai/chats")
def create_chat():
    chat = ai_store.create_chat()
    return {"id": chat.id, "title": chat.title}


@app.delete("/ai/chats/{chat_id}")
def delete_chat(chat_id: str):
    ai_store.delete_chat(chat_id)
    return {"ok": True}


@app.patch("/ai/chats/{chat_id}")
def rename_chat(chat_id: str, req: RenameRequest):
    ai_store.rename_chat(chat_id, req.title)
    return {"ok": True}


@app.get("/ai/chats/{chat_id}/messages")
def get_messages(chat_id: str):
    chat = ai_store.get_chat(chat_id)
    if not chat:
        return []
    return [{"role": m.role, "content": m.content} for m in chat.messages]


@app.post("/ai/chat")
def ai_chat(req: AIChatRequest):
    global llm
    if llm is None:
        from core.llm_client import LLMClient
        llm = LLMClient()

    chat = ai_store.get_chat(req.chat_id)
    if not chat:
        return {"reply": "Chat not found. Please create a new chat."}
    ai_store.add_message(req.chat_id, "user", req.message)
    messages = [{"role": m.role, "content": m.content} for m in chat.messages]
    reply = llm.chat(messages, model=req.model)
    ai_store.add_message(req.chat_id, "assistant", reply)
    _speak_bg(reply)
    return {"reply": reply}

# ─────────────────────────────────────────────────────────────────────────────
# File system + folder picker
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/fs/directory")
def get_directory():
    return {"path": get_base_dir()}


@app.post("/fs/directory")
def set_directory_api(req: DirectoryRequest):
    global _working_dir
    set_base_dir(req.path)
    _working_dir = Path(req.path)
    ai_store_reload()
    return {"ok": True, "path": req.path}


@app.post("/fs/browse")
def browse_directory():
    """
    Open native Explorer folder picker, set base_dir to chosen path,
    and return that path to the frontend.
    """
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    initial = get_base_dir()
    print(f"[FS] Opening folder picker, initial dir: {initial!r}")
    folder = filedialog.askdirectory(initialdir=initial or None)
    root.destroy()

    if not folder:
        print("[FS] Folder picker canceled.")
        return {"ok": False, "path": get_base_dir()}

    print(f"[FS] Folder chosen: {folder!r}")
    set_base_dir(folder)
    global _working_dir
    _working_dir = Path(folder)
    ai_store_reload()
    return {"ok": True, "path": folder}


@app.get("/fs/list")
def list_files_api():
    return {"items": file_control.list_items()}


def ai_store_reload():
    global ai_store
    ai_store = AIChatStore(_working_dir)

# ─────────────────────────────────────────────────────────────────────────────
# Direct skill endpoints (volume, power, alarms, etc.)
# ─────────────────────────────────────────────────────────────────────────────
@app.get("/volume")
def get_volume():
    return {"volume": volume_control.get_volume()}


@app.post("/volume/set")
def set_volume(req: VolumeRequest):
    reply = volume_control.set_volume(req.value)
    _speak_bg(reply)
    return {"reply": reply}


@app.post("/volume/up")
def volume_up():
    reply = volume_control.increase_volume()
    _speak_bg(reply)
    return {"reply": reply}


@app.post("/volume/down")
def volume_down():
    reply = volume_control.decrease_volume()
    _speak_bg(reply)
    return {"reply": reply}


@app.post("/volume/mute")
def mute_volume():
    reply = volume_control.mute()
    return {"reply": reply}


@app.post("/volume/unmute")
def unmute_volume():
    reply = volume_control.unmute()
    return {"reply": reply}


@app.post("/power/shutdown")
def shutdown():
    reply = power_control.shutdown_system()
    _speak_bg(reply)
    return {"reply": reply}


@app.post("/power/restart")
def restart():
    reply = power_control.restart_system()
    _speak_bg(reply)
    return {"reply": reply}


@app.post("/power/sleep")
def sleep():
    reply = power_control.sleep_system()
    _speak_bg(reply)
    return {"reply": reply}


@app.post("/alarm/set")
def set_alarm_api(req: AlarmRequest):
    parts = req.time.split(":")
    if len(parts) != 2:
        return {"reply": "Invalid time format. Use HH:MM."}
    hour, minute = int(parts[0]), int(parts[1])

    def alarm_callback():
        _speak_bg("Your alarm is ringing!")
        _broadcast_state_sync("wake")

    reply = alarm_control.set_alarm(hour, minute, alarm_callback)
    return {"reply": reply}


@app.post("/alarm/cancel")
def cancel_alarm_api():
    return {"reply": alarm_control.cancel_alarm()}


@app.get("/alarm/status")
def alarm_status():
    return {"reply": alarm_control.get_alarm_status()}


@app.get("/system/status")
def system_status():
    ss = get_system_state()
    ss.refresh()
    return {
        "summary": ss.summary(),
        "cpu": ss.cpu,
        "memory": ss.memory,
        "disk": ss.disk,
        "battery": ss.battery,
        "online": ss.online,
        "uptime_min": ss.uptime_min,
    }


@app.get("/system/time")
def get_time_api():
    return {"time": system_info.get_current_time()}


@app.get("/system/date")
def get_date_api():
    return {"date": system_info.get_current_date()}


@app.get("/screen/describe")
def describe_screen():
    reply = screen_analyzer.describe_current_screen()
    _speak_bg(reply)
    return {"reply": reply}


@app.get("/screen/read")
def read_screen():
    reply = screen_analyzer.read_screen_text()
    return {"reply": reply}


@app.get("/screen/window")
def foreground_window():
    reply = screen_analyzer.get_foreground_window_info()
    return {"reply": reply}


@app.post("/weather")
def weather(req: WeatherRequest):
    reply = weather_skill.get_weather(req.city)
    _speak_bg(reply)
    return {"reply": reply}


@app.post("/wiki")
def wiki(req: WikiRequest):
    reply = wiki_skill.wikipedia_summary(req.query)
    _speak_bg(reply)
    return {"reply": reply}


@app.post("/notes/append")
def append_note(req: NoteRequest):
    reply = notes_skill.append_note(req.text, base_dir=str(_working_dir))
    return {"reply": reply}


@app.get("/notes/read")
def read_notes():
    return {"reply": notes_skill.read_notes(base_dir=str(_working_dir))}


@app.post("/apps/open")
def open_app(req: AppRequest):
    reply = application_control.open_application(req.name)
    _speak_bg(reply)
    return {"reply": reply}


@app.post("/apps/close")
def close_app(req: AppRequest):
    reply = application_control.close_application(req.name)
    _speak_bg(reply)
    return {"reply": reply}


@app.get("/apps/list")
def list_apps():
    data = application_control.list_installed_applications()
    return data


@app.post("/apps/refresh")
def refresh_apps():
    return {"reply": application_control.refresh_applications()}


@app.post("/speech/stop")
def speech_stop():
    stop_speaking()
    return {"ok": True}


@app.post("/speech/replay")
def speech_replay():
    replay_last()
    return {"ok": True}


@app.post("/speech/mute")
def speech_mute():
    muted = toggle_mute()
    return {"muted": muted}


@app.post("/dialog/reply")
def dialog_reply(req: DialogReply):
    answer = req.answer.lower().strip()
    if answer == "yes":
        return {"reply": dialog.confirm()}
    if answer in ("no", "cancel"):
        return {"reply": dialog.cancel()}
    if answer == "undo":
        return {"reply": dialog.undo()}
    for key, idx in {
        "first": 0,
        "second": 1,
        "third": 2,
        "fourth": 3,
        "fifth": 4,
    }.items():
        if key == answer:
            return {"reply": dialog.select(idx)}
    return {"reply": "Unknown dialog answer."}

# ─────────────────────────────────────────────────────────────────────────────
# Voice endpoints (for Voice button, not wakeword)
# ─────────────────────────────────────────────────────────────────────────────
@app.post("/voice/listen")
def voice_listen():
    """
    Single-shot STT from desktop mic.
    """
    print("[Voice] listen_once requested from frontend.")
    _broadcast_state_sync("listening")
    text = listen_once()
    print(f"[Voice] listen_once heard: {text!r}")
    _broadcast_state_sync("idle")
    return {"text": text}

# ─────────────────────────────────────────────────────────────────────────────
# Wakeword engine – backend side, autostart + logging
# ─────────────────────────────────────────────────────────────────────────────
_wake_engine: Optional[WakeWordEngine] = None  # already imported at top


def _on_wakeword_detected(detected_text: str):
    """
    Called by WakeWordEngine when wake phrase is detected.
    """
    print("[Wakeword] Detected wake phrase:", repr(detected_text))
    _broadcast_state_sync("wake")
    _broadcast_wake_event_sync(
        {"type": "detected", "text": detected_text or ""}
    )

    _speak_bg("Yes?")

    def worker():
        _broadcast_state_sync("listening")
        text = listen_once()
        print(f"[Wakeword] After 'Yes?' heard: {text!r}")
        _broadcast_wake_event_sync(
            {"type": "after_heard", "text": text or ""}
        )

        if not text:
            _broadcast_state_sync("idle")
            return

        result = process_command(text)
        rtype = result.get("type", "")
        reply = _dispatch(rtype, result, text)
        print(f"[Wakeword] Reply: {reply!r}")
        _speak_bg(reply)
        _broadcast_wake_event_sync(
            {"type": "after_reply", "reply": reply}
        )
        _broadcast_state_sync("idle")

    threading.Thread(target=worker, daemon=True).start()


def start_wake_engine_once():
    global _wake_engine
    if _wake_engine is not None:
        return
    print("[Wakeword] Starting WakeWordEngine in background...")
    _wake_engine = WakeWordEngine(lambda: _on_wakeword_detected("wakeword"))
    _wake_engine.start()

# ─────────────────────────────────────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    global event_loop
    event_loop = asyncio.get_running_loop()

    # Disable wakeword for now so backend starts instantly
    # start_wake_engine_once()
    print("[Startup] Wakeword disabled on startup.")
    print("[Startup] OrbitOS API ready.")
