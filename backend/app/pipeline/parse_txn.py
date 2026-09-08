import pandas as pd
from typing import List, Dict, Any, Tuple
from .resolve_entities import EntityResolver
from ..models.schemas import NodeSchema, EdgeSchema

def parse_financial_transactions(
    file_path_or_bytes: Any,
    filename: str,
    resolver: EntityResolver
) -> Tuple[List[NodeSchema], List[EdgeSchema], List[str]]:
    """
    Parses financial transactions XLSX into PAID edges.
    Extracts amounts, transaction modes, dates, and remarks.
    """
    nodes: List[NodeSchema] = []
    edges: List[EdgeSchema] = []
    warnings: List[str] = []

    try:
        df = pd.read_excel(file_path_or_bytes)
        
        # Normalize column names
        col_map = {c.lower().strip().replace(' ', '_'): c for c in df.columns}
        
        txn_id_col = col_map.get('txn_id', col_map.get('transaction_id', col_map.get('id', None)))
        from_acc_col = col_map.get('from_account', col_map.get('source_account', None))
        from_name_col = col_map.get('from_name', col_map.get('sender_name', col_map.get('from', None)))
        to_acc_col = col_map.get('to_account', col_map.get('destination_account', None))
        to_name_col = col_map.get('to_name', col_map.get('receiver_name', col_map.get('to', None)))
        amount_col = col_map.get('amount', col_map.get('txn_amount', None))
        mode_col = col_map.get('mode', col_map.get('type', col_map.get('payment_mode', None)))
        date_col = col_map.get('date', col_map.get('timestamp', col_map.get('txn_date', None)))
        remarks_col = col_map.get('remarks', col_map.get('description', None))

        for idx, row in df.iterrows():
            from_name = str(row[from_name_col]).strip() if from_name_col and pd.notna(row[from_name_col]) else None
            from_acc = str(row[from_acc_col]).strip() if from_acc_col and pd.notna(row[from_acc_col]) else None
            
            to_name = str(row[to_name_col]).strip() if to_name_col and pd.notna(row[to_name_col]) else None
            to_acc = str(row[to_acc_col]).strip() if to_acc_col and pd.notna(row[to_acc_col]) else None
            
            amount = float(row[amount_col]) if amount_col and pd.notna(row[amount_col]) else 0.0
            mode = str(row[mode_col]).strip() if mode_col and pd.notna(row[mode_col]) else "TRANSFER"
            date_str = str(row[date_col]).strip() if date_col and pd.notna(row[date_col]) else None
            remarks = str(row[remarks_col]).strip() if remarks_col and pd.notna(row[remarks_col]) else ""
            txn_id = str(row[txn_id_col]).strip() if txn_id_col and pd.notna(row[txn_id_col]) else f"TXN-{idx+1:04d}"

            # Clean name from corporate descriptors if parenthesized e.g. "Rajan Malhotra (Apex Logistics)"
            src_clean_name = from_name
            if from_name and "(" in from_name:
                src_clean_name = from_name.split("(")[0].strip()

            tgt_clean_name = to_name
            if to_name and "(" in to_name:
                tgt_clean_name = to_name.split("(")[0].strip()

            # Determine source entity
            if src_clean_name and src_clean_name.lower() != 'nan':
                src_id, src_label = resolver.resolve_person(src_clean_name)
                src_type = "Person"
            elif from_acc:
                src_id = f"acc_{from_acc.lower()}"
                src_label = f"Account {from_acc}"
                src_type = "Account"
            else:
                continue

            # Determine destination entity
            if tgt_clean_name and tgt_clean_name.lower() != 'nan':
                tgt_id, tgt_label = resolver.resolve_person(tgt_clean_name)
                tgt_type = "Person"
            elif to_acc:
                tgt_id = f"acc_{to_acc.lower()}"
                tgt_label = f"Account {to_acc}"
                tgt_type = "Account"
            else:
                continue

            # Add nodes
            nodes.append(NodeSchema(
                id=src_id,
                label=src_label,
                type=src_type,
                attributes={"account": from_acc} if from_acc else {}
            ))
            nodes.append(NodeSchema(
                id=tgt_id,
                label=tgt_label,
                type=tgt_type,
                attributes={"account": to_acc} if to_acc else {}
            ))

            # Weight scaled logarithmically by amount
            weight = 1.0 + (min(amount, 1000000.0) / 100000.0)

            edges.append(EdgeSchema(
                id=f"edge_paid_{src_id}_{tgt_id}_{idx}",
                source=src_id,
                target=tgt_id,
                type="Transaction",
                weight=round(weight, 2),
                last_seen=date_str,
                evidence_ref=txn_id,
                attributes={
                    "amount": amount,
                    "mode": mode,
                    "date": date_str,
                    "remarks": remarks,
                    "from_account": from_acc,
                    "to_account": to_acc
                }
            ))

    except Exception as e:
        warnings.append(f"Financial XLSX parsing error: {str(e)}")

    return nodes, edges, warnings
