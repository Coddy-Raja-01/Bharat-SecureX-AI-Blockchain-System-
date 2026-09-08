import re
from typing import List, Dict, Any, Tuple
import spacy

try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = spacy.blank("en")

# Indian phone number regex: +91 followed by 10 digits starting with 6-9, or bare 10-digit
PHONE_PATTERN = re.compile(r'(?:\+?91[\-\s]?)?[6-9]\d{9}\b')

# Indian vehicle registration plate pattern: DL-01-AB-1234 or UP-32-CD-5678 or MH12AB1234
VEHICLE_PATTERN = re.compile(r'\b[A-Z]{2}[-\s]?\d{2}[-\s]?[A-Z]{1,2}[-\s]?\d{4}\b')

# Money pattern (INR/Rs/₹)
MONEY_PATTERN = re.compile(r'(?:Rs\.?|INR|₹)\s?([\d,]+(?:\.\d+)?)')

# Regional language unicode ranges (Devanagari, Bengali, Tamil, Telugu, Gurmukhi, Gujarati)
REGIONAL_SCRIPT_PATTERN = re.compile(r'[\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF\u0B80-\u0BFF\u0C00-\u0C7F]')

# Common FIR and police stop words to exclude from person/org names
IGNORED_NAMES = {
    "first information report", "fir", "police station", "sub inspector",
    "station house officer", "investigating officer", "ipc", "crpc",
    "honorable court", "prosecution", "charge sheet", "accused", "complainant",
    "informant", "case summary", "ps", "cyber crime", "crime", "special operations"
}

def detect_regional_language(text: str) -> bool:
    """Returns True if regional Indian script (e.g. Hindi, Bengali) is detected."""
    return bool(REGIONAL_SCRIPT_PATTERN.search(text))

def extract_entities_from_text(text: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extracts PERSON, ORG, GPE, PHONE, VEHICLE, and MONEY entities
    from unstructured document or intel snippet.
    """
    results: Dict[str, List[Dict[str, Any]]] = {
        "persons": [],
        "organizations": [],
        "locations": [],
        "phones": [],
        "vehicles": [],
        "amounts": []
    }
    
    seen_entities = set()

    # 1. Regex for Phones
    for match in PHONE_PATTERN.finditer(text):
        raw_phone = match.group(0).strip()
        # Canonicalize to +91XXXXXXXXXX
        clean_digits = re.sub(r'\D', '', raw_phone)
        if len(clean_digits) == 10:
            canonical_phone = f"+91{clean_digits}"
        elif len(clean_digits) == 12 and clean_digits.startswith("91"):
            canonical_phone = f"+{clean_digits}"
        else:
            canonical_phone = raw_phone
            
        key = ("PHONE", canonical_phone)
        if key not in seen_entities:
            seen_entities.add(key)
            results["phones"].append({
                "value": canonical_phone,
                "raw": raw_phone,
                "start": match.start(),
                "end": match.end()
            })

    # 2. Regex for Vehicles
    for match in VEHICLE_PATTERN.finditer(text):
        raw_veh = match.group(0).strip().upper()
        # Canonicalize format to XX-00-XX-0000
        parts = re.split(r'[-\s]', raw_veh)
        if len(parts) == 4:
            canonical_veh = f"{parts[0]}-{parts[1]}-{parts[2]}-{parts[3]}"
        else:
            canonical_veh = raw_veh
            
        key = ("VEHICLE", canonical_veh)
        if key not in seen_entities:
            seen_entities.add(key)
            results["vehicles"].append({
                "value": canonical_veh,
                "raw": raw_veh,
                "start": match.start(),
                "end": match.end()
            })

    # 3. Regex for Amounts
    for match in MONEY_PATTERN.finditer(text):
        raw_amt = match.group(0).strip()
        num_str = match.group(1).replace(',', '')
        try:
            val = float(num_str)
            results["amounts"].append({
                "value": val,
                "raw": raw_amt,
                "start": match.start(),
                "end": match.end()
            })
        except ValueError:
            pass

    # 4. spaCy NER for PERSON, ORG, GPE
    doc = nlp(text)
    for ent in doc.ents:
        ent_text = ent.text.strip()
        if len(ent_text) < 3 or ent_text.lower() in IGNORED_NAMES:
            continue
            
        if ent.label_ == "PERSON":
            # Filter obvious false positives like single common words
            if any(char.isdigit() for char in ent_text):
                continue
            key = ("PERSON", ent_text)
            if key not in seen_entities:
                seen_entities.add(key)
                results["persons"].append({
                    "name": ent_text,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
        elif ent.label_ in ("ORG", "ORGANIZATION"):
            key = ("ORG", ent_text)
            if key not in seen_entities:
                seen_entities.add(key)
                results["organizations"].append({
                    "name": ent_text,
                    "start": ent.start_char,
                    "end": ent.end_char
                })
        elif ent.label_ in ("GPE", "LOC"):
            key = ("GPE", ent_text)
            if key not in seen_entities:
                seen_entities.add(key)
                results["locations"].append({
                    "name": ent_text,
                    "start": ent.start_char,
                    "end": ent.end_char
                })

    return results
