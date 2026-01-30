import os
import shutil

BASE_DIR = os.getcwd()

def set_base_dir(path):
    global BASE_DIR
    BASE_DIR = path

def create_file(name):
    path = os.path.join(BASE_DIR, name)
    if os.path.exists(path):
        return f"File '{name}' already exists."
    open(path, 'w').close()
    return f"File '{name}' created in {BASE_DIR}"

def delete_file(name):
    path = os.path.join(BASE_DIR, name)
    if not os.path.exists(path):
        return f"File '{name}' not found."
    os.remove(path)
    return f"File '{name}' deleted."

def create_folder(name):
    path = os.path.join(BASE_DIR, name)
    if os.path.exists(path):
        return f"Folder '{name}' already exists."
    os.mkdir(path)
    return f"Folder '{name}' created in {BASE_DIR}"

def delete_folder(name):
    path = os.path.join(BASE_DIR, name)
    if not os.path.exists(path):
        return f"Folder '{name}' not found."
    shutil.rmtree(path)
    return f"Folder '{name}' deleted."

def list_items():
    items = os.listdir(BASE_DIR)
    if not items:
        return "Directory is empty."
    return "\n".join(items)
