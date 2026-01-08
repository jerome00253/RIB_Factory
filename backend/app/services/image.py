import cv2
import numpy as np
from pdf2image import convert_from_bytes

def load_image_from_bytes(file_bytes: bytes) -> np.ndarray:
    """Convert bytes trigger to OpenCV Image format"""
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def load_pdf_from_bytes(file_bytes: bytes) -> np.ndarray:
    """Convert first page of PDF bytes to OpenCV Image format"""
    try:
        images = convert_from_bytes(file_bytes)
        if not images:
            return None
        # Take first page
        pil_image = images[0]
        # Convert RGB (PIL) to BGR (OpenCV)
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return None

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Basic preprocessing pipeline for OCR:
    1. Grayscale
    2. Noise reduction
    3. Thresholding (optional, DocTR handles RBG well but cleaner is better)
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Denoising
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # Optional: deskewing could be added here if DocTR struggles directly
    
    return image # DocTR actually works well on RGB, we return original for now or slightly enhanced
