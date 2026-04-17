import pytesseract
import cv2

def extract_text(image_path):
    try:
        img = cv2.imread(image_path)
        # Convert to RGB for better tesseract reading
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        text = pytesseract.image_to_string(img_rgb)
        return text.strip()
    except pytesseract.TesseractNotFoundError:
        return "[Error: Tesseract-OCR is not installed. Please install it system-level to read the screen.]"
    except Exception as e:
        return f"[Error extracting text: {e}]"
