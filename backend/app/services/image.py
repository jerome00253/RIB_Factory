import cv2
import numpy as np
import pypdfium2 as pdfium

def load_image_from_bytes(file_bytes: bytes) -> np.ndarray:
    """Convert bytes trigger to OpenCV Image format"""
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def load_pdf_pages_from_bytes(file_bytes: bytes) -> list[np.ndarray]:
    """Convert ALL pages of a PDF bytes to a list of OpenCV Image format"""
    try:
        pdf = pdfium.PdfDocument(file_bytes)
        if len(pdf) == 0:
            return []
        
        cv_images = []
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            # Render at 2x scale for better OCR quality
            bitmap = page.render(scale=2.0)
            pil_image = bitmap.to_pil()
            # Convert RGB (PIL) to BGR (OpenCV)
            cv_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            cv_images.append(cv_img)
            
        return cv_images
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return []

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
