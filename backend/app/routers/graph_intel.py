"""
ThreatPro - Fraud Graph Intelligence Router
Graph analytics, mule network detection, and legal dossier generation.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..models.schemas import (
    TransactionRecord,
    TransactionCreate,
    TransactionResponse,
    GraphData,
    FraudMuleNetwork,
    LegalDossierResponse,
)
from ..core.graph_builder import (
    fraud_graph,
    dossier_generator,
    GraphNode,
    GraphEdge,
)

router = APIRouter(prefix="/api/v1/graph", tags=["Graph Intelligence"])


@router.get("/snapshot", response_model=GraphData)
def get_graph_snapshot(max_nodes: int = Query(100, ge=10, le=500)):
    """Get the fraud intelligence graph snapshot for visualization."""
    snapshot = fraud_graph.get_graph_snapshot(max_nodes=max_nodes)
    return snapshot


@router.get("/nodes/count")
def get_node_counts():
    """Get count of each node type in the graph."""
    counts = {}
    for node in fraud_graph.nodes.values():
        ntype = node.node_type
        counts[ntype] = counts.get(ntype, 0) + 1
    return {
        "total_nodes": len(fraud_graph.nodes),
        "total_edges": len(fraud_graph.edges),
        "node_type_counts": counts,
    }


@router.get("/components")
def get_connected_components():
    """Find all weakly connected components in the fraud graph."""
    components = fraud_graph.find_connected_components()
    return {
        "total_components": len(components),
        "components": [
            {"id": i, "size": len(comp), "nodes": list(comp)}
            for i, comp in enumerate(components)
        ],
    }


@router.post("/transactions", response_model=TransactionResponse)
def add_transaction(tx: TransactionCreate, db: Session = Depends(get_db)):
    """
    Add a transaction record and update the fraud graph.
    """
    # Store in database
    record = TransactionRecord(
        transaction_id=tx.transaction_id,
        source_account=tx.source_account,
        target_account=tx.target_account,
        amount=tx.amount,
        transaction_type=tx.transaction_type,
        source_bank=tx.source_bank,
        target_bank=tx.target_bank,
        source_phone=tx.source_phone,
        target_phone=tx.target_phone,
        source_ip=tx.source_ip,
        device_id=tx.device_id,
        location_lat=tx.location_lat,
        location_lon=tx.location_lon,
        location_name=tx.location_name,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Build graph nodes
    fraud_graph.add_node(GraphNode(
        node_id=f"ACC_{tx.source_account}",
        label=tx.source_account,
        node_type="Account",
        properties={"bank": tx.source_bank, "phone": tx.source_phone},
    ))
    fraud_graph.add_node(GraphNode(
        node_id=f"ACC_{tx.target_account}",
        label=tx.target_account,
        node_type="Account",
        properties={"bank": tx.target_bank, "phone": tx.target_phone},
    ))
    if tx.source_phone:
        fraud_graph.add_node(GraphNode(
            node_id=f"PH_{tx.source_phone}",
            label=tx.source_phone,
            node_type="Phone",
        ))
        fraud_graph.add_edge(GraphEdge(
            source=f"ACC_{tx.source_account}",
            target=f"PH_{tx.source_phone}",
            relationship="HAS_PHONE",
        ))
    if tx.device_id:
        fraud_graph.add_node(GraphNode(
            node_id=f"DEV_{tx.device_id}",
            label=tx.device_id,
            node_type="Device",
        ))
        fraud_graph.add_edge(GraphEdge(
            source=f"ACC_{tx.source_account}",
            target=f"DEV_{tx.device_id}",
            relationship="USES_DEVICE",
        ))
    if tx.source_ip:
        fraud_graph.add_node(GraphNode(
            node_id=f"IP_{tx.source_ip}",
            label=tx.source_ip,
            node_type="IP_Address",
        ))
        fraud_graph.add_edge(GraphEdge(
            source=f"ACC_{tx.source_account}",
            target=f"IP_{tx.source_ip}",
            relationship="USES_IP",
        ))

    # Add transaction edge
    fraud_graph.add_edge(GraphEdge(
        source=f"ACC_{tx.source_account}",
        target=f"ACC_{tx.target_account}",
        relationship="TRANSFERRED_TO",
        weight=min(1.0, tx.amount / 100000),
        properties={
            "amount": tx.amount,
            "type": tx.transaction_type,
            "tx_id": tx.transaction_id,
        },
    ))

    return record


@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(
    skip: int = 0,
    limit: int = 100,
    suspicious_only: bool = False,
    db: Session = Depends(get_db),
):
    """Retrieve transaction records with optional filtering."""
    query = db.query(TransactionRecord)
    if suspicious_only:
        query = query.filter(TransactionRecord.is_suspicious == True)
    query = query.order_by(TransactionRecord.timestamp.desc()).offset(skip).limit(limit)
    return query.all()


@router.get("/mule-networks", response_model=List[FraudMuleNetwork])
def detect_mule_networks(
    min_inflow: float = Query(50000.0, ge=1000),
    min_sources: int = Query(3, ge=2),
    db: Session = Depends(get_db),
):
    """
    Detect money mule networks using WCC-based flow analysis.
    """
    transactions = [
        {
            "target_account": tx.target_account,
            "source_account": tx.source_account,
            "amount": tx.amount,
            "device_id": tx.device_id,
            "source_ip": tx.source_ip,
        }
        for tx in db.query(TransactionRecord).all()
    ]

    networks = fraud_graph.detect_mule_networks(
        transactions=transactions,
        min_inflow=min_inflow,
        min_source_accounts=min_sources,
    )
    return networks


@router.post("/dossier/generate", response_model=LegalDossierResponse)
def generate_legal_dossier(
    case_summary: str = "Digital Arrest / Financial Fraud Investigation Case",
    db: Session = Depends(get_db),
):
    """
    Generate a Section 65B-compliant legal dossier with SHA-256 evidence hashing.
    """
    graph_snapshot = fraud_graph.get_graph_snapshot(max_nodes=200)

    transactions = [
        {
            "transaction_id": tx.transaction_id or str(tx.id),
            "source_account": tx.source_account,
            "target_account": tx.target_account,
            "amount": tx.amount,
            "transaction_type": tx.transaction_type,
            "is_suspicious": tx.is_suspicious,
            "fraud_score": tx.fraud_score,
            "timestamp": tx.timestamp.isoformat() if tx.timestamp else "",
        }
        for tx in db.query(TransactionRecord).all()
    ]

    from ..models.schemas import ThreatAlert
    alerts = [
        {
            "alert_id": alert.alert_id or str(alert.id),
            "title": alert.title,
            "severity": alert.severity,
            "risk_score": alert.risk_score,
            "created_at": alert.created_at.isoformat() if alert.created_at else "",
            "description": alert.description,
        }
        for alert in db.query(ThreatAlert).all()
    ]

    dossier = dossier_generator.generate(
        case_summary=case_summary,
        graph_snapshot=graph_snapshot,
        transactions=transactions,
        alerts=alerts,
    )

    return dossier


@router.get("/dossier/{dossier_id}/download")
def download_dossier(dossier_id: str):
    """Download a previously generated legal dossier."""
    return {
        "dossier_id": dossier_id,
        "message": "Dossier download endpoint",
        "note": "In production, this returns a signed PDF document",
    }


@router.get("/stats")
def get_graph_stats(db: Session = Depends(get_db)):
    """Get aggregate intelligence statistics."""
    total_tx = db.query(TransactionRecord).count()
    suspicious_tx = db.query(TransactionRecord).filter(TransactionRecord.is_suspicious == True).count()
    total_alerts = 0
    from ..models.schemas import ThreatAlert
    total_alerts = db.query(ThreatAlert).count()
    active_alerts = db.query(ThreatAlert).filter(ThreatAlert.is_active == True).count()

    return {
        "total_transactions": total_tx,
        "suspicious_transactions": suspicious_tx,
        "suspicious_rate": round(suspicious_tx / max(total_tx, 1) * 100, 2),
        "total_alerts": total_alerts,
        "active_alerts": active_alerts,
        "graph_nodes": len(fraud_graph.nodes),
        "graph_edges": len(fraud_graph.edges),
    }