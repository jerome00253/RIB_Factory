export interface RibData {
  iban: string | null;
  bic: string | null;
  owner_name: string | null;
  bank_name: string | null;
}

export interface AnalyzeResponse {
  status: 'valid' | 'warning' | 'invalid';
  confidence_score: number;
  extraction_method?: string | null;
  checksum_valid: boolean;
  rib_key_valid?: boolean | null;
  validation_details?: string[] | null;
  page_number?: number | null;
  data: RibData;
  message: string | null;
}

export async function analyzeRib(file: File): Promise<AnalyzeResponse[]> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('http://localhost:8000/api/v1/analyze', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Erreur lors de l\'analyse');
  }

  return response.json();
}
