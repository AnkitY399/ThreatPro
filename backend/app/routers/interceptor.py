"""
ThreatPro - Digital Arrest Interceptor Router
Real-time call interception, transcript processing, and threat alert WebSocket streaming.
"""

import json
import uuid
import asyncio
import random
from typing import List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db
from ..models.schemas import (
    TranscriptRecord,
    ThreatAlert,
    TranscriptCreate,
    TranscriptResponse,
    ThreatAlertResponse,
)
from ..core.audio_stream import stream_manager, AudioChunk
from ..core.classifier import stream_classifier

router = APIRouter(prefix="/api/v1/interceptor", tags=["Interceptor"])


# ============================================================================
# Connection Manager for WebSocket broadcasting
# ============================================================================

class ConnectionManager:
    """Manages WebSocket connections for real-time streaming."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for conn in dead:
            self.active_connections.remove(conn)


manager = ConnectionManager()


# ============================================================================
# REST Endpoints
# ============================================================================

@router.get("/calls/active", response_model=List[dict])
def get_active_calls():
    """List all currently intercepted active calls."""
    return stream_manager.simulator.get_active_calls()


@router.post("/calls/start")
def start_interception(db: Session = Depends(get_db)):
    """Start a new call interception session."""
    call_id = stream_manager.simulator.start_call()
    call_info = stream_manager.simulator.active_calls.get(call_id, {})
    is_scam = call_info.get("is_scam", False)

    return {
        "call_id": call_id,
        "status": "intercepting",
        "is_suspicious": is_scam,
        "message": f"Call {call_id} is now being monitored",
    }


@router.post("/calls/{call_id}/stop")
def stop_interception(call_id: str):
    """Stop an active call interception."""
    success = stream_manager.simulator.end_call(call_id)
    stream_classifier.clear_context(call_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Call {call_id} not found")
    return {"status": "stopped", "call_id": call_id}


@router.get("/calls/{call_id}/summary")
def get_call_summary(call_id: str):
    """Get the complete analysis summary for a processed call."""
    summary = stream_classifier.get_call_summary(call_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Call {call_id} not found")
    return summary


@router.get("/alerts", response_model=List[ThreatAlertResponse])
def get_alerts(
    skip: int = 0,
    limit: int = 50,
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    """Retrieve threat alerts with optional filtering."""
    query = db.query(ThreatAlert)
    if active_only:
        query = query.filter(ThreatAlert.is_active == True)
    query = query.order_by(ThreatAlert.created_at.desc()).offset(skip).limit(limit)
    return query.all()


@router.get("/alerts/{alert_id}", response_model=ThreatAlertResponse)
def get_alert(alert_id: str, db: Session = Depends(get_db)):
    """Get a specific threat alert by ID."""
    alert = db.query(ThreatAlert).filter(ThreatAlert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return alert


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    """Mark a threat alert as resolved."""
    alert = db.query(ThreatAlert).filter(ThreatAlert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    alert.is_active = False
    alert.resolved_at = datetime.now()
    db.commit()
    return {"status": "resolved", "alert_id": alert_id}


@router.post("/transcript", response_model=TranscriptResponse)
def submit_transcript(transcript: TranscriptCreate, db: Session = Depends(get_db)):
    """Submit a single transcript chunk for processing and storage."""
    from ..core.classifier import transcript_classifier

    # Classify the transcript
    result = transcript_classifier.classify(transcript.transcript_text)

    # Store in database
    record = TranscriptRecord(
        call_id=transcript.call_id,
        chunk_index=transcript.chunk_index,
        transcript_text=transcript.transcript_text,
        risk_score=result["risk_score"],
        risk_category=result["risk_category"],
        matched_keywords=result["matched_keywords"],
        pitch_variance=result["pitch_variance"],
        is_spoof=result["is_spoof"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # Generate alert if high risk
    if result["risk_category"] in ("High Risk", "Active Scam"):
        alert_id = f"ALERT_{uuid.uuid4().hex[:10].upper()}"
        alert = ThreatAlert(
            alert_id=alert_id,
            title=f"Digital Arrest Threat Detected - {result['risk_category']}",
            description=f"Risk Score: {result['risk_score']:.1f} | Keywords: {', '.join(m['keyword'] for m in result['matched_keywords'][:5])}",
            severity="Critical" if result["risk_category"] == "Active Scam" else "High",
            source="interceptor",
            risk_score=result["risk_score"],
            transcript_snippet=transcript.transcript_text[:200],
            call_id=transcript.call_id,
            related_entities=[m["keyword"] for m in result["matched_keywords"][:10]],
        )
        db.add(alert)
        db.commit()

    return record


# ============================================================================
# WebSocket Endpoint for Live Streaming
# ============================================================================

@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time interception streaming."""
    await manager.connect(websocket)
    call_id = None

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "ThreatPro Interceptor Stream Connected",
            "timestamp": datetime.now().isoformat(),
        })

        # Receive the start command
        data = await websocket.receive_json()
        if data.get("action") == "start_stream":
            call_id = stream_manager.simulator.start_call()
            await websocket.send_json({
                "type": "stream_started",
                "call_id": call_id,
                "message": f"Intercepting call {call_id}",
            })

            # Stream chunks in real-time
            async for chunk in stream_manager.stream_chunks_generator(call_id):
                # Classify the transcript
                text_preview = chunk.metadata.get("text_preview", "")
                classification = stream_classifier.process_chunk(
                    call_id, text_preview, chunk.metadata.get("pitch_variance", 0.0)
                )

                # Send to client
                await websocket.send_json({
                    "type": "chunk",
                    "call_id": call_id,
                    "chunk_index": chunk.chunk_index,
                    "transcript": text_preview,
                    "pcm_b64": "",  # Omit audio data for streaming efficiency
                    "classification": classification,
                    "timestamp": chunk.timestamp,
                })

                # Generate alert for high-risk chunks
                if classification["risk_category"] in ("High Risk", "Active Scam"):
                    await websocket.send_json({
                        "type": "alert",
                        "alert_id": f"ALERT_{uuid.uuid4().hex[:10].upper()}",
                        "severity": "CRITICAL" if classification["risk_category"] == "Active Scam" else "HIGH",
                        "risk_score": classification["risk_score"],
                        "call_id": call_id,
                        "message": f"Digital Arrest pattern detected! Risk: {classification['risk_score']:.1f}%",
                        "timestamp": datetime.now().isoformat(),
                    })

            # Send stream complete
            summary = stream_classifier.get_call_summary(call_id)
            await websocket.send_json({
                "type": "stream_complete",
                "call_id": call_id,
                "summary": summary,
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass
    finally:
        manager.disconnect(websocket)
        if call_id:
            stream_manager.simulator.end_call(call_id)
            stream_classifier.clear_context(call_id)