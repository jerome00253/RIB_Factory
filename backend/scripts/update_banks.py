import json
import os
import urllib.request
import csv
import io

# Sources pour l'enrichissement
BIC_SOURCE_CSV = "https://raw.githubusercontent.com/franckverrot/codes-bic-france/main/codes-bic-france.csv"

def update_from_external():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    resources_dir = os.path.join(base_dir, "app", "resources")
    os.makedirs(resources_dir, exist_ok=True)
    
    bics_path = os.path.join(resources_dir, "bics_fr.json")
    
    # Update BIC to Name mapping
    try:
        print(f"Téléchargement du mapping BIC depuis {BIC_SOURCE_CSV}...")
        with urllib.request.urlopen(BIC_SOURCE_CSV) as response:
            content = response.read().decode('utf-8')
            lines = content.splitlines()
            
            bic_mapping = {}
            # Use csv reader for better parsing
            reader = csv.reader(io.StringIO(content))
            next(reader) # Skip header
            
            for row in reader:
                if len(row) >= 3:
                    name = row[0].strip()
                    bic = row[2].strip()
                    if len(bic) >= 8:
                        code_8 = bic[:8].upper()
                        # Shortest name is usually the most generic
                        if code_8 not in bic_mapping or len(name) < len(bic_mapping[code_8]):
                            bic_mapping[code_8] = name
            
            with open(bics_path, 'w', encoding='utf-8') as f:
                json.dump(bic_mapping, f, indent=4, ensure_ascii=False)
            
            print(f"Mise à jour BIC terminée : {len(bic_mapping)} entrées uniques dans bics_fr.json")
            
    except Exception as e:
        print(f"Erreur mise à jour BIC : {e}")

if __name__ == "__main__":
    update_from_external()
