import os
import pdfplumber
from typing import List, Dict, Any, Tuple
from .ner import extract_entities_from_text, detect_regional_language
from .resolve_entities import EntityResolver
from ..models.schemas import NodeSchema, EdgeSchema

def parse_pdf_document(
    file_path_or_bytes: Any,
    filename: str,
    resolver: EntityResolver
) -> Tuple[List[NodeSchema], List[EdgeSchema], List[str]]:
    """
    Parses a PDF document page by page using pdfplumber.
    Extracts text, detects regional scripts, extracts entities with spaCy/regex,
    and returns nodes and edges linking Document nodes to extracted entities.
    """
    nodes: List[NodeSchema] = []
    edges: List[EdgeSchema] = []
    warnings: List[str] = []

    has_regional_script = False

    try:
        with pdfplumber.open(file_path_or_bytes) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_num = page_idx + 1
                text = page.extract_text() or ""
                if not text.strip():
                    continue

                if detect_regional_language(text):
                    has_regional_script = True

                # Determine document sub-title or FIR number from first line
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                first_line = lines[0] if lines else f"Page {page_num}"
                doc_title = f"{filename} (P{page_num})"
                doc_id = f"doc_{os.path.splitext(filename)[0]}_p{page_num}".replace('-', '_').replace(' ', '_').lower()

                # Extract entities from page text
                ent_dict = extract_entities_from_text(text)

                doc_node = NodeSchema(
                    id=doc_id,
                    label=doc_title,
                    type="Document",
                    attributes={
                        "filename": filename,
                        "page": page_num,
                        "excerpt": text[:280] + ("..." if len(text) > 280 else ""),
                        "first_line": first_line
                    }
                )
                nodes.append(doc_node)

                # Track entity IDs mentioned in this page to create inter-entity co-mentions
                page_entity_ids = []

                # Resolve Persons
                for p in ent_dict["persons"]:
                    p_id, p_label = resolver.resolve_person(p["name"])
                    page_entity_ids.append(p_id)
                    nodes.append(NodeSchema(
                        id=p_id,
                        label=p_label,
                        type="Person",
                        attributes={"raw_name": p["name"]}
                    ))
                    edges.append(EdgeSchema(
                        id=f"edge_{p_id}_{doc_id}",
                        source=p_id,
                        target=doc_id,
                        type="Mentioned_In",
                        weight=1.0,
                        evidence_ref=doc_title,
                        attributes={"page": page_num, "entity": p_label}
                    ))

                # Resolve Phones
                for ph in ent_dict["phones"]:
                    ph_id, ph_label = resolver.resolve_phone(ph["value"])
                    page_entity_ids.append(ph_id)
                    nodes.append(NodeSchema(
                        id=ph_id,
                        label=ph_label,
                        type="Phone",
                        attributes={"phone_number": ph_label}
                    ))
                    edges.append(EdgeSchema(
                        id=f"edge_{ph_id}_{doc_id}",
                        source=ph_id,
                        target=doc_id,
                        type="Mentioned_In",
                        weight=1.0,
                        evidence_ref=doc_title,
                        attributes={"page": page_num}
                    ))

                # Resolve Vehicles
                for veh in ent_dict["vehicles"]:
                    v_id, v_label = resolver.resolve_vehicle(veh["value"])
                    page_entity_ids.append(v_id)
                    nodes.append(NodeSchema(
                        id=v_id,
                        label=v_label,
                        type="Vehicle",
                        attributes={"registration": v_label}
                    ))
                    edges.append(EdgeSchema(
                        id=f"edge_{v_id}_{doc_id}",
                        source=v_id,
                        target=doc_id,
                        type="Mentioned_In",
                        weight=1.0,
                        evidence_ref=doc_title,
                        attributes={"page": page_num}
                    ))

                # Resolve Organizations
                for org in ent_dict["organizations"]:
                    org_id, org_label = resolver.resolve_organization(org["name"])
                    page_entity_ids.append(org_id)
                    nodes.append(NodeSchema(
                        id=org_id,
                        label=org_label,
                        type="Organization",
                        attributes={}
                    ))
                    edges.append(EdgeSchema(
                        id=f"edge_{org_id}_{doc_id}",
                        source=org_id,
                        target=doc_id,
                        type="Mentioned_In",
                        weight=1.0,
                        evidence_ref=doc_title,
                        attributes={"page": page_num}
                    ))

                # Create targeted relational edges between Persons and their mentioned Vehicles/Phones/Persons on the same page
                page_persons = [eid for eid in page_entity_ids if eid.startswith("person_")]
                page_vehs = [eid for eid in page_entity_ids if eid.startswith("veh_")]
                page_phones = [eid for eid in page_entity_ids if eid.startswith("phone_")]

                # Link Person to Vehicle (Operates/Associated)
                for p_id in page_persons:
                    for v_id in page_vehs:
                        edges.append(EdgeSchema(
                            id=f"assoc_{p_id}_{v_id}_{doc_id}",
                            source=p_id,
                            target=v_id,
                            type="Uses_Vehicle",
                            weight=1.5,
                            evidence_ref=doc_title,
                            attributes={"document": doc_title, "page": page_num}
                        ))
                    # Link Person to Phone (Contact)
                    for ph_id in page_phones:
                        edges.append(EdgeSchema(
                            id=f"assoc_{p_id}_{ph_id}_{doc_id}",
                            source=p_id,
                            target=ph_id,
                            type="Uses_Phone",
                            weight=1.2,
                            evidence_ref=doc_title,
                            attributes={"document": doc_title, "page": page_num}
                        ))

                # Link co-accused Persons to each other
                for i in range(len(page_persons)):
                    for j in range(i + 1, min(i + 3, len(page_persons))):
                        edges.append(EdgeSchema(
                            id=f"comention_{page_persons[i]}_{page_persons[j]}_{doc_id}",
                            source=page_persons[i],
                            target=page_persons[j],
                            type="Co_Accused",
                            weight=1.0,
                            evidence_ref=doc_title,
                            attributes={"document": doc_title, "page": page_num}
                        ))

    except Exception as e:
        warnings.append(f"PDF parsing error: {str(e)}")

    if has_regional_script:
        warnings.append("Regional-language content detected — extraction may be incomplete.")

    return nodes, edges, warnings
