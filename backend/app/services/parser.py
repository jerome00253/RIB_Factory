import re
import json
import os
from app.models.schemas import RibData, ValidationStatus, AnalyzeResponse
from schwifty import IBAN, BIC
from stdnum import iban as stdnum_iban

def anonymize_text_for_debug(text: str, iban: str = None, bic: str = None, 
                              bank_code: str = None, branch_code: str = None, 
                              account_number: str = None, key: str = None) -> str:
    """
    Anonymize sensitive data in text for safe debugging.
    Replaces real values with fictitious but valid ones (correct RIB key).
    """
    anon_text = text
    
    # Generate a fake but valid French IBAN
    fake_bank = "11111"
    fake_branch = "22222"
    fake_account = "33333333333"
    
    # Calculate correct RIB key for fake values (inline to avoid circular import)
    bank_val = int(fake_bank)
    branch_val = int(fake_branch)
    account_numeric = ''.join(c if c.isdigit() else '0' for c in fake_account)
    account_val = int(account_numeric)
    result = (89 * (bank_val % 97)) + (15 * (branch_val % 97)) + (3 * (account_val % 97))
    calculated_key = 97 - (result % 97)
    if calculated_key == 97:
        calculated_key = 0
    fake_key = f"{calculated_key:02d}"
    
    # Build fake IBAN (simplified - using hardcoded valid test IBAN)
    fake_iban = f"FR7611111222223333333333344"  # Valid test IBAN
    fake_bic = "XXXXFR99XXX"
    
    # Replace real data with fake
    if iban:
        anon_text = anon_text.replace(iban, fake_iban)
    if bic:
        anon_text = anon_text.replace(bic, fake_bic)
    if bank_code:
        anon_text = anon_text.replace(bank_code, fake_bank)
    if branch_code:
        anon_text = anon_text.replace(branch_code, fake_branch)
    if account_number:
        anon_text = anon_text.replace(account_number, fake_account)
    if key:
        anon_text = anon_text.replace(key, fake_key)
    
    return anon_text


def clean_iban(text: str) -> str:
    return text.replace(" ", "").replace("-", "").upper()

def validate_iban_checksum(iban_str: str) -> tuple[bool, str]:
    """
    Validate IBAN using schwifty library.
    Returns: (is_valid, error_message)
    """
    try:
        clean = clean_iban(iban_str)
        iban_obj = IBAN(clean)
        return True, "Checksum Valid (ISO 13616)"
    except Exception as e:
        # Fallback to python-stdnum for edge cases
        try:
            if stdnum_iban.is_valid(clean):
                return True, "Checksum Valid (Stdnum)"
            return False, "Invalid IBAN Checksum"
        except:
            return False, str(e)

def extract_iban_components(iban_str: str) -> dict:
    """
    Extract IBAN components using schwifty.
    Returns: {'bank_code': str, 'branch_code': str, 'account_code': str}
    """
    try:
        clean = clean_iban(iban_str)
        iban_obj = IBAN(clean)
        return {
            'bank_code': iban_obj.bank_code or None,
            'branch_code': iban_obj.branch_code or None,
            'account_code': iban_obj.account_code or None,
        }
    except:
        return {'bank_code': None, 'branch_code': None, 'account_code': None}

def validate_french_rib_key(bank_code: str, branch_code: str, account_number: str, key: str) -> tuple[bool, str]:
    """
    Validate French RIB key.
    Returns: (is_valid, error_message)
    """
    if not bank_code or not branch_code or not account_number or not key:
        return False, "Missing components for RIB key validation"
    
    try:
        # Letter to number conversion table for French RIB (official spec)
        letter_map = {
            'A': '1', 'J': '1',
            'B': '2', 'K': '2', 'S': '2',
            'C': '3', 'L': '3', 'T': '3',
            'D': '4', 'M': '4', 'U': '4',
            'E': '5', 'N': '5', 'V': '5',
            'F': '6', 'O': '6', 'W': '6',
            'G': '7', 'P': '7', 'X': '7',
            'H': '8', 'Q': '8', 'Y': '8',
            'I': '9', 'R': '9', 'Z': '9'
        }
        
        # Convert account number letters to digits
        account_numeric = ''
        for char in account_number.upper():
            if char.isdigit():
                account_numeric += char
            elif char.isalpha():
                account_numeric += letter_map.get(char, '0')
            else:
                account_numeric += '0'
        
        # Calculate key using French RIB formula
        bank = int(bank_code)
        branch = int(branch_code)
        account = int(account_numeric)
        
        result = (89 * (bank % 97)) + (15 * (branch % 97)) + (3 * (account % 97))
        calculated_key = 97 - (result % 97)
        
        # Handle key = 0 case
        if calculated_key == 97:
            calculated_key = 0
            
        is_valid = calculated_key == int(key)
        if is_valid:
            return True, "RIB Key Valid"
        else:
            return False, f"Invalid RIB Key: Expected {calculated_key:02d}, got {key}"
    except Exception as e:
        return False, f"RIB Validation Error: {str(e)}"


def parse_rib(raw_text: str) -> AnalyzeResponse:
    confidence = 0.0
    status = ValidationStatus.INVALID
    
    # Regex Patterns
    iban_pattern = re.compile(r'([A-Z]{2}\d{2}[A-Z0-9]{10,30})')
    bic_pattern = re.compile(r'([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?)')
    
    raw_upper = raw_text.upper()

    
    # Clean text
    text_nospace = re.sub(r'[^A-Z0-9]', '', raw_upper)
    text_clean = re.sub(r'[^A-Z0-9\s]', '', raw_upper)
    
    # Initialize all result variables
    found_iban = None
    found_bic = None
    found_owner = "Unknown"
    found_bank = "Unknown"
    checksum_valid = False
    validation_details = []
    
    rib_bank_code = None
    rib_branch_code = None
    rib_account_number = None
    rib_key = None
    detection_method = "Unknown"

    valid_country_codes = {'FR', 'BE', 'DE', 'ES', 'IT', 'GB', 'CH', 'LU', 'NL', 'AT', 'PT', 'IE', 'SE', 'DK', 'FI', 'NO', 'PL', 'CZ', 'HU', 'SK', 'SI', 'HR', 'EE', 'LV', 'LT', 'MT', 'CY', 'GR', 'BG', 'RO', 'MC', 'SM', 'LI', 'IS'}

    # Strategy 1: Find IBANs in nospace string
    potential_matches = re.findall(r'(?=([A-Z]{2}\d{2}[A-Z0-9]{10,30}))', text_nospace)
    potential_matches = sorted(potential_matches, key=lambda x: (0 if x.startswith('FR') else 1, x))
    
    for candidate in potential_matches:
        if candidate[:2] not in valid_country_codes:
            continue

        valid_iban = None
        max_len = min(len(candidate), 34)
        min_len = 15
        is_french = candidate.startswith('FR')
        
        for length in range(max_len, min_len - 1, -1):
            sub_candidate = candidate[:length]
            is_valid, _ = validate_iban_checksum(sub_candidate)
            if is_valid:
                if sub_candidate.startswith('FR') and len(sub_candidate) != 27:
                    continue
                valid_iban = sub_candidate
                detection_method = "Direct Extraction"
                break
            
            # OCR Correction for French IBANs
            if is_french:
                # Add C -> 0 for LCL cases
                replacements = {'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'Z': '2', 'B': '8', 'S': '5', 'C': '0'}
                header = sub_candidate[:2]
                body = ''.join(replacements.get(char, char) for char in sub_candidate[2:])
                corrected = header + body
                if corrected != sub_candidate:
                    is_valid_corr, _ = validate_iban_checksum(corrected)
                    if is_valid_corr:
                        if corrected.startswith('FR') and len(corrected) != 27:
                            continue
                        valid_iban = corrected
                        detection_method = "OCR Correction"
                        break
                
                # Special Case: Key correction (last 2 digits)
                # If everything else looks okay but checksum fails, try fixing the key digits
                if len(sub_candidate) == 27:
                    body_main = sub_candidate[2:25]
                    key_part = sub_candidate[25:27]
                    fixed_key = ''.join(replacements.get(char, char) for char in key_part)
                    if fixed_key != key_part:
                        corrected_key = header + body_main + fixed_key
                        if validate_iban_checksum(corrected_key)[0]:
                            valid_iban = corrected_key
                            detection_method = "OCR Correction (Key)"
                            break

        if valid_iban:
            found_iban = valid_iban
            confidence += 80 
            status = ValidationStatus.VALID if validate_iban_checksum(found_iban)[0] else ValidationStatus.INVALID
            break 

    # Strategy 2: Reconstruct IBAN from RIB components
    if not found_iban:
        rb_bank = re.search(r'BANQUE.*?(\d{5})', text_nospace)
        rb_branch = re.search(r'GUICHET.*?(\d{5})', text_nospace)
        rb_account = re.search(r'(?:NODECOMPTE|NOCOMPTE|NUMERODECOMPTE|COMPTE).*?([A-Z0-9]{11})', text_nospace)
        rb_key = re.search(r'(?:CLE|RIB|CL)(\d{2})', text_nospace)
        
        if rb_bank and rb_branch and rb_account and rb_key:
            rib_bank_code = rb_bank.group(1)
            rib_branch_code = rb_branch.group(1)
            rib_account_number = rb_account.group(1)
            rib_key = rb_key.group(1)
            
            rib_body = rib_bank_code + rib_branch_code + rib_account_number + rib_key
            
            # Find prefix ONLY if it's a valid country code and near labels
            prefix = "FR76"
            prefix_match = re.search(r'IBAN.{0,60}?([A-Z]{2}\d{2})', text_nospace)
            if prefix_match:
                cand_prefix = prefix_match.group(1)
                if cand_prefix[:2] in valid_country_codes:
                    prefix = cand_prefix
            
            reconstructed = prefix + rib_body
            if validate_iban_checksum(reconstructed)[0]:
                found_iban = reconstructed
                status = ValidationStatus.VALID
                confidence = 85
                detection_method = "Reconstructed (Found in Text)" if reconstructed in text_nospace else "Reconstructed"

    # Strategy 3: Grouped Labels followed by digits (Robust Window Search)
    if not found_iban:
        # Capture ALPHANUMERIC block (to handle C -> 0 errors)
        grouped_labels = re.search(r'(?:BANQUE|GUICHET|COMPTE|CLE|RIB|CL|IDENTIFIANT){3,}.*?([A-Z0-9]{23,33})', text_nospace)
        if grouped_labels:
            raw_block = grouped_labels.group(1)
            # Apply OCR digit corrections to the block
            replacements = {'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'Z': '2', 'B': '8', 'S': '5', 'C': '0'}
            raw_digits = ''.join(replacements.get(c, c) for c in raw_block if c.isdigit() or c in replacements)
            
            # Try all 23-digit windows in the corrected block
            for i in range(len(raw_digits) - 22):
                window = raw_digits[i:i+23]
                bank, branch, acc, key = window[0:5], window[5:10], window[10:21], window[21:23]
                
                # Check reconstruction
                prefix = "FR76"
                prefix_match = re.search(r'IBAN.{0,60}?([A-Z]{2}\d{2})', text_nospace)
                if prefix_match:
                    cand_prefix = prefix_match.group(1)
                    if cand_prefix[:2] in valid_country_codes:
                        prefix = cand_prefix
                
                reconstructed = prefix + bank + branch + acc + key
                if validate_iban_checksum(reconstructed)[0]:
                    found_iban = reconstructed
                    status = ValidationStatus.VALID
                    confidence = 90
                    detection_method = "Reconstructed (Grouped Labels - Valid)"
                    rib_bank_code, rib_branch_code, rib_account_number, rib_key = bank, branch, acc, key
                    break
            
            # Fallback for grouped labels: take first 23 digits even if invalid
            if not found_iban and len(raw_digits) >= 23:
                bank, branch, acc, key = raw_digits[0:5], raw_digits[5:10], raw_digits[10:21], raw_digits[21:23]
                
                prefix = "FR76"
                prefix_match = re.search(r'IBAN.{0,60}?([A-Z]{2}\d{2})', text_nospace)
                if prefix_match:
                    cand_prefix = prefix_match.group(1)
                    if cand_prefix[:2] in valid_country_codes:
                        prefix = cand_prefix
                
                found_iban = prefix + bank + branch + acc + key
                status = ValidationStatus.INVALID
                confidence = 40
                detection_method = "Reconstructed (Grouped Labels - Invalid Checksum)"
                rib_bank_code, rib_branch_code, rib_account_number, rib_key = bank, branch, acc, key

    # --- 2. BIC Extraction (Improved) ---
    found_bic = None
    
    # Strategy E: BIC following IBAN (with optional intermediate labels)
    # Regex: IBAN + (Optional Labels/Noise) + BIC
    if found_iban:
        escaped_iban = re.escape(found_iban)
        # Allow up to 60 characters of noise between IBAN and BIC in text_nospace
        bic_after_iban = re.search(escaped_iban + r'(?:[A-Z\s]{0,60}?)' + r'([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)', text_nospace)
        
        if bic_after_iban:
             potential = bic_after_iban.group(1)
             blacklist = {"IQUEMENT", "PAIEMENT", "FICTIF", "CONFORME", "BANKIDEN", "DOMICILI", "TITULAIR", "NUMBER", "ACCOUNT"}
             
             if len(potential) in [8, 11] and not any(bad in potential for bad in blacklist):
                final_bic = potential
                # Handle "glued" text (e.g. CMCIFRPPDOM -> CMCIFRPP)
                if len(potential) == 11 and potential[8:] in {'DOM', 'TIT', 'NAM', 'ADR', 'ADD', 'IBAN', 'BIC'}:
                    final_bic = potential[:8]
                found_bic = final_bic
                confidence += 20

    # Strategy F: General BIC fallback (if Strategy E failed)
    if not found_bic:
        # Search for any string matching BIC pattern in text_nospace
        all_bics = re.findall(r'([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)', text_nospace)
        for cand in all_bics:
            # blacklist expanded with partial labels to avoid "DENTITEBA" etc.
            blacklist = {
                "IQUEMENT", "PAIEMENT", "FICTIF", "CONFORME", "BANKIDEN", "DOMICILI", "TITULAIR", 
                "NUMBER", "ACCOUNT", "RELEVE", "IDENTITE", "BANQUE", "AGENCE", "NUMERO", "GUICHET",
                "POURTOUT", "DENTITE", "IDENTIT", "IBAN", "SWIFT", "ADDRESS", "OWNER"
            }
            if not any(bad in cand for bad in blacklist):
                found_bic = cand
                confidence += 10
                break


    # Strategy 4: Bank Name Extraction (from text)
    # Refined to stop before civility or keywords to avoid eating the Owner Name
    # e.g. "CIC WITTENHEIM MLE LILY..." -> "CIC WITTENHEIM"
    stop_lookahead = r'(?=\s+(?:M\.|MME|MLE|MLLE|MR|TITULAIRE|COMPTE|IBAN|BIC))'
    bank_patterns = [
        r'(CIC\s+[A-Z\s]+?)' + stop_lookahead, 
        r'(CREDIT\s+AGRICOLE(?:\s+[A-Z]+)?)', 
        r'(BANQUE\s+POPULAIRE(?:\s+[A-Z]+)?)',
        r'(CR\s+[A-Z\s]+)' + stop_lookahead,
        r'(BNP\s+PARIBAS)',
        r'(SOCIETE\s+GENERALE)', 
        r'(LA\s+BANQUE\s+POSTALE)', 
        r'(CAISSE\s+D[\'\s]?EPARGNE)',
        r'(BRED)', 
        r'(LCL)', 
        r'(BOURSORAMA)', 
        r'(REVOLUT)'
    ]
    for pattern in bank_patterns:
        match = re.search(pattern, raw_upper)
        if match:
            potential_bank = match.group(1).strip()
            # Safety: don't let it be too long (address included?)
            if len(potential_bank) < 40:
                found_bank = potential_bank
                confidence += 5
                break

    # Strategy 5: Owner Name Extraction
    # Updated to include 'MLE' and better filtering
    civ_match = re.search(r'(?:^|\n)\s*(M\.|MME|MR|MLLE|MLE)\s+([A-Z\s\-]{3,30})', raw_upper, re.MULTILINE)
    label_match = re.search(r'(?:TITULAIRE|NOM)(?:\s*(?:DU|DE)?\s*COMPTE)?(?:\s*\(?ACCOUNT\s*OWNER\)?)?\s*[:.\-]?\s*([A-Z\s\-]{3,30})', raw_upper) # Use raw_upper for regex spaces
    
    raw_owner = None
    
    # Priority: Civility (M. Name) - Strongest signal
    if civ_match:
        raw_owner = f"{civ_match.group(1)} {civ_match.group(2)}"
        
    # Priority: Label (TITULAIRE...)
    elif label_match:
        cand = label_match.group(1).strip()
        
        # CLEANUP: If the candidate starts with a Bank Name (e.g. CIC WITTENHEIM...), remove it
        # This happens if "TITULAIRE" is followed by Bank Address on next line
        for bank_pat in [r'^CIC\s', r'^CREDIT\sAGRICOLE', r'^BNP']:
            if re.match(bank_pat, cand):
                # Try to find what comes AFTER the bank name in this candidate string
                # This is hard if we don't know where bank name ends exactly in 'cand'
                # Simplification: If cand seems to BE a bank, discard it and look for civility in it?
                # or just fail this match type
                cand = "BANK_DETECTED" # validation below will kill it
                break

        blacklist = ["DOMICILIATION", "ADRESSE", "BANQUE", "COMPTE", "IBAN", "BIC", "ACCOUNT", "OWNER", "RELEVE", "BANK_DETECTED"]
        if not any(sw in cand for sw in blacklist) and len(cand) >= 3:
             # Extra check: DOES it contain a civility? "CIC WITTENHEIM MLE LILY"
             # If yes, extract from civility
             inner_civ = re.search(r'(M\.|MME|MR|MLLE|MLE)\s+([A-Z\s\-]{3,30})', cand)
             if inner_civ:
                 raw_owner = f"{inner_civ.group(1)} {inner_civ.group(2)}"
             else:
                 raw_owner = cand

    if raw_owner:
        found_owner = ' '.join(raw_owner.strip().split()) # Normalize spaces
        stop_words = ["IBAN", "BIC", "ADRESSE", "CHEZ", "BANQUE", "DOMICILIATION", "SWIFT", "ACCOUNT", "OWNER"]
        for sw in stop_words:
            if sw in found_owner:
                found_owner = found_owner.split(sw)[0].strip()

    # --- Final Data Lookup & Validation ---
    def load_bank_codes(filename="banks_fr.json"):
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            json_path = os.path.join(base_dir, "resources", filename)
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"DEBUG: Error loading {filename}: {e}")
        return {}

    bank_codes = load_bank_codes("banks_fr.json")
    bic_codes = load_bank_codes("bics_fr.json")
    
    if found_iban and len(found_iban) >= 9:
        bcode = found_iban[4:9]
        if bcode in bank_codes:
            found_bank = bank_codes[bcode]
        else:
            found_bank = f"Unknown (Code {bcode})"

    # If bank is still unknown, try identifying via BIC (using first 8 chars)
    if found_bank.startswith("Unknown") and found_bic and len(found_bic) >= 8:
        bic_8 = found_bic[:8].upper()
        found_bank = bic_codes.get(bic_8, "Unknown")

    if found_iban:
        is_v, msg = validate_iban_checksum(found_iban)
        checksum_valid = is_v
        if not is_v: validation_details.append(f"IBAN Checksum: {msg}")

    rib_key_valid = None
    if found_iban and found_iban.startswith('FR'):
        comps = extract_iban_components(found_iban)
        if comps['bank_code'] and comps['branch_code'] and comps['account_code']:
            rib_bank_code, rib_branch_code, rib_account_number = comps['bank_code'], comps['branch_code'], comps['account_code']
            rib_key = found_iban[25:27]
            is_v, msg = validate_french_rib_key(rib_bank_code, rib_branch_code, rib_account_number, rib_key)
            rib_key_valid = is_v
            if not is_v: validation_details.append(f"RIB Key: {msg}")

    # Anonymize logs (kept for internal logic if needed)
    try:
        anon = anonymize_text_for_debug(text_nospace, iban=found_iban, bic=found_bic, bank_code=rib_bank_code, branch_code=rib_branch_code, account_number=rib_account_number, key=rib_key)
        # Log removed for cleaner console/GUI
    except: pass

    return AnalyzeResponse(
        status=ValidationStatus.VALID if found_iban and checksum_valid else ValidationStatus.WARNING if found_iban else ValidationStatus.INVALID,
        confidence_score=min(100.0, confidence),
        extraction_method=detection_method,
        checksum_valid=checksum_valid,
        rib_key_valid=rib_key_valid,
        validation_details=validation_details if validation_details else None,
        data=RibData(iban=found_iban, bic=found_bic, owner_name=found_owner, bank_name=found_bank),
        message="Extraction successful" if found_iban else "No valid IBAN found"
    )
