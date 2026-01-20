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
            print("Loading DocTR model...")
            cls._model = ocr_predictor(det_arch='db_resnet50', reco_arch='crnn_vgg16_bn', pretrained=True)
            print("DocTR model loaded.")
        return cls._instance

    def predict(self, image: np.ndarray) -> str:
        """
        Run OCR on the image and return full extracted text.
        """
        try:
            # The predictor __call__ supports List[np.ndarray] directly
            result = self._model([image])
        except Exception as e:
            print(f"ERROR in OCR: {e}")
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
