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

export async function analyzeRib(
  file: File, 
  onResult: (result: AnalyzeResponse) => void
): Promise<void> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/v1/analyze', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    let errorMessage = 'Erreur lors de l\'analyse';
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = `Erreur Serveur: ${typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail)}`;
      } else {
        errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`;
      }
    } catch (e) {
      errorMessage = `Erreur HTTP ${response.status}: ${response.statusText}`;
    }
    console.error("Backend Error Response:", errorMessage);
    throw new Error(errorMessage);
  }

  // Handle Streaming Response (NDJSON)
  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Impossible de lire le flux de réponse");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");

    // Keep the last partial line in buffer
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.trim()) {
        try {
          const result = JSON.parse(line) as AnalyzeResponse;
          onResult(result);
        } catch (e) {
          console.error("Erreur de parsing NDJSON:", e, line);
        }
      }
    }
  }

  // Process any remaining text in buffer
  if (buffer.trim()) {
    try {
      const result = JSON.parse(buffer) as AnalyzeResponse;
      onResult(result);
    } catch (e) {
      console.error("Erreur de parsing NDJSON (final):", e, buffer);
    }
  }
}
