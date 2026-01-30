import os
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from core.command_engine import process_command
from core.voice_engine import listen_once
from skills.file_control import set_base_dir

def run_command(entry, console):
    cmd = entry.get()
    if not cmd.strip():
        return
    result = process_command(cmd)
    console.insert(tk.END, f">> {cmd}\n{result}\n\n")
    console.see(tk.END)
    entry.delete(0, tk.END)

def start_voice(console):
    text = listen_once()
    if not text:
        console.insert(tk.END, "[Voice] Could not understand.\n\n")
        return

    console.insert(tk.END, f"[Voice] {text}\n")
    result = process_command(text)
    console.insert(tk.END, f"{result}\n\n")
    console.see(tk.END)

def browse_folder(label):
    path = filedialog.askdirectory()
    if path:
        set_base_dir(path)
        label.config(text=f"Working Directory: {path}")

def launch_ui():
    root = tk.Tk()
    root.title("OrbitOS")
    root.geometry("700x500")

   
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=6)
    root.grid_columnconfigure(0, weight=1)


    title = tk.Label(root, text="OrbitOS", font=("Arial", 18, "bold"))
    title.grid(row=0, column=0, sticky="n", pady=10)

  
    top_frame = tk.Frame(root)
    top_frame.grid(row=1, column=0, sticky="ew", padx=10)
    top_frame.grid_columnconfigure(0, weight=5)
    top_frame.grid_columnconfigure(1, weight=1)
    top_frame.grid_columnconfigure(2, weight=1)

    entry = tk.Entry(top_frame, font=("Arial", 12))
    entry.grid(row=0, column=0, sticky="ew", padx=5)

    run_btn = tk.Button(top_frame, text="Run",
                        command=lambda: run_command(entry, console))
    run_btn.grid(row=0, column=1, sticky="ew", padx=5)

    voice_btn = tk.Button(top_frame, text="Voice",
                          command=lambda: start_voice(console))
    voice_btn.grid(row=0, column=2, sticky="ew", padx=5)

 
    dir_frame = tk.Frame(root)
    dir_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 0))
    dir_frame.grid_columnconfigure(0, weight=6)
    dir_frame.grid_columnconfigure(1, weight=1)

    dir_label = tk.Label(dir_frame,
                         text="Working Directory: " + os.getcwd(),
                         anchor="w",
                         wraplength=500)
    dir_label.grid(row=0, column=0, sticky="ew", padx=5)

    browse_btn = tk.Button(dir_frame, text="Browse",
                            command=lambda: browse_folder(dir_label))
    browse_btn.grid(row=0, column=1, sticky="ew", padx=5)

    # Console
    console = scrolledtext.ScrolledText(root, font=("Consolas", 11))
    console.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)

    # Make console expand the most
    root.grid_rowconfigure(3, weight=10)

    root.mainloop()
