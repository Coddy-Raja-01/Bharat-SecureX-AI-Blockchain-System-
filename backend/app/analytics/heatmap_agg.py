from typing import List, Dict, Any, Tuple
from datetime import datetime
from collections import defaultdict
from ..models.schemas import (
    EdgeSchema, NodeSchema, TemporalHeatmapPoint,
    GeoHeatmapPoint, CooccurrenceMatrixData, TimelineEvent
)

# Static geocoding coordinates for demo locations across India
CITY_COORDINATES = {
    "connaught place, new delhi": (28.6315, 77.2167, "Connaught Place, New Delhi"),
    "rohini sector 7, new delhi": (28.7159, 77.1126, "Rohini, New Delhi"),
    "lajpat nagar, new delhi": (28.5677, 77.2433, "Lajpat Nagar, New Delhi"),
    "new delhi": (28.6139, 77.2090, "New Delhi"),
    "noida sector 18, noida": (28.5708, 77.3259, "Noida Sector 18, Uttar Pradesh"),
    "noida sector 62, noida": (28.6279, 77.3649, "Noida Sector 62, Uttar Pradesh"),
    "noida": (28.5355, 77.3910, "Noida, Uttar Pradesh"),
    "cyber city, gurugram": (28.4950, 77.0895, "Cyber City, Gurugram, Haryana"),
    "gurugram": (28.4595, 77.0266, "Gurugram, Haryana"),
    "gomti nagar, lucknow": (26.8530, 80.9984, "Gomti Nagar, Lucknow, Uttar Pradesh"),
    "lucknow": (26.8467, 80.9462, "Lucknow, Uttar Pradesh"),
    "salt lake city, kolkata": (22.5868, 88.4178, "Salt Lake City, Kolkata, West Bengal"),
    "kolkata": (22.5726, 88.3639, "Kolkata, West Bengal"),
    "bandra west, mumbai": (19.0596, 72.8295, "Bandra West, Mumbai, Maharashtra"),
    "mumbai": (19.0760, 72.8777, "Mumbai, Maharashtra"),
}

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def geocode_location(loc_str: str) -> Tuple[float, float, str]:
    """Matches a location string against static Indian coordinates."""
    clean = loc_str.lower().strip()
    # Exact match
    if clean in CITY_COORDINATES:
        return CITY_COORDINATES[clean]
    
    # Substring match
    for key, val in CITY_COORDINATES.items():
        if key in clean or clean in key:
            return val
            
    # Default fallback: New Delhi
    return (28.6139, 77.2090, loc_str)

def aggregate_temporal_heatmap(edges: List[EdgeSchema]) -> List[TemporalHeatmapPoint]:
    """
    Buckets timestamped edges into (day_of_week, hour) -> count.
    Surfaces 'active 1-3 AM' night operational patterns.
    """
    counts = defaultdict(int)

    for e in edges:
        ts_str = e.last_seen or e.attributes.get("timestamp") or e.attributes.get("date")
        if not ts_str:
            continue
        try:
            # Parse ISO or standard formats
            dt = None
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d-%b-%Y"):
                try:
                    dt = datetime.strptime(ts_str.strip(), fmt)
                    break
                except ValueError:
                    pass

            if dt:
                day_name = DAYS_OF_WEEK[dt.weekday()]
                hour = dt.hour
                counts[(day_name, hour)] += 1
        except Exception:
            pass

    # Ensure all (day, hour) slots are present so the matrix renders continuously
    result: List[TemporalHeatmapPoint] = []
    for day in DAYS_OF_WEEK:
        for hour in range(24):
            cnt = counts.get((day, hour), 0)
            result.append(TemporalHeatmapPoint(day=day, hour=hour, count=cnt))

    return result

def aggregate_geo_heatmap(
    edges: List[EdgeSchema],
    nodes: List[NodeSchema]
) -> List[GeoHeatmapPoint]:
    """
    Buckets location-tagged events and node mentions into (lat, lng) -> weight.
    """
    loc_weights = defaultdict(float)
    loc_labels = {}

    # 1. From edge tower locations
    for e in edges:
        tower_loc = e.attributes.get("tower_location")
        if tower_loc and tower_loc != "Unknown":
            lat, lng, canon_name = geocode_location(tower_loc)
            key = (round(lat, 4), round(lng, 4))
            loc_weights[key] += float(e.weight)
            loc_labels[key] = canon_name

    # 2. From Document nodes / FIR locations mentioned
    for n in nodes:
        if n.type == "Location":
            lat, lng, canon_name = geocode_location(n.label)
            key = (round(lat, 4), round(lng, 4))
            loc_weights[key] += 3.0
            loc_labels[key] = canon_name
        elif n.type == "Document":
            text = n.attributes.get("first_line", "") + " " + n.attributes.get("excerpt", "")
            for city_key, coord_info in CITY_COORDINATES.items():
                if city_key.split(",")[0] in text.lower():
                    lat, lng, canon_name = coord_info
                    key = (round(lat, 4), round(lng, 4))
                    loc_weights[key] += 4.0
                    loc_labels[key] = canon_name

    geo_points: List[GeoHeatmapPoint] = []
    for (lat, lng), wt in loc_weights.items():
        geo_points.append(GeoHeatmapPoint(
            lat=lat,
            lng=lng,
            weight=round(wt, 2),
            location=loc_labels.get((lat, lng), f"{lat}, {lng}")
        ))

    # Sort descending by weight
    geo_points.sort(key=lambda x: x.weight, reverse=True)
    return geo_points

def compute_cooccurrence_matrix(
    nodes: List[NodeSchema],
    edges: List[EdgeSchema],
    max_entities: int = 15
) -> CooccurrenceMatrixData:
    """
    Builds entity x entity interaction strength matrix (calls + transactions + co-mentions).
    """
    # Select top individuals / active entities
    person_org_nodes = [n for n in nodes if n.type in ("Person", "Organization", "Vehicle")]
    person_org_nodes.sort(key=lambda n: n.centrality_score, reverse=True)
    selected = person_org_nodes[:max_entities]

    entity_ids = [n.id for n in selected]
    labels = [n.label for n in selected]
    id_to_idx = {eid: idx for idx, eid in enumerate(entity_ids)}

    n_size = len(entity_ids)
    raw_matrix = [[0.0 for _ in range(n_size)] for _ in range(n_size)]

    for e in edges:
        u = e.source
        v = e.target
        if u in id_to_idx and v in id_to_idx:
            i, j = id_to_idx[u], id_to_idx[v]
            amt = float(e.attributes.get("amount", 0.0))
            score = 1.0 + (amt / 50000.0) if amt > 0 else 1.0
            raw_matrix[i][j] += score
            raw_matrix[j][i] += score

    # Normalize matrix to 0.0 - 1.0
    max_val = max((max(row) for row in raw_matrix), default=1.0)
    if max_val == 0:
        max_val = 1.0

    normalized_matrix = [
        [round(raw_matrix[i][j] / max_val, 3) for j in range(n_size)]
        for i in range(n_size)
    ]

    return CooccurrenceMatrixData(
        labels=labels,
        entity_ids=entity_ids,
        matrix=normalized_matrix
    )

def generate_chronological_timeline(
    edges: List[EdgeSchema],
    nodes: List[NodeSchema]
) -> List[TimelineEvent]:
    """
    Extracts a chronological timeline of all events across calls, transactions, and documents.
    """
    events: List[TimelineEvent] = []

    # 1. From edges (Calls & Transactions)
    for idx, e in enumerate(edges):
        ts = e.last_seen or e.attributes.get("timestamp") or e.attributes.get("date")
        if not ts:
            continue

        if e.type == "Call":
            dur = e.attributes.get("duration_sec", 60)
            loc = e.attributes.get("tower_location", "Unknown")
            events.append(TimelineEvent(
                id=f"tl_call_{idx}",
                type="Call",
                timestamp=ts,
                title=f"Call: {e.source} -> {e.target}",
                description=f"Duration: {dur}s | Tower: {loc}",
                entity_ids=[e.source, e.target],
                evidence_ref=e.evidence_ref or f"CDR-{idx}",
                location=loc
            ))
        elif e.type == "Transaction":
            amt = float(e.attributes.get("amount", 0.0))
            mode = e.attributes.get("mode", "TRANSFER")
            remarks = e.attributes.get("remarks", "")
            events.append(TimelineEvent(
                id=f"tl_txn_{idx}",
                type="Transaction",
                timestamp=ts,
                title=f"Payment: ₹{int(amt):,} ({mode})",
                description=f"From: {e.source} To: {e.target} | {remarks}",
                entity_ids=[e.source, e.target],
                evidence_ref=e.evidence_ref or f"TXN-{idx}",
                location=None
            ))

    # 2. From Document nodes
    for n in nodes:
        if n.type == "Document":
            excerpt = n.attributes.get("excerpt", "")
            first_line = n.attributes.get("first_line", n.label)
            # Try finding date in excerpt e.g. 04-AUG-2026
            events.append(TimelineEvent(
                id=f"tl_doc_{n.id}",
                type="FIR" if "FIR" in first_line else "Surveillance",
                timestamp="2026-08-10 09:00:00",
                title=first_line,
                description=excerpt[:140] + "...",
                entity_ids=[n.id],
                evidence_ref=n.label,
                location=None
            ))

    # Sort chronologically
    events.sort(key=lambda x: x.timestamp)
    return events
