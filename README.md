# An NLP-Based Intelligent Agent for System Automation

This repository contains the implementation of an NLP-driven intelligent voice-based agent that enables users to automate system-level tasks using natural language through voice or text commands.  

The system integrates:
- Speech Recognition  
- Natural Language Processing (NLP)  
- Machine Learning–based intent classification  

to interpret commands and perform actions such as file manipulation and basic system automation.

The project is designed with a modular and extensible architecture, making it suitable for:
- Academic use  
- Experimentation  
- Research projects  
- Future feature expansion  

---

## Features

- Voice and text-based command input  
- NLP-based intent recognition using a trained ML model  
- File system automation (create, delete, list files/folders)  
- Confidence-based intent handling  
- Context-aware working directory selection  
- Modular architecture (UI, NLP, controller, skills)  
- Offline-capable core functionality  
- OCR readiness using Tesseract (for future image/text recognition features)  

---

## System Architecture Overview

The system follows a layered architecture:

- **UI Layer**
  - Desktop GUI (PySide6)
  - Displays logs, responses, and system state  

- **Controller Layer**
  - Handles dialog flow
  - Manages confirmations and undo
  - Connects UI with skills  

- **NLP Layer**
  - Tokenization and preprocessing
  - ML-based intent classification
  - Confidence threshold handling  

- **Skills Layer**
  - File control
  - Application control
  - System interaction  

This separation ensures maintainability and extensibility.

---

## Prerequisites

Before running the project, ensure the following requirements are met:

- Python **3.9 or higher**  
- Windows OS (recommended for full system automation features)  
- A working microphone (for voice input)  
- Git (optional, for cloning the repository)  

---

## Getting the Project

-> Download as a ZIP folder from code.

## Creating the virtual environment:

###Creating the environment;
python -m venv venv

### Activating the environment:
venv\sccripts\activate

## Install required dependencies
pip install -r requirements.txt

## INstalling OCR Application (TESSERACT)
### Install official installer from:
https://github.com/UB-Mannheim/tesseract/wiki

Run the installer from downloads and keel the default installation directory at:
C:\Program Files\Tesseract-OCR\

## Add Tesseract to PATH
Step 3: Add Tesseract to System PATH

Press Windows + R

Type sysdm.cpl and press Enter

Open the Advanced tab

Click Environment Variables

Under System variables, select Path

Click Edit → New

Add the following path:

C:\Program Files\Tesseract-OCR\


Click OK on all dialogs to save changes
---

## Configure Tesseract Path in Python

If required by the code, explicitly configure the Tesseract executable path:

import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


This ensures OCR works even if PATH resolution fails.
---

### Train the NLP Model

The NLP intent classification model must be retrained when:

The dataset is updated

New intents are added

The model architecture is modified

Run the training script:

python core/train_intent_model.py


This will generate:

The trained model file

Tokenizer and label encoder artifacts

---
### Run the Application

Start the intelligent agent by running:

python main.py


Once running, the assistant can accept:

Text commands via the UI

Voice commands via microphone input