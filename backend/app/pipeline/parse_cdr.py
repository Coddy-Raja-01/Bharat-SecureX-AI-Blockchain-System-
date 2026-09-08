import pandas as pd
from typing import List, Dict, Any, Tuple
from .resolve_entities import EntityResolver
from ..models.schemas import NodeSchema, EdgeSchema

def parse_cdr_file(
    file_path_or_bytes: Any,
    filename: str,
    resolver: EntityResolver
) -> Tuple[List[NodeSchema], List[EdgeSchema], List[str]]:
    """
    Parses CDR CSV file into CALLED edges between Person nodes (or Phone nodes).
    Extracts timestamps, durations, and tower locations.
    """
    nodes: List[NodeSchema] = []
    edges: List[EdgeSchema] = []
    warnings: List[str] = []

    try:
        df = pd.read_csv(file_path_or_bytes)
        
        # Normalize column names
        col_map = {c.lower().strip().replace(' ', '_'): c for c in df.columns}
        
        caller_no_col = col_map.get('caller_number', col_map.get('caller_no', col_map.get('caller', None)))
        caller_name_col = col_map.get('caller_name', col_map.get('caller_person', None))
        receiver_no_col = col_map.get('receiver_number', col_map.get('receiver_no', col_map.get('receiver', None)))
        receiver_name_col = col_map.get('receiver_name', col_map.get('receiver_person', None))
        ts_col = col_map.get('timestamp', col_map.get('call_time', col_map.get('date_time', None)))
        dur_col = col_map.get('duration_sec', col_map.get('duration', None))
        tower_col = col_map.get('tower_location', col_map.get('cell_tower_location', col_map.get('location', None)))
        rec_id_col = col_map.get('record_id', col_map.get('id', None))

        for idx, row in df.iterrows():
            caller_name = str(row[caller_name_col]).strip() if caller_name_col and pd.notna(row[caller_name_col]) else None
            caller_no = str(row[caller_no_col]).strip() if caller_no_col and pd.notna(row[caller_no_col]) else None
            
            receiver_name = str(row[receiver_name_col]).strip() if receiver_name_col and pd.notna(row[receiver_name_col]) else None
            receiver_no = str(row[receiver_no_col]).strip() if receiver_no_col and pd.notna(row[receiver_no_col]) else None
            
            timestamp = str(row[ts_col]).strip() if ts_col and pd.notna(row[ts_col]) else None
            duration = float(row[dur_col]) if dur_col and pd.notna(row[dur_col]) else 60.0
            location = str(row[tower_col]).strip() if tower_col and pd.notna(row[tower_col]) else "Unknown"
            rec_id = str(row[rec_id_col]).strip() if rec_id_col and pd.notna(row[rec_id_col]) else f"CDR-{idx+1:04d}"

            # Determine caller entity ID
            if caller_name and caller_name.lower() != 'nan':
                src_id, src_label = resolver.resolve_person(caller_name)
                src_type = "Person"
            elif caller_no:
                src_id, src_label = resolver.resolve_phone(caller_no)
                src_type = "Phone"
            else:
                continue

            # Determine receiver entity ID
            if receiver_name and receiver_name.lower() != 'nan':
                tgt_id, tgt_label = resolver.resolve_person(receiver_name)
                tgt_type = "Person"
            elif receiver_no:
                tgt_id, tgt_label = resolver.resolve_phone(receiver_no)
                tgt_type = "Phone"
            else:
                continue

            # Add nodes
            nodes.append(NodeSchema(
                id=src_id,
                label=src_label,
                type=src_type,
                attributes={"phone": caller_no} if caller_no else {}
            ))
            nodes.append(NodeSchema(
                id=tgt_id,
                label=tgt_label,
                type=tgt_type,
                attributes={"phone": receiver_no} if receiver_no else {}
            ))

            # Add CALLED edge
            edges.append(EdgeSchema(
                id=f"edge_call_{src_id}_{tgt_id}_{idx}",
                source=src_id,
                target=tgt_id,
                type="Call",
                weight=1.0 + (duration / 120.0),
                last_seen=timestamp,
                evidence_ref=rec_id,
                attributes={
                    "duration_sec": duration,
                    "tower_location": location,
                    "timestamp": timestamp,
                    "caller_no": caller_no,
                    "receiver_no": receiver_no
                }
            ))

    except Exception as e:
        warnings.append(f"CDR CSV parsing error: {str(e)}")

    return nodes, edges, warnings
