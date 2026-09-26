"""
ThreatPro - Counterfeit Currency Sentinel Router
Forensic analysis endpoints for currency note verification.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..models.schemas import CurrencyScanResult, CurrencyScanRequest, CurrencyScanResponse
from ..core.cv_model import currency_forensics

router = APIRouter(prefix="/api/v1/sentinel", tags=["Sentinel"])


@router.post("/scan", response_model=CurrencyScanResponse)
async def scan_currency(
    request: CurrencyScanRequest,
    db: Session = Depends(get_db),
):
    """
    Perform full forensic analysis on a currency note image.
    Accepts base64-encoded image with optional denomination hint.
    """
    if not request.image_b64 or len(request.image_b64) < 100:
        raise HTTPException(status_code=400, detail="Invalid image data - too short")

    # Run forensic pipeline
    result = currency_forensics.analyze(
        image_b64=request.image_b64,
        denomination_hint=request.denomination_hint,
    )

    # Store in database
    scan_record = CurrencyScanResult(
        scan_id=result["scan_id"],
        denomination=result["denomination"],
        is_authentic=result["is_authentic"],
        confidence_score=result["confidence_score"],
        serial_number=result["serial_number"],
        serial_valid=result["serial_valid"],
        security_thread_detected=result["security_thread_detected"],
        security_thread_score=result["security_thread_score"],
        uv_fibers_detected=result["uv_fibers_detected"],
        uv_fiber_count=result["uv_fiber_count"],
        watermark_detected=result["watermark_detected"],
        micro_printing_valid=result["micro_printing_valid"],
        anomaly_details=result["anomaly_details"],
        visual_overlay_b64=result["visual_overlay_b64"],
    )
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)

    return scan_record


@router.post("/scan/upload")
async def scan_currency_upload(
    file: UploadFile = File(...),
    denomination_hint: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Upload a currency note image file for forensic analysis.
    """
    # Read and encode the uploaded file
    contents = await file.read()
    import base64
    image_b64 = base64.b64encode(contents).decode("utf-8")

    if len(image_b64) < 100:
        raise HTTPException(status_code=400, detail="Uploaded image is too small or empty")

    # Run forensic pipeline
    result = currency_forensics.analyze(
        image_b64=image_b64,
        denomination_hint=denomination_hint,
    )

    # Store in database
    scan_record = CurrencyScanResult(
        scan_id=result["scan_id"],
        denomination=result["denomination"],
        is_authentic=result["is_authentic"],
        confidence_score=result["confidence_score"],
        serial_number=result["serial_number"],
        serial_valid=result["serial_valid"],
        security_thread_detected=result["security_thread_detected"],
        security_thread_score=result["security_thread_score"],
        uv_fibers_detected=result["uv_fibers_detected"],
        uv_fiber_count=result["uv_fiber_count"],
        watermark_detected=result["watermark_detected"],
        micro_printing_valid=result["micro_printing_valid"],
        anomaly_details=result["anomaly_details"],
        visual_overlay_b64=result["visual_overlay_b64"],
    )
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)

    return scan_record


@router.get("/scans", response_model=list)
def get_recent_scans(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Retrieve recent currency scan results."""
    scans = (
        db.query(CurrencyScanResult)
        .order_by(CurrencyScanResult.scanned_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return scans


@router.get("/scans/{scan_id}", response_model=CurrencyScanResponse)
def get_scan(scan_id: str, db: Session = Depends(get_db)):
    """Get a specific currency scan result by ID."""
    scan = db.query(CurrencyScanResult).filter(CurrencyScanResult.scan_id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan {scan_id} not found")
    return scan


@router.get("/denominations")
def list_denominations():
    """List supported currency denominations."""
    from ..core.cv_model import CURRENCY_SPECS
    return {
        "denominations": list(CURRENCY_SPECS.keys()),
        "count": len(CURRENCY_SPECS),
    }


@router.get("/stats")
def get_sentinel_stats(db: Session = Depends(get_db)):
    """Get aggregate statistics from currency scanning."""
    scans = db.query(CurrencyScanResult).all()
    total = len(scans)
    authentic = sum(1 for s in scans if s.is_authentic)
    counterfeit = total - authentic
    avg_confidence = sum(s.confidence_score for s in scans) / max(total, 1)

    # Denomination breakdown
    denom_counts = {}
    for s in scans:
        denom_counts[s.denomination] = denom_counts.get(s.denomination, 0) + 1

    return {
        "total_scans": total,
        "authentic": authentic,
        "counterfeit": counterfeit,
        "counterfeit_rate": round(counterfeit / max(total, 1) * 100, 2),
        "avg_confidence": round(avg_confidence, 2),
        "denomination_breakdown": denom_counts,
    }