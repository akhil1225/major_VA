# An NLP-Based Intelligent Agent for System Automation

This repository contains the implementation of an **NLP-driven intelligent voice-based agent** that enables users to automate system-level tasks using natural language through **voice or text commands**.  
The system integrates **Speech Recognition, Natural Language Processing (NLP), and Machine Learning–based intent classification** to interpret commands and perform actions such as file manipulation and basic system automation.

The project is designed with a **modular and extensible architecture**, making it suitable for academic use, experimentation, and future enhancements.

---

## ✨ Features

- Voice and text-based command input  
- NLP-based intent recognition using a trained ML model  
- File system automation (create, delete, list files/folders)  
- Confidence-based intent handling  
- Context-aware working directory selection  
- Modular architecture (UI, NLP, control, skills)  
- Offline-capable core functionality  



---

## 🔧 Prerequisites

- **Python 3.9 or higher**
- Git (optional, for cloning)
- A working microphone (for voice commands)

---

## 📥 Getting the Project

### Option 1: Clone Using Git


git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>

Option 2: Download as ZIP

Click Code → Download ZIP on the GitHub repository page

Extract the ZIP file

Open a terminal in the extracted folder


Then Create a venv -> virtual environment in the folder 

python -m venv venv

venv\Scripts\activate


---

# Install Required dependencies

pip install -r requirements.txt

# First, train the NLP Model, has to be trained everytime the dataset has been changed or the model has been modified

python core/train_intent_model.py

---

# Run the application

python main.py
