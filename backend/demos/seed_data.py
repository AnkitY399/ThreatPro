"""
ThreatPro - Comprehensive Seed Data Generator
Generates 200+ transactions, 30 spatial data points, and mock currency arrays.
"""

import uuid
import random
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.database import SessionLocal
from app.models.schemas import (
    TranscriptRecord,
    ThreatAlert,
    CurrencyScanResult,
    TransactionRecord,
    GeoLocation,
    PatrolRoute,
)
from app.core.audio_stream import SCAM_SCRIPTS, NORMAL_SCRIPTS
from app.core.graph_builder import (
    fraud_graph,
    geospatial_engine,
    GraphNode,
    GraphEdge,
)


# ============================================================================
# HELPER DATA
# ============================================================================

BANKS = [
    "State Bank of India", "HDFC Bank", "ICICI Bank", "Axis Bank",
    "Kotak Mahindra", "Yes Bank", "Punjab National Bank", "Bank of Baroda",
    "Canara Bank", "Union Bank of India", "IndusInd Bank", "IDBI Bank",
]

CITIES = [
    "Mumbai", "New Delhi", "Bengaluru", "Hyderabad", "Chennai",
    "Kolkata", "Pune", "Ahmedabad", "Jaipur", "Lucknow",
    "Surat", "Chandigarh", "Bhopal", "Patna", "Nagpur",
]

ACCOUNT_PREFIXES = [
    "SBIN", "HDFC", "ICIC", "AXIS", "KKBK", "YESB", "PNB",
    "BARB", "CNRB", "UBIN", "INDB", "IDIB",
]

PHONE_PREFIXES = [
    "98765", "99887", "77665", "88990", "76543", "99880",
    "98700", "77654", "88998", "76500", "99881", "98712",
]


def random_account() -> str:
    """Generate a realistic bank account number."""
    prefix = random.choice(ACCOUNT_PREFIXES)
    digits = "".join(random.choices("0123456789", k=12))
    return f"{prefix}{digits}"


def random_phone() -> str:
    """Generate a realistic Indian phone number."""
    prefix = random.choice(PHONE_PREFIXES)
    suffix = "".join(random.choices("0123456789", k=5))
    return f"{prefix}{suffix}"


def random_ip() -> str:
    """Generate a random IP address."""
    return ".".join(str(random.randint(1, 255)) for _ in range(4))


def random_device_id() -> str:
    """Generate a random device identifier."""
    return f"DEVICE_{uuid.uuid4().hex[:10].upper()}"


# ============================================================================
# SEED FUNCTIONS
# ============================================================================

def seed_transactions() -> List[TransactionRecord]:
    """
    Generate 200+ financial transaction records with
    embedded money laundering patterns.
    """
    transactions = []
    db = SessionLocal()
    now = datetime.now()

    # Define mule sink accounts (receiving large sums from many sources)
    mule_sinks = [random_account() for _ in range(5)]

    for i in range(220):
        is_mule_pattern = i < 50  # First 50 are mule transactions

        if is_mule_pattern:
            # Mule pattern: many small deposits into few sink accounts
            sink = random.choice(mule_sinks)
            source = random_account()
            amount = round(random.uniform(1000, 15000), 2)
            tx_type = random.choice(["NEFT", "IMPS", "UPI", "CASH_DEPOSIT"])
            is_suspicious = True
            fraud_score = round(random.uniform(60, 95), 2)
        else:
            # Normal pattern: diverse transaction flows
            if random.random() < 0.15:
                # Some normal-looking patterns with suspicious characteristics
                sink = random_account()
                source = random_account()
                amount = round(random.uniform(2000, 50000), 2)
                tx_type = random.choice(["NEFT", "RTGS"])
                is_suspicious = random.random() < 0.20
                fraud_score = round(random.uniform(20, 55), 2) if is_suspicious else round(random.uniform(0, 15), 2)
            else:
                sink = random_account()
                source = random_account()
                amount = round(random.uniform(100, 50000), 2)
                tx_type = random.choice(["NEFT", "RTGS", "IMPS", "UPI"])
                is_suspicious = False
                fraud_score = round(random.uniform(0, 10), 2)

        # Build mule network connectivity: share devices/IPs among sink accounts
        if is_mule_pattern and random.random() < 0.4:
            shared_device = random_device_id()
            shared_ip = random_ip()
        else:
            shared_device = random_device_id()
            shared_ip = random_ip()

        city = random.choice(CITIES)
        record = TransactionRecord(
            transaction_id=f"TXN_{now.strftime('%Y%m%d')}_{i:04d}_{uuid.uuid4().hex[:6].upper()}",
            source_account=source,
            target_account=sink,
            amount=amount,
            transaction_type=tx_type,
            source_bank=random.choice(BANKS),
            target_bank=random.choice(BANKS),
            source_phone=random_phone(),
            target_phone=random_phone(),
            source_ip=shared_ip,
            device_id=shared_device,
            location_lat=round(random.uniform(8.0, 37.0), 6),
            location_lon=round(random.uniform(68.0, 97.0), 6),
            location_name=city,
            is_suspicious=is_suspicious,
            fraud_score=fraud_score,
            timestamp=now - timedelta(
                days=random.randint(0, 60),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            ),
        )
        db.add(record)

        # Build graph nodes
        fraud_graph.add_node(GraphNode(
            node_id=f"ACC_{source}",
            label=source[-8:],
            node_type="Account",
            properties={"bank": record.source_bank},
        ))
        fraud_graph.add_node(GraphNode(
            node_id=f"ACC_{sink}",
            label=sink[-8:],
            node_type="Account",
            properties={"bank": record.target_bank},
        ))
        fraud_graph.add_node(GraphNode(
            node_id=f"PH_{record.source_phone}",
            label=record.source_phone[-6:],
            node_type="Phone",
        ))
        fraud_graph.add_node(GraphNode(
            node_id=f"DEV_{shared_device}",
            label=shared_device[-8:],
            node_type="Device",
        ))
        fraud_graph.add_node(GraphNode(
            node_id=f"IP_{shared_ip}",
            label=shared_ip,
            node_type="IP_Address",
        ))
        fraud_graph.add_node(GraphNode(
            node_id=f"LOC_{city}",
            label=city,
            node_type="Location",
            properties={"city": city},
        ))

        # Add edges
        fraud_graph.add_edge(GraphEdge(
            source=f"ACC_{source}", target=f"ACC_{sink}",
            relationship="TRANSFERRED_TO",
            weight=min(1.0, amount / 100000),
            properties={"amount": amount, "type": tx_type},
        ))
        fraud_graph.add_edge(GraphEdge(
            source=f"ACC_{source}", target=f"PH_{record.source_phone}",
            relationship="HAS_PHONE",
        ))
        fraud_graph.add_edge(GraphEdge(
            source=f"ACC_{source}", target=f"DEV_{shared_device}",
            relationship="USES_DEVICE",
        ))
        fraud_graph.add_edge(GraphEdge(
            source=f"ACC_{source}", target=f"IP_{shared_ip}",
            relationship="USES_IP",
        ))
        fraud_graph.add_edge(GraphEdge(
            source=f"ACC_{source}", target=f"LOC_{city}",
            relationship="LOCATED_IN",
        ))

        transactions.append(record)

    db.commit()
    db.close()
    return transactions


def seed_alerts() -> List[ThreatAlert]:
    """
    Generate pre-recorded threat alerts simulating past detection events.
    """
    db = SessionLocal()
    alerts = []
    now = datetime.now()

    alert_templates = [
        ("Digital Arrest Scam Detected - CBI Impersonation", "High"),
        ("Money Laundering Threat - PMLA Section Violation", "Critical"),
        ("Fake ED Notice - Enforcement Directorate Impersonation", "High"),
        ("Customs Department Scam - Parcel Seizure Fraud", "Medium"),
        ("Lottery Fraud - KBC Prize Scam Detected", "Medium"),
        ("Fake Investment Scheme - SEBI Impersonation", "High"),
        ("Tech Support Scam - Remote Access Requested", "Medium"),
        ("Family Emergency Scam - Urgent Money Request", "High"),
        ("Job Offer Fraud - Fake Registration Fee", "Low"),
        ("Aadhaar Linked Crime Alert - Identity Theft Risk", "Critical"),
    ]

    for i, (title, severity) in enumerate(alert_templates):
        sev_mult = {"Low": 20, "Medium": 50, "High": 75, "Critical": 95}[severity]
        alert = ThreatAlert(
            alert_id=f"ALERT_SEED_{i:04d}",
            title=title,
            description=f"Automated detection of {title.lower()} pattern in intercepted communication. Risk assessment indicates {severity.lower()} severity threat.",
            severity=severity,
            source="interceptor",
            risk_score=sev_mult + random.uniform(-10, 10),
            transcript_snippet=random.choice(SCAM_SCRIPTS)[:200],
            call_id=f"CALL_SEED_{uuid.uuid4().hex[:8].upper()}",
            related_entities=[random_account(), random_phone(), random_ip()],
            is_active=random.random() < 0.6,
            created_at=now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23)),
        )
        db.add(alert)
        alerts.append(alert)

    db.commit()
    db.close()
    return alerts


def seed_transcripts() -> List[TranscriptRecord]:
    """
    Seed historical transcript records for demo visualization.
    """
    db = SessionLocal()
    transcripts = []
    now = datetime.now()

    # Mix of scam and normal transcripts
    all_scripts = SCAM_SCRIPTS + NORMAL_SCRIPTS
    for i in range(30):
        script = random.choice(all_scripts)
        is_scam = script in SCAM_SCRIPTS
        pitch_var = random.uniform(0.3, 0.8) if is_scam else random.uniform(0.05, 0.15)

        from app.core.classifier import transcript_classifier
        result = transcript_classifier.classify(script, pitch_var)

        record = TranscriptRecord(
            call_id=f"CALL_SEED_{uuid.uuid4().hex[:8].upper()}",
            chunk_index=i % 5,
            transcript_text=script,
            risk_score=result["risk_score"],
            risk_category=result["risk_category"],
            matched_keywords=result["matched_keywords"],
            pitch_variance=pitch_var,
            is_spoof=result["is_spoof"],
            processed=True,
            timestamp=now - timedelta(days=random.randint(0, 15), minutes=random.randint(0, 59)),
        )
        db.add(record)
        transcripts.append(record)

    db.commit()
    db.close()
    return transcripts


def seed_currency_scans() -> List[CurrencyScanResult]:
    """
    Generate mock currency forensic scan results.
    """
    db = SessionLocal()
    scans = []

    denominations = ["₹10", "₹20", "₹50", "₹100", "₹200", "₹500", "₹2000"]

    for i in range(20):
        denom = random.choice(denominations)
        is_authentic = random.random() < 0.6  # 60% authentic

        # Build mock base64 overlay
        overlay_data = {
            "scan_id": f"FOR_SEED_{i:04d}",
            "denomination": denom,
            "authentic": is_authentic,
            "checks_passed": random.randint(2, 5),
        }
        import json, base64
        overlay_b64 = base64.b64encode(json.dumps(overlay_data).encode()).decode()

        scan = CurrencyScanResult(
            scan_id=f"FOR_SEED_{i:04d}",
            denomination=denom,
            is_authentic=is_authentic,
            confidence_score=round(random.uniform(45, 98), 2) if is_authentic else round(random.uniform(10, 45), 2),
            serial_number=f"{random.choice(['AB','AC','AD','AE','AF'])}{''.join(random.choices('0123456789', k=8))}",
            serial_valid=is_authentic or random.random() < 0.3,
            security_thread_detected=is_authentic or random.random() < 0.4,
            security_thread_score=round(random.uniform(40, 98), 2),
            uv_fibers_detected=is_authentic or random.random() < 0.3,
            uv_fiber_count=random.randint(5, 45),
            watermark_detected=is_authentic or random.random() < 0.5,
            micro_printing_valid=is_authentic or random.random() < 0.3,
            anomaly_details={"seed_anomaly": "Synthetic test data"} if not is_authentic else {},
            visual_overlay_b64=overlay_b64,
        )
        db.add(scan)
        scans.append(scan)

    db.commit()
    db.close()
    return scans


def seed_geolocations() -> List[GeoLocation]:
    """
    Seed geospatial locations for Indian urban centers.
    """
    db = SessionLocal()
    locations = []

    geospatial_engine.seed_locations(count=30)

    for loc in geospatial_engine.locations:
        record = GeoLocation(
            location_id=loc["location_id"],
            latitude=loc["latitude"],
            longitude=loc["longitude"],
            location_name=loc["location_name"],
            city=loc["city"],
            state=loc["state"],
            incident_count=loc["incident_count"],
            risk_level=loc["risk_level"],
            cluster_id=loc.get("cluster_id"),
        )
        db.add(record)
        locations.append(record)

    db.commit()
    db.close()

    # Run initial clustering
    geospatial_engine.run_dbscan()

    return locations


# ============================================================================
# MASTER SEED FUNCTION
# ============================================================================

def seed_all():
    """
    Master function to seed all demo data.
    Called during application startup.
    """
    print("[SEED] Starting comprehensive data seeding...")

    print("[SEED] Seeding 200+ transaction records with mule patterns...")
    seed_transactions()

    print("[SEED] Seeding threat alerts...")
    seed_alerts()

    print("[SEED] Seeding transcript records...")
    seed_transcripts()

    print("[SEED] Seeding currency scan results...")
    seed_currency_scans()

    print("[SEED] Seeding geospatial locations...")
    seed_geolocations()

    print(f"[SEED] Graph built: {len(fraud_graph.nodes)} nodes, {len(fraud_graph.edges)} edges")
    print("[SEED] Seeding complete! All demo data ready.")


if __name__ == "__main__":
    seed_all()