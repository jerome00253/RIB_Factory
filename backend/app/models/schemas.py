from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class ValidationStatus(str, Enum):
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"

class RibData(BaseModel):
    iban: Optional[str] = Field(None, description="International Bank Account Number")
    bic: Optional[str] = Field(None, description="Bank Identifier Code")
    owner_name: Optional[str] = Field(None, description="Nom du titulaire du compte")
    bank_name: Optional[str] = Field(None, description="Nom de la banque")
    
class AnalyzeResponse(BaseModel):
    status: ValidationStatus
    confidence_score: float = Field(..., ge=0, le=100, description="Global confidence score of the extraction")
    extraction_method: Optional[str] = Field(None, description="Method used to find the IBAN (Direct, Corrected, Reconstructed)")
    checksum_valid: bool = Field(False, description="Indicates if the found IBAN passed the checksum validation")
    rib_key_valid: Optional[bool] = Field(None, description="Indicates if the French RIB key is valid (France only)")
    validation_details: Optional[list[str]] = Field(None, description="List of specific validation errors or details")
    page_number: Optional[int] = Field(None, description="Page number if extracted from a multi-page document")
    data: RibData
    message: Optional[str] = None
