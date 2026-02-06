import os
import shutil

BASE_DIR = os.getcwd()

def get_base_dir():
    return BASE_DIR


def set_base_dir(path):
    global BASE_DIR
    BASE_DIR = path

def create_file(name):
    path = os.path.join(BASE_DIR, name)
    folder_name = os.path.basename(BASE_DIR)
    if os.path.exists(path):
        return f"The file named {name} already exists in the folder {folder_name}"
    open(path, 'w').close()
    return f"A new file named {name} has been created in the folder {folder_name}."


def delete_file(name):
    path = os.path.join(BASE_DIR, name)
    folder_name = os.path.basename(BASE_DIR)
    if not os.path.exists(path):
        return f"I could not find a file named {name}."
    os.remove(path)
    return f"The file named {name} has been successfully deleted from {folder_name}."

def create_folder(name):
    path = os.path.join(BASE_DIR, name)
    folder_name = os.path.basename(BASE_DIR)
    if os.path.exists(path):
        return f"Folder '{name}' already exists."
    os.mkdir(path)
    return f"Folder '{name}' created in the parent folder {folder_name}"

def delete_folder(name):
    path = os.path.join(BASE_DIR, name)
    if not os.path.exists(path):
        return f"Folder '{name}' not found."
    shutil.rmtree(path)
    return f"Folder '{name}' deleted."

def list_items():
    folder_name = os.path.basename(BASE_DIR)
    items = os.listdir(BASE_DIR)
    if not items:
        return "The selected folder is empty."
    return (
        
        ", ".join(items)
    )

def get_current_folder():
    return os.path.basename(BASE_DIR)

def navigate_to_folder(folder_name):
    global BASE_DIR
    target = os.path.join(BASE_DIR, folder_name)

    if not os.path.exists(target):
        return f"I could not find a folder named {folder_name}."

    if not os.path.isdir(target):
        return f"{folder_name} is not a folder."
    
    BASE_DIR = os.path.abspath(target)


    BASE_DIR = target
    return f"I have moved into the folder {folder_name}."

def go_back():
    global BASE_DIR
    parent = os.path.dirname(BASE_DIR)

    if parent == BASE_DIR:
        return "You are already at the root directory."

    BASE_DIR = parent
    return f"I have moved back to the folder {os.path.basename(BASE_DIR)}."
