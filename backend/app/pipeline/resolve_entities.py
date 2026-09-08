import re
from typing import Dict, Optional, Tuple
from rapidfuzz import fuzz

class EntityResolver:
    """
    Maintains a canonical entity registry for a case.
    Uses fuzzy string matching (rapidfuzz) to resolve name variations
    (e.g., 'Amit Sharma' vs 'A. Sharma' vs 'Amit Kumar Sharma')
    and exact canonical formatting for phones and vehicle plates.
    """
    def __init__(self, similarity_threshold: float = 85.0):
        self.similarity_threshold = similarity_threshold
        # Maps canonical_id -> entity dict { "id": str, "label": str, "type": str, "aliases": set }
        self.entities: Dict[str, Dict] = {}
        # Fast lookup mapping alias / variant -> canonical_id
        self.alias_to_id: Dict[str, str] = {}

    def _normalize_name(self, name: str) -> str:
        clean = re.sub(r'[^\w\s]', '', name)
        clean = re.sub(r'\s+', ' ', clean).strip().title()
        return clean

    def _normalize_phone(self, phone: str) -> str:
        digits = re.sub(r'\D', '', phone)
        if len(digits) == 10:
            return f"+91{digits}"
        elif len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"
        return f"+{digits}" if digits else phone

    def _normalize_vehicle(self, plate: str) -> str:
        cleaned = re.sub(r'[^A-Za-z0-9]', '', plate).upper()
        if len(cleaned) >= 9:
            # DL01AB1234 -> DL-01-AB-1234
            state = cleaned[:2]
            district = cleaned[2:4]
            series = cleaned[4:-4]
            number = cleaned[-4:]
            return f"{state}-{district}-{series}-{number}"
        return plate.upper()

    def resolve_person(self, raw_name: str) -> Tuple[str, str]:
        """
        Resolves a person's name against existing person entities using rapidfuzz.
        Returns (canonical_id, canonical_label).
        """
        clean_name = self._normalize_name(raw_name)
        lookup_key = clean_name.lower()
        
        if lookup_key in self.alias_to_id:
            canon_id = self.alias_to_id[lookup_key]
            return canon_id, self.entities[canon_id]["label"]

        # Check fuzzy match against existing person entities
        best_id = None
        best_score = 0.0

        for canon_id, ent in self.entities.items():
            if ent["type"] != "Person":
                continue
            
            # Compare with canonical label and all registered aliases
            candidates = [ent["label"]] + list(ent.get("aliases", []))
            for cand in candidates:
                # Token sort ratio handles initials and word order ("A. Sharma" vs "Amit Sharma")
                score = fuzz.token_sort_ratio(clean_name, cand)
                # Check initials match e.g. "V. Singh" vs "Vikram Singh"
                parts_clean = clean_name.split()
                parts_cand = cand.split()
                if len(parts_clean) >= 2 and len(parts_cand) >= 2:
                    if parts_clean[-1].lower() == parts_cand[-1].lower():
                        # Surnames match; check if first name is an initial
                        if (len(parts_clean[0]) == 1 or parts_clean[0].endswith('.')) and parts_clean[0][0].lower() == parts_cand[0][0].lower():
                            score = max(score, 90.0)
                        elif (len(parts_cand[0]) == 1 or parts_cand[0].endswith('.')) and parts_cand[0][0].lower() == parts_clean[0][0].lower():
                            score = max(score, 90.0)

                if score > best_score:
                    best_score = score
                    best_id = canon_id

        if best_score >= self.similarity_threshold and best_id is not None:
            # Match found! Register alias
            self.alias_to_id[lookup_key] = best_id
            self.entities[best_id]["aliases"].add(clean_name)
            # If current clean_name is longer and more descriptive, upgrade the label
            if len(clean_name) > len(self.entities[best_id]["label"]) and "." not in clean_name:
                self.entities[best_id]["label"] = clean_name
            return best_id, self.entities[best_id]["label"]

        # New person entity
        slug = re.sub(r'[\s_]+', '_', clean_name.lower())
        new_id = f"person_{slug}"
        # Ensure uniqueness
        counter = 1
        base_id = new_id
        while new_id in self.entities:
            new_id = f"{base_id}_{counter}"
            counter += 1

        self.entities[new_id] = {
            "id": new_id,
            "label": clean_name,
            "type": "Person",
            "aliases": {clean_name},
            "attributes": {}
        }
        self.alias_to_id[lookup_key] = new_id
        return new_id, clean_name

    def resolve_phone(self, raw_phone: str) -> Tuple[str, str]:
        canonical_phone = self._normalize_phone(raw_phone)
        slug = re.sub(r'\D', '', canonical_phone)
        phone_id = f"phone_{slug}"
        if phone_id not in self.entities:
            self.entities[phone_id] = {
                "id": phone_id,
                "label": canonical_phone,
                "type": "Phone",
                "aliases": {canonical_phone, raw_phone},
                "attributes": {"number": canonical_phone}
            }
        return phone_id, canonical_phone

    def resolve_vehicle(self, raw_plate: str) -> Tuple[str, str]:
        canonical_plate = self._normalize_vehicle(raw_plate)
        slug = re.sub(r'[^a-zA-Z0-9]', '_', canonical_plate.lower())
        veh_id = f"veh_{slug}"
        if veh_id not in self.entities:
            self.entities[veh_id] = {
                "id": veh_id,
                "label": canonical_plate,
                "type": "Vehicle",
                "aliases": {canonical_plate, raw_plate},
                "attributes": {"license_plate": canonical_plate}
            }
        return veh_id, canonical_plate

    def resolve_organization(self, raw_org: str) -> Tuple[str, str]:
        clean_org = self._normalize_name(raw_org)
        lookup_key = clean_org.lower()
        if lookup_key in self.alias_to_id:
            org_id = self.alias_to_id[lookup_key]
            return org_id, self.entities[org_id]["label"]

        slug = re.sub(r'[\s_]+', '_', clean_org.lower())
        org_id = f"org_{slug}"
        self.entities[org_id] = {
            "id": org_id,
            "label": clean_org,
            "type": "Organization",
            "aliases": {clean_org},
            "attributes": {}
        }
        self.alias_to_id[lookup_key] = org_id
        return org_id, clean_org

    def resolve_location(self, raw_loc: str) -> Tuple[str, str]:
        clean_loc = self._normalize_name(raw_loc)
        lookup_key = clean_loc.lower()
        if lookup_key in self.alias_to_id:
            loc_id = self.alias_to_id[lookup_key]
            return loc_id, self.entities[loc_id]["label"]

        slug = re.sub(r'[\s_]+', '_', clean_loc.lower())
        loc_id = f"loc_{slug}"
        self.entities[loc_id] = {
            "id": loc_id,
            "label": clean_loc,
            "type": "Location",
            "aliases": {clean_loc},
            "attributes": {}
        }
        self.alias_to_id[lookup_key] = loc_id
        return loc_id, clean_loc
