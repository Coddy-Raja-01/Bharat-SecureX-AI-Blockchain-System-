from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..case_store import case_store
from ..models.schemas import (
    CaseSummary, CaseDetail, NodeSchema, EdgeSchema,
    KeyIndividualSchema, AnomalySchema, TemporalHeatmapPoint,
    GeoHeatmapPoint, CooccurrenceMatrixData, TimelineEvent
)

router = APIRouter(prefix="/api/cases", tags=["Cases"])

@router.get("", response_model=List[CaseSummary])
def list_cases():
    return case_store.list_cases()

@router.post("/create", response_model=CaseSummary)
def create_case(case_id: str, name: str, description: Optional[str] = ""):
    instance = case_store.get_or_create_case(case_id, name, description or "")
    detail = instance.compute_analytics()
    return detail.summary

@router.get("/{case_id}", response_model=CaseDetail)
def get_case_detail(case_id: str):
    instance = case_store.get_case(case_id)
    if not instance:
        # If demo case is requested and not loaded yet, load it automatically
        if case_id == "demo_case_001":
            return case_store.load_sample_dataset()
        raise HTTPException(status_code=404, detail="Case not found")
    
    if not instance.cached_detail:
        return instance.compute_analytics()
    return instance.cached_detail

@router.get("/{case_id}/graph")
def get_case_graph(case_id: str):
    detail = get_case_detail(case_id)
    return {
        "nodes": [n.model_dump() for n in detail.nodes],
        "edges": [e.model_dump() for e in detail.edges]
    }

@router.get("/{case_id}/key-individuals", response_model=List[KeyIndividualSchema])
def get_key_individuals(case_id: str):
    detail = get_case_detail(case_id)
    return detail.key_individuals

@router.get("/{case_id}/anomalies", response_model=List[AnomalySchema])
def get_anomalies(case_id: str):
    detail = get_case_detail(case_id)
    return detail.anomalies

@router.get("/{case_id}/heatmaps")
def get_heatmaps(case_id: str):
    detail = get_case_detail(case_id)
    return {
        "temporal": [t.model_dump() for t in detail.temporal_heatmap],
        "geo": [g.model_dump() for g in detail.geo_heatmap],
        "cooccurrence": detail.cooccurrence.model_dump()
    }

@router.get("/{case_id}/timeline", response_model=List[TimelineEvent])
def get_timeline(case_id: str, entity_id: Optional[str] = None):
    detail = get_case_detail(case_id)
    if not entity_id:
        return detail.timeline
    # Filter timeline by entity
    return [e for e in detail.timeline if entity_id in e.entity_ids]

@router.get("/{case_id}/node/{node_id}")
def get_node_details(case_id: str, node_id: str):
    detail = get_case_detail(case_id)
    target_node = next((n for n in detail.nodes if n.id == node_id), None)
    if not target_node:
        raise HTTPException(status_code=404, detail="Node not found")

    # Find all connected edges
    connected_edges = []
    neighbor_ids = set()
    for e in detail.edges:
        if e.source == node_id or e.target == node_id:
            connected_edges.append(e)
            neighbor_ids.add(e.target if e.source == node_id else e.source)

    neighbors = [n for n in detail.nodes if n.id in neighbor_ids]

    # Find associated anomalies
    node_anomalies = [a for a in detail.anomalies if node_id in a.entity_ids]

    return {
        "node": target_node.model_dump(),
        "neighbors": [n.model_dump() for n in neighbors],
        "edges": [e.model_dump() for e in connected_edges],
        "anomalies": [a.model_dump() for a in node_anomalies]
    }
