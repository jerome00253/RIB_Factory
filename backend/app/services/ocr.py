from doctr.io import DocumentFile
from doctr.models import ocr_predictor
import numpy as np

class OCRService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OCRService, cls).__new__(cls)
            # Initialize model only once
            # pretrained=True will try to download, but in offline mode 
            # we rely on the docker build having cached it or volume mapping.
            print("Loading DocTR model...")
            cls._model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
            print("DocTR model loaded.")
        return cls._instance

    def predict(self, image: np.ndarray) -> str:
        """
        Run OCR on the image and return full extracted text.
        """
        print(f"DEBUG: OCR Predict called. Input Type: {type(image)}")
        if isinstance(image, np.ndarray):
            print(f"DEBUG: Image Shape: {image.shape}")
        
        try:
            # Bypass DocumentFile which seems to assume files/paths in some versions
            # The predictor __call__ supports List[np.ndarray] directly
            print("DEBUG: Calling model directly with [image]")
            result = self._model([image])
            print("DEBUG: Model inference complete.")
        except Exception as e:
            print(f"DEBUG: Error in DocTR internal: {e}")
            raise e
        
        # Aggregating text result
        full_text = ""
        for page in result.pages:
            for block in page.blocks:
                for line in block.lines:
                    for word in line.words:
                        full_text += word.value + " "
                    full_text += "\n"
        
        return full_text
