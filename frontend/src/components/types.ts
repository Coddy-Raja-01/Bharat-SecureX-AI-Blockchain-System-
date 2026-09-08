export interface NodeSchema {
  id: string;
  label: string;
  type: string; // Person, Organization, Vehicle, Location, Document, Phone, Account
  centrality_score: number;
  community_id: number;
  risk_flag: boolean;
  attributes: Record<string, any>;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

export interface EdgeSchema {
  id?: string;
  source: any;
  target: any;
  type: string; // Call, Transaction, Mentioned_In, Uses_Vehicle, Uses_Phone, Co_Accused
  weight: number;
  last_seen?: string | null;
  evidence_ref?: string | null;
  attributes: Record<string, any>;
}

export interface KeyIndividualSchema {
  id: string;
  label: string;
  type: string;
  centrality_score: number;
  pagerank: number;
  betweenness: number;
  community_id: number;
  rationale: string;
  risk_flag: boolean;
}

export interface AnomalySchema {
  id: string;
  entity_ids: string[];
  description: string;
  severity: string; // high, medium, low
  evidence_refs: string[];
  attributes: Record<string, any>;
}

export interface TemporalHeatmapPoint {
  day: string;
  hour: number;
  count: number;
}

export interface GeoHeatmapPoint {
  lat: number;
  lng: number;
  weight: number;
  location: string;
}

export interface CooccurrenceMatrixData {
  labels: string[];
  entity_ids: string[];
  matrix: number[][];
}

export interface TimelineEvent {
  id: string;
  type: string;
  timestamp: string;
  title: string;
  description: string;
  entity_ids: string[];
  evidence_ref: string;
  location?: string | null;
}

export interface CaseSummary {
  case_id: string;
  name: string;
  description: string;
  created_at: string;
  total_nodes: number;
  total_edges: number;
  total_anomalies: number;
  total_communities: number;
  regional_language_warning?: boolean;
}

export interface CaseDetail {
  summary: CaseSummary;
  nodes: NodeSchema[];
  edges: EdgeSchema[];
  key_individuals: KeyIndividualSchema[];
  anomalies: AnomalySchema[];
  temporal_heatmap: TemporalHeatmapPoint[];
  geo_heatmap: GeoHeatmapPoint[];
  cooccurrence: CooccurrenceMatrixData;
  timeline: TimelineEvent[];
}

export interface ExtractionPreview {
  source_filename: string;
  file_type: string;
  nodes_found: NodeSchema[];
  edges_found: EdgeSchema[];
  warnings: string[];
}
