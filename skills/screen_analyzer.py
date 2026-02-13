# skills/screen_analyzer.py

from typing import Optional, Tuple

from PIL import ImageGrab, ImageDraw, ImageOps, Image
import win32gui  # type: ignore
import win32con  # type: ignore
import pytesseract # type: ignore

from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer # type: ignore
import torch # type: ignore


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"



_CAPTION_MODEL_NAME = "nlpconnect/vit-gpt2-image-captioning"
_MAX_CAPTION_SIZE: Tuple[int, int] = (1024, 1024)



_caption_model: VisionEncoderDecoderModel | None = None
_feature_extractor: ViTImageProcessor | None = None
_tokenizer: AutoTokenizer | None = None
_device = "cuda" if torch.cuda.is_available() else "cpu"


def _load_caption_model_once() -> None:
    global _caption_model, _feature_extractor, _tokenizer
    if _caption_model is not None:
        return

    _caption_model = VisionEncoderDecoderModel.from_pretrained(_CAPTION_MODEL_NAME)
    _feature_extractor = ViTImageProcessor.from_pretrained(_CAPTION_MODEL_NAME)
    _tokenizer = AutoTokenizer.from_pretrained(_CAPTION_MODEL_NAME)

    _caption_model.to(_device) # type: ignore
    _caption_model.eval() # pyright: ignore[reportOptionalMemberAccess]




def _get_orbitos_hwnd() -> Optional[int]:
    return win32gui.FindWindow(None, "OrbitOS – Intelligent System Agent")


def _get_orbitos_window_rect() -> Optional[tuple[int, int, int, int]]:
    hwnd = _get_orbitos_hwnd()
    if not hwnd:
        return None
    return win32gui.GetWindowRect(hwnd)


def _get_foreground_window_rect() -> Optional[tuple[int, int, int, int]]:
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None
    return win32gui.GetWindowRect(hwnd)


def _get_window_client_rect(hwnd: int) -> tuple[int, int, int, int]:
    """
    Return client-area rect of a window in screen coordinates.
    """
 
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
  
    pt = win32gui.ClientToScreen(hwnd, (left, top))
    return (pt[0], pt[1], pt[0] + (right - left), pt[1] + (bottom - top))


def _capture_full_screen() -> Image.Image:
    return ImageGrab.grab()


def _capture_region(rect: tuple[int, int, int, int]) -> Image.Image:
    return ImageGrab.grab(bbox=rect)


def _mask_orbitos_window(img: Image.Image) -> Image.Image:
    rect = _get_orbitos_window_rect()
    if not rect:
        return img

    left, top, right, bottom = rect
    masked = img.copy()
    draw = ImageDraw.Draw(masked)
    draw.rectangle([left, top, right, bottom], fill=(0, 0, 0))
    return masked




def _describe_image_with_model(pil_image: Image.Image) -> str:
    _load_caption_model_once()

    assert _caption_model is not None
    assert _feature_extractor is not None
    assert _tokenizer is not None

    img = pil_image.copy()
    img.thumbnail(_MAX_CAPTION_SIZE)

    pixel_values = _feature_extractor(img, return_tensors="pt").pixel_values.to(_device)

    with torch.no_grad():
        output_ids = _caption_model.generate(
            pixel_values,
            max_new_tokens=40,
            num_beams=4,
            early_stopping=True,
        )

    caption = _tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return caption.strip()


def describe_current_screen() -> str:

    try:
        fg_hwnd = win32gui.GetForegroundWindow()
        orbit_hwnd = _get_orbitos_hwnd()

        use_full_screen = False

        if not fg_hwnd or (orbit_hwnd and fg_hwnd == orbit_hwnd):
            use_full_screen = True

        if use_full_screen:
            img = _capture_full_screen()
            img = _mask_orbitos_window(img)
            fg_title = None
        else:
         
            rect = _get_window_client_rect(fg_hwnd)
            img = _capture_region(rect)
            fg_title = win32gui.GetWindowText(fg_hwnd).strip() or None

        caption = _describe_image_with_model(img) or "a window on your desktop"

        if fg_title:
            return f"On your screen, I see the window '{fg_title}', which looks like {caption}."
        else:
            return f"On your screen, I see {caption}."
    except Exception as e:
        return f"I could not analyze the screen properly: {e}"




def read_screen_text() -> str:

    try:
        fg_hwnd = win32gui.GetForegroundWindow()
        orbit_hwnd = _get_orbitos_hwnd()

        if fg_hwnd and orbit_hwnd and fg_hwnd != orbit_hwnd:
          
            rect = _get_window_client_rect(fg_hwnd)
            img = _capture_region(rect)
        else:
         
            img = _capture_full_screen()
            img = _mask_orbitos_window(img)

        gray = ImageOps.grayscale(img)
        text = pytesseract.image_to_string(gray).strip()

        if not text:
            return "I could not read any text from the screen."
        return text
    except Exception as e:
        return f"I could not read text from the screen: {e}"



def get_foreground_window_info() -> str:
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
