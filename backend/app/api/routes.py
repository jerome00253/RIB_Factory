from fastapi import APIRouter, File, UploadFile, HTTPException
from app.models.schemas import AnalyzeResponse, ValidationStatus
from app.services.ocr import OCRService
from app.services.image import load_image_from_bytes, preprocess_image, load_pdf_pages_from_bytes
from app.services.parser import parse_rib

router = APIRouter()

@router.post("/analyze", response_model=list[AnalyzeResponse])
async def analyze_rib(file: UploadFile = File(...)):
    """
    Analyze an uploaded RIB image or PDF.
    Returns a LIST of results (one per page if multi-page).
    """
    if not file.content_type.startswith("image/") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be an image or PDF")
    
    try:
        contents = await file.read()
        
        # 1. Load Images (List)
        images = []
        is_pdf = file.content_type == "application/pdf"
        
        if is_pdf:
            images = load_pdf_pages_from_bytes(contents)
        else:
            img = load_image_from_bytes(contents)
            if img is not None:
                images = [img]
            
        if not images:
             raise HTTPException(status_code=400, detail="Invalid file content or empty PDF")
             
        # 2. Process each page
        ocr_service = OCRService()
        results = []
        
        for idx, image in enumerate(images):
            # Preprocess
            processed_image = preprocess_image(image)
            
            # OCR
            raw_text = ocr_service.predict(processed_image)
            
            # Parse
            result = parse_rib(raw_text)
            
            # Add Page context if PDF
            if is_pdf:
                result.page_number = idx + 1
                
            results.append(result)
            
        # 3. Filter Results
        # Keep only valid or warning results (where something was found)
        # If nothing found at all, return the first failure to show the error
        useful_results = [r for r in results if r.data.iban or r.data.bic] 
        # Note: checking data.iban covers VALID and WARNING status usually
        
        if useful_results:
            return useful_results
        
        # If nothing found, return the result with highest confidence (or just the first one)
        # Sort by confidence descending
        results.sort(key=lambda x: x.confidence_score, reverse=True)
        return [results[0]]
        
    except Exception as e:
        print(f"Error processing file: {e}")
        # Return a generic error in a list structure if we can, or 500
        # For 500 let standard handler catch it
        raise HTTPException(status_code=500, detail=str(e))
