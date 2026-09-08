from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class NodeSchema(BaseModel):
    id: str
    label: str
    type: str = "Person"  # Person, Organization, Vehicle, Location, Document, Account
    centrality_score: float = 0.0
    community_id: int = 0
    risk_flag: bool = False
    attributes: Dict[str, Any] = Field(default_factory=dict)

class EdgeSchema(BaseModel):
    id: Optional[str] = None
    source: str
    target: str
    type: str = "Connected"  # Call, Transaction, Mentioned_In, Operates, Associated
    weight: float = 1.0
    last_seen: Optional[str] = None
    evidence_ref: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)

class AnomalySchema(BaseModel):
    id: str
    entity_ids: List[str]
    description: str
    severity: str = "medium"  # high, medium, low
    evidence_refs: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)

class KeyIndividualSchema(BaseModel):
    id: str
    label: str
    type: str = "Person"
    centrality_score: float
    pagerank: float
    betweenness: float
    community_id: int
    rationale: str
    risk_flag: bool = False

class TemporalHeatmapPoint(BaseModel):
    day: str
    hour: int
    count: int

class GeoHeatmapPoint(BaseModel):
    lat: float
    lng: float
    weight: float
    location: str

class CooccurrenceMatrixData(BaseModel):
    labels: List[str]
    entity_ids: List[str]
    matrix: List[List[float]]

class TimelineEvent(BaseModel):
    id: str
    type: str  # FIR, Call, Transaction, Surveillance, Intel
    timestamp: str
    title: str
    description: str
    entity_ids: List[str]
    evidence_ref: str
    location: Optional[str] = None

class ExtractionPreview(BaseModel):
    source_filename: str
    file_type: str
    nodes_found: List[NodeSchema]
    edges_found: List[EdgeSchema]
    warnings: List[str] = Field(default_factory=list)

class CaseSummary(BaseModel):
    case_id: str
    name: str
    description: str
    created_at: str
    total_nodes: int
    total_edges: int
    total_anomalies: int
    total_communities: int
    regional_language_warning: bool = False

class CaseDetail(BaseModel):
    summary: CaseSummary
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]
    key_individuals: List[KeyIndividualSchema]
    anomalies: List[AnomalySchema]
    temporal_heatmap: List[TemporalHeatmapPoint]
    geo_heatmap: List[GeoHeatmapPoint]
    cooccurrence: CooccurrenceMatrixData
    timeline: List[TimelineEvent]

class PasteIntelRequest(BaseModel):
    text: str
    case_id: str = "demo_case_001"
    source_label: Optional[str] = "Pasted Intel"


class IdentityIntelRequest(BaseModel):
    case_id: str = "demo_case_001"
    name: str
    address: Optional[str] = None
    id_proof_number: Optional[str] = None
    alias_names: List[str] = Field(default_factory=list)
    phone_number: Optional[str] = None
    sim_number: Optional[str] = None
    upi_id: Optional[str] = None
    fir_number: Optional[str] = None
    fir_metadata: Dict[str, Any] = Field(default_factory=dict)
    geolocation_logs: List[Dict[str, Any]] = Field(default_factory=list)
    co_location_logs: List[Dict[str, Any]] = Field(default_factory=list)
