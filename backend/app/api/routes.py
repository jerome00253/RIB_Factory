from fastapi import APIRouter, File, UploadFile, HTTPException
from app.models.schemas import AnalyzeResponse, ValidationStatus
from app.services.ocr import OCRService
from app.services.image import load_image_from_bytes, preprocess_image, load_pdf_pages_from_bytes
from app.services.parser import parse_rib

router = APIRouter()

from fastapi.responses import StreamingResponse
import json
import asyncio

@router.post("/analyze")
async def analyze_rib(file: UploadFile = File(...)):
    """
    Analyze an uploaded RIB image or PDF.
    Returns a STREAM of results (one per page) using NDJSON.
    """
    if not file.content_type.startswith("image/") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be an image or PDF")
    
    try:
        contents = await file.read()
        is_pdf = file.content_type == "application/pdf"
        
        if is_pdf:
            images = load_pdf_pages_from_bytes(contents)
        else:
            img = load_image_from_bytes(contents)
            images = [img] if img is not None else []
                
        if not images:
             raise HTTPException(status_code=400, detail="Invalid file content or empty PDF")

        async def generate_results():
            ocr_service = OCRService()
            for idx, image in enumerate(images):
                try:
                    # Preprocess & OCR & Parse
                    processed_image = preprocess_image(image)
                    raw_text = ocr_service.predict(processed_image)
                    result = parse_rib(raw_text)
                    
                    if is_pdf:
                        result.page_number = idx + 1
                    
                    # Yield as JSON line
                    yield json.dumps(result.dict()) + "\n"
                    
                    # Small sleep to ensure event loop yields if processing many files
                    await asyncio.sleep(0.01)
                except Exception as e:
                    print(f"Error on page {idx}: {e}")
                    # We can yield an error object or just skip
                    continue

        return StreamingResponse(generate_results(), media_type="application/x-ndjson")

    except Exception as e:
        print(f"Error initializing analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

