import os
import io
import tempfile
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import Response
from typing import List, Optional
from pydantic import BaseModel

from ..case_store import case_store
from ..models.schemas import (
    ExtractionPreview, CaseDetail, PasteIntelRequest,
    NodeSchema, EdgeSchema, IdentityIntelRequest
)
from ..pipeline.resolve_entities import EntityResolver
from ..pipeline.parse_pdf import parse_pdf_document
from ..pipeline.parse_cdr import parse_cdr_file
from ..pipeline.parse_txn import parse_financial_transactions

router = APIRouter(prefix="/api", tags=["Ingestion & Demo"])
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

@router.post("/demo/load-sample", response_model=CaseDetail)
def load_sample_case():
    """
    Sub-second 1-click demo loader for Smart India Hackathon judging.
    Pre-loads bundled synthetic case:
    - sample_unstructured_reports.pdf
    - sample_cdr_data.csv
    - sample_financial_transactions.xlsx
    """
    try:
        detail = case_store.load_sample_dataset()
        return detail
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load sample dataset: {str(e)}")

@router.post("/upload/preview", response_model=ExtractionPreview)
async def preview_upload_file(
    file: UploadFile = File(...),
    case_id: str = Form("demo_case_001")
):
    """
    Entity extraction confirmation view:
    Parses the uploaded PDF, CSV, or XLSX file into nodes and edges,
    returning a preview before committing it to the active graph.
    """
    filename = file.filename or "uploaded_file"
    ext = os.path.splitext(filename)[1].lower()

    case = case_store.get_or_create_case(case_id)
    # Use case's resolver so it accurately links against known entities
    resolver = case.resolver

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file exceeds the {MAX_UPLOAD_BYTES // (1024 * 1024)} MiB limit."
        )
    file_bytes_io = io.BytesIO(content)

    nodes: List[NodeSchema] = []
    edges: List[EdgeSchema] = []
    warnings: List[str] = []

    if ext == ".pdf":
        nodes, edges, warnings = parse_pdf_document(file_bytes_io, filename, resolver)
        file_type = "PDF Intelligence / FIR Dossier"
    elif ext == ".csv":
        nodes, edges, warnings = parse_cdr_file(file_bytes_io, filename, resolver)
        file_type = "CDR (Call Detail Records)"
    elif ext in (".xlsx", ".xls"):
        nodes, edges, warnings = parse_financial_transactions(file_bytes_io, filename, resolver)
        file_type = "Financial Transactions Ledger"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Expected PDF, CSV, or XLSX."
        )

    # Deduplicate nodes by ID
    unique_nodes = list({n.id: n for n in nodes}.values())

    return ExtractionPreview(
        source_filename=filename,
        file_type=file_type,
        nodes_found=unique_nodes,
        edges_found=edges,
        warnings=warnings
    )

class UploadCommitRequest(BaseModel):
    case_id: str
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]


@router.post("/upload/commit", response_model=CaseDetail)
def commit_extracted_data(request: UploadCommitRequest):
    """
    Inserts confirmed nodes and edges into the specified case graph and recomputes analytics.
    """
    case = case_store.get_or_create_case(request.case_id)
    case.add_nodes_and_edges(request.nodes, request.edges, recalculate=True)
    return case.cached_detail


@router.post("/intel/identity", response_model=CaseDetail)
def add_identity_intel(request: IdentityIntelRequest):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Identity name cannot be empty")
    return case_store.add_identity_intel(request)


@router.get("/cases/{case_id}/audit")
def get_case_audit(case_id: str):
    case = case_store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"valid": case.audit_chain.verify(), "records": case.audit_chain.records()}

@router.post("/intel/paste", response_model=CaseDetail)
def paste_new_intel(req: PasteIntelRequest):
    """
    Incrementally re-runs NER on the provided intel snippet and merges new entities
    and edges into the current case graph in real-time.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Intel text cannot be empty")

    detail = case_store.paste_intel_snippet(
        case_id=req.case_id,
        text=req.text,
        source_label=req.source_label or "Pasted Field Intel"
    )
    return detail

@router.get("/search")
def search_entities(
    q: str = Query(..., min_length=1),
    case_id: str = Query("demo_case_001")
):
    """
    Searches entities within the case by name, phone number, vehicle plate, or label.
    """
    case = case_store.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    query = q.lower().strip()
    matches = []

    for nid, node in case.nodes_dict.items():
        label = node.label.lower()
        ntype = node.type.lower()
        attrs = str(node.attributes).lower()
        
        if query in label or query in nid.lower() or query in attrs:
            matches.append(node.model_dump())

    return {"query": q, "total_matches": len(matches), "results": matches}

@router.get("/cases/{case_id}/export-report")
def export_case_report(case_id: str):
    """
    Generates a printable law enforcement intelligence case summary report.
    """
    instance = case_store.get_case(case_id)
    if not instance:
        raise HTTPException(status_code=404, detail="Case not found")

    detail = instance.cached_detail or instance.compute_analytics()

    # Generate HTML summary that can be printed or saved as PDF by browser
    report_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Intelligence Dossier - {detail.summary.name}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #1e293b; }}
            .header {{ border-bottom: 3px solid #0284c7; padding-bottom: 12px; margin-bottom: 24px; }}
            .badge {{ background: #ef4444; color: #fff; padding: 4px 8px; font-weight: bold; border-radius: 4px; font-size: 11px; }}
            .section-title {{ font-size: 16px; font-weight: bold; color: #0369a1; margin-top: 24px; border-bottom: 1px solid #e2e8f0; padding-bottom: 6px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
            th, td {{ border: 1px solid #cbd5e1; padding: 8px 10px; text-align: left; }}
            th {{ background: #f8fafc; font-weight: 600; }}
            .anomaly-card {{ background: #fef2f2; border-left: 4px solid #ef4444; padding: 10px; margin-top: 8px; border-radius: 4px; }}
            .kpi-grid {{ display: flex; gap: 16px; margin: 16px 0; }}
            .kpi-box {{ flex: 1; background: #f1f5f9; padding: 12px; border-radius: 6px; text-align: center; }}
            .kpi-val {{ font-size: 20px; font-weight: bold; color: #0f172a; }}
            .kpi-lbl {{ font-size: 11px; color: #64748b; text-transform: uppercase; }}
        </style>
    </head>
    <body>
        <div class="header">
            <span class="badge">CONFIDENTIAL // LAW ENFORCEMENT INTELLIGENCE</span>
            <h1 style="margin: 8px 0 4px 0;">{detail.summary.name}</h1>
            <p style="margin: 0; color: #64748b; font-size: 13px;"><b>Case ID:</b> {detail.summary.case_id} | <b>Generated:</b> {detail.summary.created_at} | <b>Target:</b> SIH26189</p>
            <p style="margin-top: 6px; font-size: 14px;">{detail.summary.description}</p>
        </div>

        <div class="kpi-grid">
            <div class="kpi-box"><div class="kpi-val">{detail.summary.total_nodes}</div><div class="kpi-lbl">Total Entities</div></div>
            <div class="kpi-box"><div class="kpi-val">{detail.summary.total_edges}</div><div class="kpi-lbl">Network Relationships</div></div>
            <div class="kpi-box"><div class="kpi-val">{len(detail.key_individuals)}</div><div class="kpi-lbl">Ranked Targets</div></div>
            <div class="kpi-box"><div class="kpi-val">{detail.summary.total_anomalies}</div><div class="kpi-lbl">Flagged Anomalies</div></div>
            <div class="kpi-box"><div class="kpi-val">{detail.summary.total_communities}</div><div class="kpi-lbl">Syndicate Cells</div></div>
        </div>

        <div class="section-title">TOP RANKED KEY INDIVIDUALS (CENTRALITY ANALYSIS)</div>
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Entity</th>
                    <th>Type</th>
                    <th>Centrality Score</th>
                    <th>PageRank</th>
                    <th>Betweenness</th>
                    <th>Operational Rationale</th>
                </tr>
            </thead>
            <tbody>
    """
    for idx, ki in enumerate(detail.key_individuals[:8]):
        report_html += f"""
                <tr>
                    <td><b>#{idx+1}</b></td>
                    <td><b>{ki.label}</b></td>
                    <td>{ki.type}</td>
                    <td>{ki.centrality_score:.2f}</td>
                    <td>{ki.pagerank:.3f}</td>
                    <td>{ki.betweenness:.3f}</td>
                    <td>{ki.rationale}</td>
                </tr>
        """

    report_html += """
            </tbody>
        </table>

        <div class="section-title">FLAGGED MULTI-SOURCE ANOMALIES & EVIDENCE LINKS</div>
    """

    for a in detail.anomalies:
        refs_str = ", ".join(a.evidence_refs) if a.evidence_refs else "N/A"
        report_html += f"""
        <div class="anomaly-card">
            <b>[{a.severity.upper()}] {a.id}</b>: {a.description}
            <div style="margin-top: 4px; font-size: 12px; color: #7f1d1d;">
                <b>Evidence Anchors:</b> {refs_str}
            </div>
        </div>
        """

    report_html += """
        <div style="margin-top: 40px; border-top: 1px solid #cbd5e1; padding-top: 10px; font-size: 11px; color: #94a3b8; text-align: center;">
            MINISTRY OF HOME AFFAIRS / NCRB — WOMEN SAFETY DIVISION | SYNTHETIC DEMO CASE SIH26189
        </div>
    </body>
    </html>
    """

    return Response(content=report_html, media_type="text/html")
