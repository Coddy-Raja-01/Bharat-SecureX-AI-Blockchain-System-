import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List


class AuditChain:
    """Small append-only hash chain for provenance verification.

    Only metadata and digests are stored in the chain; raw identity data is not
    copied into the audit record.
    """

    def __init__(self) -> None:
        self._records: List[Dict[str, Any]] = []

    def append(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        previous_hash = self._records[-1]["hash"] if self._records else "0" * 64
        timestamp = datetime.now(timezone.utc).isoformat()
        canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(
            f"{previous_hash}|{timestamp}|{event_type}|{canonical_payload}".encode("utf-8")
        ).hexdigest()
        record = {
            "index": len(self._records),
            "timestamp": timestamp,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
            "hash": digest,
        }
        self._records.append(record)
        return record

    def records(self) -> List[Dict[str, Any]]:
        return list(self._records)

    def verify(self) -> bool:
        previous_hash = "0" * 64
        for record in self._records:
            if record["previous_hash"] != previous_hash:
                return False
            canonical_payload = json.dumps(
                record["payload"], sort_keys=True, separators=(",", ":")
            )
            expected = hashlib.sha256(
                f'{previous_hash}|{record["timestamp"]}|{record["event_type"]}|{canonical_payload}'.encode(
                    "utf-8"
                )
            ).hexdigest()
            if record["hash"] != expected:
                return False
            previous_hash = record["hash"]
        return True
