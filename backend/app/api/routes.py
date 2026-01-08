from fastapi import APIRouter, File, UploadFile, HTTPException
from app.models.schemas import AnalyzeResponse
from app.services.ocr import OCRService
from app.services.image import load_image_from_bytes, preprocess_image, load_pdf_from_bytes
from app.services.parser import parse_rib

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_rib(file: UploadFile = File(...)):
    """
    Analyze an uploaded RIB image or PDF.
    1. Read file
    2. Convert PDF to Image if needed
    3. Preprocess
    4. OCR (DocTR)
    5. Parse & Validate
    """
    if not file.content_type.startswith("image/") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be an image or PDF")
    
    try:
        contents = await file.read()
        
        # 1. Processing
        image = None
        if file.content_type == "application/pdf":
            image = load_pdf_from_bytes(contents)
        else:
            image = load_image_from_bytes(contents)
            
        if image is None:
             raise HTTPException(status_code=400, detail="Invalid file content")
             
        processed_image = preprocess_image(image)
        
        # 2. OCR
        ocr_service = OCRService()
        raw_text = ocr_service.predict(processed_image)
        
        # 3. Parsing
        result = parse_rib(raw_text)
        
        return result
        
    except Exception as e:
        print(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))
