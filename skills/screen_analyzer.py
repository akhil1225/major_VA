# skills/screen_analyzer.py

from typing import Optional
from PIL import ImageGrab, ImageDraw, Image
import win32gui  # type: ignore

from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import torch

# ------------- LOAD PRETRAINED CAPTIONING MODEL -------------

_MODEL_NAME = "nlpconnect/vit-gpt2-image-captioning"

_model: VisionEncoderDecoderModel | None = None
_feature_extractor: ViTImageProcessor | None = None
_tokenizer: AutoTokenizer | None = None
_device = "cuda" if torch.cuda.is_available() else "cpu"


def _load_model_once():
    global _model, _feature_extractor, _tokenizer
    if _model is not None:
        return

    _model = VisionEncoderDecoderModel.from_pretrained(_MODEL_NAME)
    _feature_extractor = ViTImageProcessor.from_pretrained(_MODEL_NAME)
    _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)

    _model.to(_device)
    _model.eval()


# ------------- WINDOW / SCREEN HELPERS -------------

def _get_orbitos_window_rect() -> Optional[tuple[int, int, int, int]]:
    """
    Find the OrbitOS window by its title and return (left, top, right, bottom).
    Returns None if not found.
    """
    hwnd = win32gui.FindWindow(None, "OrbitOS – Intelligent System Agent")
    if not hwnd:
        return None
    return win32gui.GetWindowRect(hwnd)


def _capture_full_screen() -> Image.Image:
    # Capture full primary screen
    return ImageGrab.grab()


def _mask_orbitos_window(img: Image.Image) -> Image.Image:
    rect = _get_orbitos_window_rect()
    if not rect:
        return img

    left, top, right, bottom = rect
    masked = img.copy()
    draw = ImageDraw.Draw(masked)
    # Fill OrbitOS window area with black so it doesn't dominate the caption
    draw.rectangle([left, top, right, bottom], fill=(0, 0, 0))
    return masked


# ------------- CAPTIONING / OCR API -------------

def _describe_image_with_model(pil_image: Image.Image) -> str:
    _load_model_once()

    assert _model is not None
    assert _feature_extractor is not None
    assert _tokenizer is not None

    # Prepare image
    pixel_values = _feature_extractor(
        pil_image, return_tensors="pt"
    ).pixel_values.to(_device)

    with torch.no_grad():
        output_ids = _model.generate(
            pixel_values,
            max_new_tokens=40,
            num_beams=4,
            early_stopping=True,
        )

    caption = _tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return caption.strip()


def describe_current_screen() -> str:
    """
    High-level description of the current screen excluding OrbitOS window
    using a pretrained image captioning model.
    """
    try:
        img = _capture_full_screen()
        img = _mask_orbitos_window(img)
        caption = _describe_image_with_model(img)
        # Make the sentence more natural for speech
        return f"On your screen, I see {caption}."
    except Exception as e:
        return f"I could not analyze the screen properly: {e}"


def read_screen_text() -> str:
    """
    Placeholder for OCR-based screen text reading.
    You can later integrate screen-ocr or pytesseract here.
    """
    return "Reading text from the screen with OCR is not implemented yet."


def get_foreground_window_info() -> str:
    """
    Returns the title of the currently active window.
    """
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return "I could not detect any active window."
        title = win32gui.GetWindowText(hwnd).strip()
        if not title:
            return "The active window has no title."
        return f"The active window is {title}."
    except Exception as e:
        return f"I could not get the active window information: {e}"
