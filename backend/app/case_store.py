import os
import networkx as nx
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from .models.schemas import (
    NodeSchema, EdgeSchema, AnomalySchema, KeyIndividualSchema,
    TemporalHeatmapPoint, GeoHeatmapPoint, CooccurrenceMatrixData,
    TimelineEvent, CaseSummary, CaseDetail, ExtractionPreview
)
from .pipeline.resolve_entities import EntityResolver
from .pipeline.ner import extract_entities_from_text, detect_regional_language
from .pipeline.parse_pdf import parse_pdf_document
from .pipeline.parse_cdr import parse_cdr_file
from .pipeline.parse_txn import parse_financial_transactions
from .analytics.centrality import compute_centrality_and_rank
from .analytics.community import detect_communities
from .analytics.anomaly import detect_anomalies
from .analytics.heatmap_agg import (
    aggregate_temporal_heatmap, aggregate_geo_heatmap,
    compute_cooccurrence_matrix, generate_chronological_timeline
)
from .audit import AuditChain

class CaseInstance:
    """Represents a single investigation case and its graph state."""
    def __init__(self, case_id: str, name: str, description: str):
        self.case_id = case_id
        self.name = name
        self.description = description
        self.created_at = datetime.now().isoformat()
        
        self.resolver = EntityResolver()
        self.G = nx.Graph()
        
        # Maps node_id -> NodeSchema
        self.nodes_dict: Dict[str, NodeSchema] = {}
        # List of EdgeSchema
        self.edges_list: List[EdgeSchema] = []
        
        # Analytics cache
        self.cached_detail: Optional[CaseDetail] = None
        self.regional_language_detected = False
        self.audit_chain = AuditChain()

    def add_nodes_and_edges(
        self,
        nodes: List[NodeSchema],
        edges: List[EdgeSchema],
        recalculate: bool = True
    ):
        """Adds nodes and edges to the case graph and invalidates cache."""
        for n in nodes:
            if n.id not in self.nodes_dict:
                self.nodes_dict[n.id] = n
                self.G.add_node(n.id, label=n.label, type=n.type)
            else:
                # Merge attributes
                self.nodes_dict[n.id].attributes.update(n.attributes)
                # Keep more descriptive label if available
                if len(n.label) > len(self.nodes_dict[n.id].label) and "." not in n.label:
                    self.nodes_dict[n.id].label = n.label
                    self.G.nodes[n.id]['label'] = n.label

        for e in edges:
            self.edges_list.append(e)
            self.G.add_edge(
                e.source,
                e.target,
                id=e.id,
                weight=e.weight,
                type=e.type,
                evidence_ref=e.evidence_ref,
                **e.attributes,
            )

        self.audit_chain.append(
            "graph_ingestion",
            {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "node_ids": sorted(n.id for n in nodes),
                "edge_ids": sorted(e.id for e in edges if e.id),
            },
        )

        if recalculate:
            self.compute_analytics()

    def compute_analytics(self) -> CaseDetail:
        """Runs the complete network analysis pass and caches results."""
        # 1. Louvain Communities
        comm_map = detect_communities(self.G)
        for nid, cid in comm_map.items():
            if nid in self.nodes_dict:
                self.nodes_dict[nid].community_id = cid

        # 2. Centrality & Key Individuals
        centralities, key_individuals = compute_centrality_and_rank(
            self.G, self.nodes_dict, self.edges_list
        )
        for nid, score in centralities.items():
            if nid in self.nodes_dict:
                self.nodes_dict[nid].centrality_score = score
                self.nodes_dict[nid].risk_flag = (score >= 0.35)

        # 3. Anomalies
        anomalies = detect_anomalies(self.edges_list)

        # 4. Heatmaps & Timeline
        temporal = aggregate_temporal_heatmap(self.edges_list)
        geo = aggregate_geo_heatmap(self.edges_list, list(self.nodes_dict.values()))
        coocc = compute_cooccurrence_matrix(list(self.nodes_dict.values()), self.edges_list)
        timeline = generate_chronological_timeline(self.edges_list, list(self.nodes_dict.values()))

        summary = CaseSummary(
            case_id=self.case_id,
            name=self.name,
            description=self.description,
            created_at=self.created_at,
            total_nodes=len(self.nodes_dict),
            total_edges=len(self.edges_list),
            total_anomalies=len(anomalies),
            total_communities=len(set(comm_map.values())) if comm_map else 0,
            regional_language_warning=self.regional_language_detected
        )

        self.cached_detail = CaseDetail(
            summary=summary,
            nodes=list(self.nodes_dict.values()),
            edges=self.edges_list,
            key_individuals=key_individuals,
            anomalies=anomalies,
            temporal_heatmap=temporal,
            geo_heatmap=geo,
            cooccurrence=coocc,
            timeline=timeline
        )
        return self.cached_detail


class CaseStore:
    """Singleton case store managing active investigation cases."""
    def __init__(self):
        self.cases: Dict[str, CaseInstance] = {}
        self.active_case_id: str = "demo_case_001"
        self._sample_case_ready = False

    def get_case(self, case_id: str) -> Optional[CaseInstance]:
        return self.cases.get(case_id)

    def get_or_create_case(self, case_id: str, name: str = "", description: str = "") -> CaseInstance:
        if case_id not in self.cases:
            self.cases[case_id] = CaseInstance(
                case_id=case_id,
                name=name or f"Investigation Case {case_id}",
                description=description or "Interstate syndicate intelligence dossier"
            )
        return self.cases[case_id]

    def list_cases(self) -> List[CaseSummary]:
        results = []
        for c in self.cases.values():
            if c.cached_detail:
                results.append(c.cached_detail.summary)
            else:
                results.append(CaseSummary(
                    case_id=c.case_id,
                    name=c.name,
                    description=c.description,
                    created_at=c.created_at,
                    total_nodes=len(c.nodes_dict),
                    total_edges=len(c.edges_list),
                    total_anomalies=0,
                    total_communities=0
                ))
        return results

    def load_sample_dataset(self) -> CaseDetail:
        """
        Loads and parses the 3 bundled sample data files:
        - sample_unstructured_reports.pdf
        - sample_cdr_data.csv
        - sample_financial_transactions.xlsx
        Caches the parsed result for sub-3-second load times.
        """
        demo_id = "demo_case_001"
        case = CaseInstance(
            case_id=demo_id,
            name="Bharat SecureX AI (NCRB Interstate Syndicate)",
            description="Multi-source intelligence investigation into interstate trafficking, extortion, and shell financial networks across Delhi NCR, UP, Kolkata, and Mumbai."
        )

        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        # Search candidate directories
        candidate_dirs = [
            os.path.join(base_dir, "sample_data"),
            os.path.join(base_dir, "..", "sample_data")
        ]

        sample_dir = None
        for cd in candidate_dirs:
            if os.path.exists(os.path.join(cd, "sample_unstructured_reports.pdf")):
                sample_dir = cd
                break

        if not sample_dir:
            raise FileNotFoundError("Sample data directory not found.")

        pdf_path = os.path.join(sample_dir, "sample_unstructured_reports.pdf")
        csv_path = os.path.join(sample_dir, "sample_cdr_data.csv")
        xlsx_path = os.path.join(sample_dir, "sample_financial_transactions.xlsx")

        # 1. Ingest PDF
        pdf_nodes, pdf_edges, pdf_warns = parse_pdf_document(
            pdf_path, "sample_unstructured_reports.pdf", case.resolver
        )
        if any("Regional-language" in w for w in pdf_warns):
            case.regional_language_detected = True
        case.add_nodes_and_edges(pdf_nodes, pdf_edges, recalculate=False)

        # 2. Ingest CDR CSV
        cdr_nodes, cdr_edges, _ = parse_cdr_file(
            csv_path, "sample_cdr_data.csv", case.resolver
        )
        case.add_nodes_and_edges(cdr_nodes, cdr_edges, recalculate=False)

        # 3. Ingest Financial Transactions XLSX
        txn_nodes, txn_edges, _ = parse_financial_transactions(
            xlsx_path, "sample_financial_transactions.xlsx", case.resolver
        )
        case.add_nodes_and_edges(txn_nodes, txn_edges, recalculate=False)

        # 4. Run Analytics Pass
        detail = case.compute_analytics()
        self.cases[demo_id] = case
        self.active_case_id = demo_id
        self._sample_case_ready = True
        return detail

    def paste_intel_snippet(
        self,
        case_id: str,
        text: str,
        source_label: str = "Pasted Intel"
    ) -> CaseDetail:
        """
        Parses pasted text snippet, extracts entities via NER, links them,
        and incrementally recomputes the case graph.
        """
        case = self.get_or_create_case(case_id)
        
        has_regional = detect_regional_language(text)
        if has_regional:
            case.regional_language_detected = True

        # Generate a Document node for this snippet
        doc_idx = len([n for n in case.nodes_dict.values() if n.type == "Document"]) + 1
        doc_id = f"doc_intel_snippet_{doc_idx}"
        doc_node = NodeSchema(
            id=doc_id,
            label=f"{source_label} #{doc_idx}",
            type="Document",
            attributes={"excerpt": text[:200] + ("..." if len(text) > 200 else "")}
        )
        
        new_nodes = [doc_node]
        new_edges = []
        page_entity_ids = []

        ent_dict = extract_entities_from_text(text)

        for p in ent_dict["persons"]:
            p_id, p_label = case.resolver.resolve_person(p["name"])
            page_entity_ids.append(p_id)
            new_nodes.append(NodeSchema(id=p_id, label=p_label, type="Person"))
            new_edges.append(EdgeSchema(
                id=f"edge_{p_id}_{doc_id}",
                source=p_id,
                target=doc_id,
                type="Mentioned_In",
                weight=1.0,
                evidence_ref=doc_node.label
            ))

        for ph in ent_dict["phones"]:
            ph_id, ph_label = case.resolver.resolve_phone(ph["value"])
            page_entity_ids.append(ph_id)
            new_nodes.append(NodeSchema(id=ph_id, label=ph_label, type="Phone"))
            new_edges.append(EdgeSchema(
                id=f"edge_{ph_id}_{doc_id}",
                source=ph_id,
                target=doc_id,
                type="Mentioned_In",
                weight=1.0,
                evidence_ref=doc_node.label
            ))

        for veh in ent_dict["vehicles"]:
            v_id, v_label = case.resolver.resolve_vehicle(veh["value"])
            page_entity_ids.append(v_id)
            new_nodes.append(NodeSchema(id=v_id, label=v_label, type="Vehicle"))
            new_edges.append(EdgeSchema(
                id=f"edge_{v_id}_{doc_id}",
                source=v_id,
                target=doc_id,
                type="Mentioned_In",
                weight=1.0,
                evidence_ref=doc_node.label
            ))

        for org in ent_dict["organizations"]:
            org_id, org_label = case.resolver.resolve_organization(org["name"])
            page_entity_ids.append(org_id)
            new_nodes.append(NodeSchema(id=org_id, label=org_label, type="Organization"))
            new_edges.append(EdgeSchema(
                id=f"edge_{org_id}_{doc_id}",
                source=org_id,
                target=doc_id,
                type="Mentioned_In",
                weight=1.0,
                evidence_ref=doc_node.label
            ))

        # Inter-entity connections
        unique_ents = list(dict.fromkeys(page_entity_ids))
        for i in range(len(unique_ents)):
            for j in range(i + 1, len(unique_ents)):
                new_edges.append(EdgeSchema(
                    id=f"comention_{unique_ents[i]}_{unique_ents[j]}_{doc_id}",
                    source=unique_ents[i],
                    target=unique_ents[j],
                    type="Co_Mentioned",
                    weight=0.5,
                    evidence_ref=doc_node.label
                ))

        case.add_nodes_and_edges(new_nodes, new_edges, recalculate=True)
        return case.cached_detail

    def add_identity_intel(self, request: Any) -> CaseDetail:
        """Add identity, SIM/UPI, FIR and location evidence to a case graph."""
        case = self.get_or_create_case(request.case_id)
        person_id, person_label = case.resolver.resolve_person(request.name)
        masked_id = None
        if request.id_proof_number:
            id_value = str(request.id_proof_number)
            masked_id = f"{'*' * max(0, len(id_value) - 4)}{id_value[-4:]}"
        identity_attributes = {
            "address": request.address,
            "id_proof_number": masked_id,
            "aliases": request.alias_names,
            "fir_number": request.fir_number,
        }
        person = NodeSchema(
            id=person_id,
            label=person_label,
            type="Person",
            attributes={k: v for k, v in identity_attributes.items() if v not in (None, [], "")},
        )
        nodes = [person]
        edges: List[EdgeSchema] = []

        if request.fir_number:
            fir_id = f"fir_{request.fir_number.lower().replace(' ', '_')}"
            nodes.append(NodeSchema(
                id=fir_id,
                label=f"FIR {request.fir_number}",
                type="Document",
                attributes={
                    "fir_number": request.fir_number,
                    "metadata": request.fir_metadata,
                },
            ))
            edges.append(EdgeSchema(
                id=f"edge_{person_id}_{fir_id}",
                source=person_id,
                target=fir_id,
                type="Mentioned_In",
                evidence_ref=request.fir_number,
                attributes={"metadata": request.fir_metadata},
            ))

        def add_linked_node(value: Optional[str], node_type: str, prefix: str, edge_type: str) -> Optional[str]:
            if not value:
                return None
            if node_type == "Phone":
                node_id, label = case.resolver.resolve_phone(value)
            elif node_type == "Location":
                node_id, label = case.resolver.resolve_location(value)
            else:
                node_id, label = f"{prefix}_{value.lower().replace(' ', '_')}", value
            nodes.append(NodeSchema(id=node_id, label=label, type=node_type, attributes={}))
            edges.append(EdgeSchema(
                id=f"edge_{person_id}_{node_id}",
                source=person_id,
                target=node_id,
                type=edge_type,
                evidence_ref=request.fir_number or "identity-intel",
            ))
            return node_id

        add_linked_node(request.phone_number, "Phone", "phone", "Uses_Phone")
        add_linked_node(request.sim_number, "SIM", "sim", "Uses_SIM")
        add_linked_node(request.upi_id, "Account", "upi", "Uses_UPI")
        add_linked_node(request.address, "Location", "loc", "Located_At")

        for alias in request.alias_names:
            alias_id = f"alias_{person_id}_{alias.lower().replace(' ', '_')}"
            nodes.append(NodeSchema(id=alias_id, label=alias, type="Alias", attributes={"for": person_id}))
            edges.append(EdgeSchema(
                id=f"edge_{person_id}_{alias_id}",
                source=person_id,
                target=alias_id,
                type="Known_Alias",
                evidence_ref=request.fir_number or "identity-intel",
            ))

        for index, log in enumerate(request.geolocation_logs + request.co_location_logs):
            location = log.get("location") or log.get("tower_location")
            location_id = add_linked_node(
                str(location), "Location", "loc", "Co_Located_At"
            ) if location else None
            if not location_id:
                continue
            edges.append(EdgeSchema(
                id=f"geo_{person_id}_{index}",
                source=person_id,
                target=location_id,
                type="Geolocation",
                evidence_ref=request.fir_number or "location-log",
                attributes={"timestamp": log.get("timestamp"), "source": log.get("source")},
            ))

        case.add_nodes_and_edges(nodes, edges, recalculate=True)
        return case.cached_detail

# Global instance
case_store = CaseStore()
