# An NLP-Based Intelligent Agent for System Automation

This repository contains the implementation of an **NLP-driven intelligent agent** that enables users to automate **system-level tasks** using **natural language**, through either **voice commands** or **text-based input**.

The system integrates the following core components:

- Speech Recognition  
- Natural Language Processing (NLP)  
- Machine Learning–based Intent Classification  

These components collectively interpret user commands and execute actions such as file manipulation, application control, and basic system automation.

The project is designed with a **modular and extensible architecture**, making it suitable for:

- Academic use  
- Experimentation and prototyping  
- Research projects  
- Future feature expansion  

---

## 1. Features

The intelligent agent provides the following functionality:

- Voice-based command input using a microphone  
- Text-based command input via a graphical user interface  
- NLP-based intent recognition using a trained ML model  
- Confidence-based intent validation before execution  
- File system automation:
  - Create files and folders  
  - Delete files and folders  
  - List directory contents  
  - Navigate directories  
- Context-aware working directory management  
- Modular architecture (UI, NLP, Controller, Skills)  
- Offline-capable core functionality  
- OCR readiness using **Tesseract OCR** for future image/text recognition  

---

## 2. System Architecture Overview

The system follows a **layered architecture**, ensuring separation of concerns, maintainability, and scalability.

### 2.1 UI Layer

- Desktop GUI built using **PySide6**  
- Displays:
  - User inputs  
  - Assistant responses  
  - Execution logs  
  - System status  

### 2.2 Controller Layer

- Manages dialog flow and command execution lifecycle  
- Handles:
  - User confirmations  
  - Undo or correction logic  
  - Error handling and fallback responses  
- Acts as a bridge between UI, NLP, and Skills layers  

### 2.3 NLP Layer

- Performs text preprocessing:
  - Cleaning  
  - Tokenization  
  - Normalization  
- Uses a trained ML model for:
  - Intent classification  
  - Confidence scoring  
- Applies confidence thresholds to ensure safe execution  

### 2.4 Skills Layer

- Encapsulates system-level actions, including:
  - File and directory operations  
  - Application control (open, close, discovery)  
  - System interactions:
    - Volume control  
    - Power management  
    - Alarms and reminders  
    - System status queries  
    - Notes handling  
    - Screen analysis (future scope)  

---

## 3. Prerequisites

Before running the project, ensure the following requirements are met:

- Python **3.9 or higher**  
- Windows OS (recommended for full automation support)  
- A working microphone (for voice input)  
- Git (optional, for cloning the repository)  

---

## 4. Getting the Project

You can obtain the project by:

- Downloading the repository as a ZIP file using the **Code** menu  
- Extracting it into a suitable local directory  

---

## 5. Virtual Environment Setup

### 5.1 Create the Virtual Environment

Create a Python virtual environment to isolate project dependencies:

```bash
python -m venv venv
```

### 5.2 Activate the Virtual Environment (Windows)

Activate the environment using:

```bash
venv\Scripts\activate
```

---

## 6. Installing Required Dependencies

With the virtual environment activated, install all required dependencies:

```bash
pip install -r requirements.txt
```

---

## 7. OCR (Tesseract) Installation

### 7.1 Install Tesseract OCR

Download and install Tesseract OCR from the official Windows builds page:

```
https://github.com/UB-Mannheim/tesseract/wiki
```

Use the default installation directory:

```
C:\Program Files\Tesseract-OCR\
```

---

### 7.2 Add Tesseract to the System PATH

1. Press **Windows + R**, type `sysdm.cpl`, and press Enter  
2. Open the **Advanced** tab  
3. Click **Environment Variables**  
4. Under **System variables**, select **Path** and click **Edit**  
5. Click **New** and add:

```
C:\Program Files\Tesseract-OCR\
```

6. Click **OK** on all dialogs to save the changes  

---

### 7.3 Configure Tesseract Path in Python (Optional)

If explicit configuration is required, add the following to your Python code:

```python
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

This ensures OCR works even if PATH resolution fails.

---

## 8. Gemini API Key Configuration

To enable Gemini-based features:

1. Obtain a **Gemini API key**  
2. Create a `.env` file in the project root directory  
3. Add the following line:

```
GEMINI_API_KEY="api_key_here"
```

---

## 9. Training the NLP Model

Retrain the intent classification model when:

- The dataset is updated  
- New intents are added  
- The model architecture changes  

Run the training script:

```bash
python core/train_intent_model.py
```

This will generate:

- Trained model file  
- Tokenizer artifacts  
- Label encoder artifacts  

---

## 10. Running the Application

Start the intelligent agent using:

```bash
python main.py
```

Once running, the assistant accepts:

- Text commands via the GUI  
- Voice commands via microphone input  

Use the interface to issue commands, monitor logs, and observe system behavior.

---

## 11. Notes

- Ensure microphone permissions are correctly configured  
- Run the application with appropriate system permissions  
- The modular design allows easy addition of new skills and intents  

---