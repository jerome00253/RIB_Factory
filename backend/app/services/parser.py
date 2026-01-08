import re
from app.models.schemas import RibData, ValidationStatus, AnalyzeResponse
from schwifty import IBAN, BIC
from stdnum import iban as stdnum_iban

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

# ... (rest of functions)

def parse_rib(raw_text: str) -> AnalyzeResponse:
    # ... (init variables)
    validation_details = []
    
    # ... (logic to find IBAN/BIC/Owner) ...

    # Final Validation Checks
    checksum_valid = False
    if found_iban:
        is_valid, msg = validate_iban_checksum(found_iban)
        checksum_valid = is_valid
        if not is_valid:
            validation_details.append(f"IBAN Checksum: {msg}")

    # Validate French RIB key if we have the components
    rib_key_valid = None
    
    # If we have an IBAN but no RIB components, try to extract them from IBAN
    if found_iban and found_iban.startswith('FR') and not rib_bank_code:
        # ... (auto extract logic) ...
        # (Assuming components extracted above)
        pass 

    # Re-verify logic for auto-extraction (simplified for replacement)
    if found_iban and found_iban.startswith('FR') and not rib_bank_code:
        try:
             components = extract_iban_components(found_iban)
             if components['bank_code'] and components['branch_code'] and components['account_code']:
                bban = found_iban[4:]
                if len(bban) >= 23:
                    rib_bank_code = components['bank_code']
                    rib_branch_code = components['branch_code'] 
                    rib_account_number = components['account_code']
                    rib_key = bban[-2:]
        except:
            pass

    if rib_bank_code and rib_branch_code and rib_account_number and rib_key:
        is_valid, msg = validate_french_rib_key(rib_bank_code, rib_branch_code, rib_account_number, rib_key)
        rib_key_valid = is_valid
        if not is_valid:
             validation_details.append(f"RIB Key: {msg}")
        # else:
            # validation_details.append("RIB Key: Valid")

    return AnalyzeResponse(
        status=status,
        confidence_score=confidence,
        extraction_method=detection_method, # Variable to be defined in logic
        checksum_valid=checksum_valid,
        rib_key_valid=rib_key_valid,
        validation_details=validation_details if validation_details else None,
        data=RibData(
            iban=found_iban,
            bic=found_bic,
            owner_name=found_owner,
            bank_name=found_bank
        ),
        message="Extraction successful" if found_iban else "No valid IBAN found"
    )

def validate_bic(bic_str: str) -> bool:
    """
    Validate BIC using schwifty library.
    """
    try:
        bic_obj = BIC(bic_str.upper())
        return True
    except:
        return False

def identify_bank_name(iban_str: str) -> str:
    """
    Try to identify bank name from IBAN using schwifty.
    """
    try:
        clean = clean_iban(iban_str)
        iban_obj = IBAN(clean)
        # Schwifty doesn't provide bank names directly
        # We keep our simple logic for now
        return "Unknown"
    except:
        return "Unknown"


def parse_rib(raw_text: str) -> AnalyzeResponse:
    confidence = 0.0
    status = ValidationStatus.INVALID
    
    # Regex Patterns
    # IBAN : Starts with 2 letters, 2 digits, then alphanumeric. Removed \b to handle concatenated text.
    iban_pattern = re.compile(r'([A-Z]{2}\d{2}[A-Z0-9]{10,30})')
    # BIC : 8 or 11 chars
    bic_pattern = re.compile(r'([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?)')
    
    # Cleaning text for easier search (removing spaces specifically for IBAN search could be done)
    # For now, we search in raw text but could be improved
    
    print(f"DEBUG: Raw OCR Text:\n{raw_text}")
    print("--------------------------------")
    
    # Clean text: remove all spaces AND non-alphanumeric characters for regex search
    # This ensures "TITULAIRE : M. DUPONT" becomes "TITULAIREMDUPONT" not "TITULAIRE:M.DUPONT"
    text_nospace = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    
    # Text clean: keep spaces but remove special chars for other searches
    text_clean = re.sub(r'[^A-Z0-9\s]', '', raw_text.upper())
    
    print(f"DEBUG: text_nospace: {text_nospace}")
    
    # Initialize all result variables
    found_iban = None
    found_bic = None
    found_owner = "Unknown"
    found_bank = "Unknown"
    checksum_valid = False # Initialize explicitly to avoid NameError
    validation_details = [] # Initialize explicitly to avoid NameError
    
    # RIB components for French key validation - DECLARE AT START
    rib_bank_code = None
    rib_branch_code = None
    rib_account_number = None
    rib_key = None
    
    detection_method = "Unknown"
    # Valid SEPA country codes (plus common ones) to filter false positives like "UE" (from BANQUE) or "IB" (from RIB)
    # This list is not exhaustive but covers most cases expected in this app context
    valid_country_codes = {'FR', 'BE', 'DE', 'ES', 'IT', 'GB', 'CH', 'LU', 'NL', 'AT', 'PT', 'IE', 'SE', 'DK', 'FI', 'NO', 'PL', 'CZ', 'HU', 'SK', 'SI', 'HR', 'EE', 'LV', 'LT', 'MT', 'CY', 'GR', 'BG', 'RO', 'MC', 'SM', 'LI', 'IS'}

    # Search for all potential IBANs in the nospace string using Lookahead to handle overlaps
    # Standard finditer consumes characters, so if "IB18..." (invalid) consumes "FR76..." (valid), we lose the valid one.
    # Lookahead (?=...) captures matches without consuming the string.
    
    # Pattern: [A-Z]{2}\d{2}[A-Z0-9]{10,30}
    # We find all strings that match this structure starting at any position
    potential_matches = re.findall(r'(?=([A-Z]{2}\d{2}[A-Z0-9]{10,30}))', text_nospace)
    
    # PRIORITIZE French IBANs - sort so FR comes first
    potential_matches = sorted(potential_matches, key=lambda x: (0 if x.startswith('FR') else 1, x))
    
    for candidate in potential_matches:
        # Filter obvious junk: Country code must be valid
        if candidate[:2] not in valid_country_codes:
            # print(f"DEBUG: Skipping candidate {candidate[:4]}... (Invalid Country Code)")
            continue

        print(f"DEBUG: Checking candidate: {candidate}")
        
        # ... (Existing Checksum & Correction Logic) ...
        # (I need to copy the logic inside the loop because replace_content overwrites it)
        
        valid_iban = None
        max_len = min(len(candidate), 34)
        min_len = 15
        
        # PRIORITIZE French IBANs (FR) - check them first
        is_french = candidate.startswith('FR')
        
        for length in range(max_len, min_len - 1, -1):
            sub_candidate = candidate[:length]
            
            # 1. Direct Check
            is_valid, _ = validate_iban_checksum(sub_candidate)
            if is_valid:
                # Extra validation: French IBANs MUST be exactly 27 characters
                if sub_candidate.startswith('FR') and len(sub_candidate) != 27:
                    print(f"DEBUG: Rejecting French IBAN with wrong length: {len(sub_candidate)} chars (need 27)")
                    continue
                    
                valid_iban = sub_candidate
                detection_method = "Direct Extraction"
                print(f"DEBUG: Found valid IBAN (Direct) (len={length}): {valid_iban}")
                break
            
            # 2. OCR Correction Strategy - ONLY for French IBANs to avoid false positives
            if is_french or sub_candidate.startswith('FR'):
                replacements = {'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'Z': '2', 'B': '8', 'S': '5'}
                
                def replace_confusing_chars(s):
                    res = []
                    for char in s:
                        res.append(replacements.get(char, char))
                    return "".join(res)
                
                header = sub_candidate[:2]
                body = sub_candidate[2:]
                corrected_body = replace_confusing_chars(body)
                corrected_candidate = header + corrected_body
                
                if corrected_candidate != sub_candidate:
                    is_valid_corr, _ = validate_iban_checksum(corrected_candidate)
                    if is_valid_corr:
                        # Extra validation: French IBANs MUST be exactly 27 characters
                        if corrected_candidate.startswith('FR') and len(corrected_candidate) != 27:
                            print(f"DEBUG: Rejecting corrected French IBAN with wrong length: {len(corrected_candidate)} chars (need 27)")
                            continue
                            
                        valid_iban = corrected_candidate
                        detection_method = "OCR Correction"
                        print(f"DEBUG: Found valid IBAN (Corrected) (len={length}): {valid_iban} (was {sub_candidate})")
                        break

        if valid_iban:
            found_iban = valid_iban
            confidence += 80 
            status = ValidationStatus.VALID 
            break 

    # Fallback: Reconstruct French IBAN from components if standard search failed
    if not found_iban:
        print("DEBUG: Standard IBAN search failed. Trying reconstruction from RIB components...")
        
        # Regex for components 
        rb_bank = re.search(r'BANQUE.*?(\d{5})', text_nospace)
        rb_branch = re.search(r'GUICHET.*?(\d{5})', text_nospace)
        
        # Account: Prioritize "NODECOMPTE" or "NUMERO" over generic "COMPTE" which matches "TITULAIRE DU COMPTE"
        # Regex looks for specific keys first
        rb_account = re.search(r'(?:NODECOMPTE|NUMERODECOMPTE|COMPTE).*?([A-Z0-9]{11})', text_nospace)
        
        # Key: "CLE" or "RIB" followed closely by 2 digits
        # Use findall to get the last one? Or just strict search
        # Avoid "OCRRIB" matching "RIB". But text_nospace has no spaces/boundaries?
        # Actually in text_nospace "OCRRIB" is "OCRRIB".
        # We should look for digits at the end of the string? Or structured query?
        # Let's try to match "CLRIB" or "CLE" + digits
        # Original failure: "CLRIB57" -> matched "RIB" in "TESTOCRRIB" then "20" in "BANQUE20041"
        # We want "RIB" followed IMMEDIATELY by digits in nospace context
        rb_key = re.search(r'(?:CLE|RIB)(\d{2})', text_nospace)
        
        if rb_bank and rb_branch and rb_account and rb_key:
            bank = rb_bank.group(1)
            branch = rb_branch.group(1)
            account = rb_account.group(1)
            key = rb_key.group(1)
            
            # Store for RIB key validation
            rib_bank_code = bank
            rib_branch_code = branch
            rib_account_number = account
            rib_key = key
            
            print(f"DEBUG: Found components: Bank={bank}, Branch={branch}, Account={account}, Key={key}")
            
            # Construct the Body: Bank + Branch + Account + Key
            rib_body = bank + branch + account + key
            
            # Now we need the Country Code and IBAN Check Digits.
            # Usually found as "FR76" or similar.
            # Search for "IBAN" followed by 2 letters and 2 digits
            rb_iban_prefix = re.search(r'IBAN.*?([A-Z]{2}\d{2})', text_nospace)
            
            prefix = "FR76" # Default assumption/fallback if missed?
             # Or verify checksum?
             # Ideally we find the prefix.
            if rb_iban_prefix:
                prefix = rb_iban_prefix.group(1)
            
            reconstructed_iban = prefix + rib_body
            
            if validate_iban_checksum(reconstructed_iban):
                found_iban = reconstructed_iban
                print(f"DEBUG: Reconstructed valid IBAN: {found_iban}")
                status = ValidationStatus.VALID
                confidence = 85 # Good but reconstructed
                
                # Check if this reconstructed IBAN actually exists in the text
                if reconstructed_iban in text_nospace:
                    detection_method = "Reconstructed (Found in Text)"
                else:
                    detection_method = "Reconstructed (Not Found in Text)"

    # --- 2. BIC Extraction (Improved) ---
    # ... (Rest of function) ...
    
    # --- 2. BIC Extraction (Improved) ---
    found_bic = None
    
    # Strategy A: Look for BIC directly after "BIC" keyword in nospace (HIGHEST PRIORITY)
    # This catches "BICCMCIFR2AXXX" -> "CMCIFR2AXXX"
    # But skip SWIFT keyword, IBAN, and person names: "BICSWIFTMLINHERJROMEBOUSFRPPXXX" -> "BOUSFRPPXXX"
    # Look for BIC after an IBAN pattern if present, and skip SWIFT + names
    # BIC format: 4 letters (bank) + 2 letters (country) + 2 alphanumeric (location) + optional 3 (branch)
    # The optional 3 should be XXX or digits, not random letters from adjacent text
    # Skip pattern: SWIFT, M/MR/MME/MLLE + name (up to 40 chars)
    bic_after_iban = re.search(r'BIC(?:SWIFT)?(?:[M]{1,4}[A-Z]{0,40}?)?(?:FR[0-9]{2}[A-Z0-9]{23})?([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[0-9X]{3})?)', text_nospace)
    if bic_after_iban:
        potential_bic = bic_after_iban.group(1)
        # Extra validation: not in blacklist and not a name fragment
        bic_blacklist_early = {"IQUEMENT", "PAIEMENT", "FICTIF", "CONFORME", "REVOLUTTITU", "TITULAIR", "LINHERJ", "SWIFTMLI"}
        if len(potential_bic) in [8, 11] and not any(bad in potential_bic for bad in bic_blacklist_early):
            found_bic = potential_bic
            confidence += 15
            print(f"DEBUG: Found BIC after keyword/IBAN: {found_bic}")
    
    # Strategy B: Look for spaced BIC patterns in clean text
    if not found_bic:
        spaced_bic_pattern_1 = re.compile(r'\b([A-Z]{4})\s+([A-Z]{2})\s+([A-Z0-9]{2})\s+([A-Z0-9]{3})\b')
        spaced_bic_pattern_2 = re.compile(r'\b([A-Z]{4})\s+([A-Z]{4})\s+([A-Z0-9]{3})\b')
        
        match_spaced_1 = spaced_bic_pattern_1.search(text_clean)
        match_spaced_2 = spaced_bic_pattern_2.search(text_clean)
        
        if match_spaced_1:
             found_bic = "".join(match_spaced_1.groups())
             confidence += 15
             print(f"DEBUG: Found Spaced BIC (4-2-2-3): {found_bic}")
        elif match_spaced_2:
             found_bic = "".join(match_spaced_2.groups())
             confidence += 15
             print(f"DEBUG: Found Spaced BIC (4-4-3): {found_bic}")
    
    # Strategy C: Contextual "BIC" keyword (with better filtering)
    if not found_bic:
        bic_context_pattern = re.compile(r'BIC[:\s]+([A-Z]{4}[A-Z]{2}[A-Z0-9]{2}([A-Z0-9]{3})?)', re.IGNORECASE)
        match_context_bic = bic_context_pattern.search(text_clean)
        
        if match_context_bic:
            raw_bic = match_context_bic.group(1).replace(" ", "")
            # Verify length and not in blacklist
            bic_blacklist = {"IQUEMENT", "PAIEMENT", "FICTIF", "CONFORME", "UNIQUEMENT"}
            if len(raw_bic) in [8, 11] and not any(bad in raw_bic for bad in bic_blacklist):
                found_bic = raw_bic
                confidence += 10
                print(f"DEBUG: Found BIC via context: {found_bic}")
    
    # Strategy D: Scanning nospace (last resort)
    if not found_bic:
        # Blacklist for words that accidentally match BIC structure
        bic_blacklist = {"IQUEMENT", "PAIEMENT", "ALEMENT", "ULEMENT", "ENT", "MENT", "TEST", "USAGE", "GUICHET", "BANQUE", "UNIQUEMENT", "FICTIF"}
        
        for match in bic_pattern.finditer(text_nospace):
            potential_bic = match.group(0)
            
            # Check blacklist
            if any(bad in potential_bic for bad in bic_blacklist):
                continue
                
            # Extra check: valid BICs rarely end in "ENT" (common in French words)
            if potential_bic.endswith("ENT") or potential_bic.endswith("MENT"):
                continue

            if len(potential_bic) in [8, 11] and potential_bic[:4] != "IBAN" and potential_bic[:3] != "BIC":
                 found_bic = potential_bic
                 confidence += 5
                 print(f"DEBUG: Found BIC via scan: {found_bic}")
                 break

    # --- 3. Owner Name Extraction (Heuristic) ---
    
    # Use RAW text (with newlines) for structure-based extraction
    raw_upper = raw_text.upper()

    # 3.1 Try Civility at Start of Line (Common in broken layouts)
    # Look for "M. NAME" or "MR NAME" at the beginning of a line
    civility_pattern = re.compile(r'(?:^|\n)\s*(M\.|MME|MR|MLLE)\s+([A-Z\s\-]{3,30})', re.MULTILINE)
    match_civility = civility_pattern.search(raw_upper)
    
    # 3.2 Try "Titulaire" Label
    owner_pattern = re.compile(r'(?:TITULAIRE|NOM)\s*(?:DU COMPTE)?\s*[:.\-]?\s*([A-Z\s\-]{3,30})')
    match_owner = owner_pattern.search(text_clean) # Use clean text for label search (might be inline)

    # Decide best match
    raw_owner = None
    
    # Priority 1: Civility (M. Name) found at start of line
    if match_civility:
         raw_owner = f"{match_civility.group(1)} {match_civility.group(2)}"
         print(f"DEBUG: Found Owner via Civility: {raw_owner}")

    # Priority 2: Inline Regex (Classic "Titulaire : NOM")
    if not raw_owner and match_owner:
        candidate = match_owner.group(1).strip()
        stop_words_inline = ["DOMICILIATION", "ADRESSE", "BANQUE", "COMPTE"]
        # Basic check: Is it just a stop word?
        is_bad = any(sw in candidate for sw in stop_words_inline)
        if not is_bad:
            raw_owner = candidate
            print(f"DEBUG: Found Owner via Regex: {raw_owner}")
    
    # Priority 2.5: Look in text_nospace after TITULAIRE
    if not raw_owner:
        # Try to extract from "TITULAIREDUCOMPTEDOMICILIATIONJEROMEIDENISPASCALLINHER" -> "JEROMEIDENISPASCALLINHER"
        # Skip "DUCOMPTE" and "DOMICILIATION" to get to the real name
        titulaire_match = re.search(r'TITULAIRE(?:DUCOMPTE)?(?:DOMICILIATION)?([A-Z][A-Z\s]{3,40}?)(?:REVOLU|BANQUE|IBAN|BIC|GUICHET|NODE|ADRESSE)', text_nospace)
        if titulaire_match:
            potential_owner = titulaire_match.group(1).strip()
            # Try to find the spaced version in the original text first
            if len(potential_owner) > 3:
                # Look for this name in the original text with spaces
                # Create a regex that allows spaces between each character
                spaced_pattern = '\s*'.join(re.escape(c) for c in potential_owner)
                spaced_search = re.search(spaced_pattern, raw_upper)
                if spaced_search:
                    raw_owner = spaced_search.group(0).strip()
                    print(f"DEBUG: Found Owner with original spacing: {raw_owner}")
                else:
                    # Fallback: add spaces intelligently
                    spaced_owner = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', potential_owner)
                    # For all-caps names, split on common words or add space every 5-7 chars (typical French names)
                    if spaced_owner == potential_owner and potential_owner.isupper():
                        common_words = ['COMPTE', 'TEST', 'EXEMPLE', 'MONSIEUR', 'MADAME', 'SOCIETE', 'ENTREPRISE']
                        for word in common_words:
                            spaced_owner = spaced_owner.replace(word, word + ' ')
                        # If still no spaces, add them every 5-7 chars (typical name length)
                        if ' ' not in spaced_owner and len(spaced_owner) > 10:
                            parts = []
                            i = 0
                            while i < len(spaced_owner):
                                # Take 5-8 chars
                                part_len = min(7, len(spaced_owner) - i) if (len(spaced_owner) - i) > 4 else len(spaced_owner) - i
                                parts.append(spaced_owner[i:i+part_len])
                                i += part_len
                            spaced_owner = ' '.join(parts)
                        spaced_owner = spaced_owner.strip()
                    
                    raw_owner = spaced_owner if spaced_owner else potential_owner
                    print(f"DEBUG: Found Owner in nospace (spaced): {raw_owner}")

    # Priority 3: Line-based contextual search (Fallback)
    if not raw_owner:
        lines = raw_upper.splitlines()
        for i, line in enumerate(lines):
            # If line contains TITULAIRE or NOM matches simple label
            if "TITULAIRE" in line or "NOM " in line: 
                # Look ahead 1-3 lines
                for offset in range(1, 4):
                    if i + offset >= len(lines):
                        break
                    
                    next_line = lines[i + offset].strip()
                    # Skip empty or banking keywords
                    skip_keywords = ["DOMICILIATION", "ADRESSE", "BANQUE", "COMPTE", "GUICHET", "IBAN", "BIC", "NODE", "CLE", "RIB"]
                    if not next_line or any(kw in next_line for kw in skip_keywords):
                        continue
                    
                    # If line looks like a name (mostly alpha, at least 3 chars)
                    # Avoid if it looks like an IBAN or BIC
                    if len(next_line) > 3:
                        # Heuristic: mostly letters?
                        check_str = re.sub(r'[^A-Z]', '', next_line)
                        if len(check_str) > 2:
                             raw_owner = next_line
                             print(f"DEBUG: Found Owner via Line Search (Offset {offset}): {raw_owner}")
                             break
                if raw_owner:
                    break



    if raw_owner:
        # Clean up result
        clean_name = raw_owner.strip()
        # Clean newlines if any slipped in (from raw capture)
        clean_name = clean_name.replace("\n", " ")
        
        stop_words = ["IBAN", "BIC", "ADRESSE", "CHEZ", "BANQUE", "DOMICILIATION", "SWIFT", "CODE", "GUICHET"]
        for sw in stop_words:
            if sw in clean_name:
                clean_name = clean_name.split(sw)[0]
        
        if len(clean_name) > 3:
            found_owner = clean_name.strip()

    # --- 4. Bank Name Extraction (Lookup Code) ---
    found_bank = "Unknown"
    bank_codes = {
        '30003': 'Société Générale',
        '30004': 'BNP Paribas',
        '30002': 'Crédit Agricole',
        '20041': 'La Banque Postale',
        '10278': 'Crédit Mutuel',
        '10096': 'Caisse d\'Epargne',
        '30066': 'CIC',
        '30007': 'LCL',
        '28233': 'Revolut (Branch)',
        '16656': 'Revolut',
        '23605': 'AXA Banque',
        '14505': 'Nickel',
        '40618': 'BoursoBank', 
        '92772': 'BoursoBank (Siège?)' # Often appears in address, adding just in case
    }
    
    if found_iban and len(found_iban) >= 9:
        # FR76 3000 4... -> Bank Code is at index 4 to 9 (5 digits)
        # Standard IBAN: CC KK BBBB B...
        # FR KK BBBB B...
        # Index: 01 23 4567 8
        # Slicing: iban[4:9]
        bank_code = found_iban[4:9]
        if bank_code in bank_codes:
            found_bank = bank_codes[bank_code]
        else:
             found_bank = f"Unknown (Code: {bank_code})"

    # Final Scoring adjustments
    if found_iban and found_bic:
        status = ValidationStatus.VALID
        confidence = 100
    elif found_iban:
        status = ValidationStatus.WARNING
        confidence = 80
    elif found_bic:
         status = ValidationStatus.WARNING
         confidence = 20

    # Final Scoring adjustments

    # Validate Checksum for found IBAN
    if found_iban:
        is_valid, msg = validate_iban_checksum(found_iban)
        checksum_valid = is_valid
        if not is_valid:
            validation_details.append(f"IBAN Checksum: {msg}")

    # Validate French RIB key if we have the components
    rib_key_valid = None
    
    # If we have an IBAN but no RIB components, try to extract them from IBAN
    if found_iban and found_iban.startswith('FR') and not rib_bank_code:
        print("DEBUG: Extracting RIB components from IBAN using schwifty...")
        components = extract_iban_components(found_iban)
        if components['bank_code'] and components['branch_code'] and components['account_code']:
            # Extract key from IBAN (last 2 digits of BBAN)
            # FR IBAN structure: FR76 + BBBBB GGGGG AAAAAAAAAAA KK (27 total)
            # BBAN is positions 4-27 (23 chars): BBBBBGGGGGAAAAAAAAAAAKK
            bban = found_iban[4:]  # Remove FR76
            if len(bban) >= 23:
                rib_bank_code = components['bank_code']
                rib_branch_code = components['branch_code'] 
                rib_account_number = components['account_code']
                rib_key = bban[-2:]  # Last 2 digits
                print(f"DEBUG: Auto-extracted RIB: Bank={rib_bank_code}, Branch={rib_branch_code}, Account={rib_account_number}, Key={rib_key}")
    
    # Validate RIB key if we have all components
    if rib_bank_code and rib_branch_code and rib_account_number and rib_key:
        is_valid, msg = validate_french_rib_key(rib_bank_code, rib_branch_code, rib_account_number, rib_key)
        rib_key_valid = is_valid
        print(f"DEBUG: RIB Key validation: {is_valid}, Msg: {msg}")
        if not is_valid:
             validation_details.append(f"RIB Key: {msg}")

    return AnalyzeResponse(
        status=status,
        confidence_score=confidence,
        extraction_method=detection_method, 
        checksum_valid=checksum_valid, # Use the boolean variable calculated above
        rib_key_valid=rib_key_valid,   # Use the boolean variable calculated above
        validation_details=validation_details if validation_details else None,
        data=RibData(
            iban=found_iban,
            bic=found_bic,
            owner_name=found_owner,
            bank_name=found_bank
        ),
        message="Extraction successful" if found_iban else "No valid IBAN found"
    )
