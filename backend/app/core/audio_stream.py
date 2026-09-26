"""
ThreatPro - Real-Time Audio Stream Processor
Simulates live phone/VoIP call interception with mock PCM audio chunking.
"""

import asyncio
import random
import time
import uuid
import base64
import struct
import math
from typing import Optional, Callable, Awaitable, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from ..config import settings


# ============================================================================
# DATA TYPES
# ============================================================================

@dataclass
class AudioChunk:
    """Represents a single audio chunk from a live interception stream."""
    chunk_id: str
    call_id: str
    chunk_index: int
    pcm_samples: List[float]  # Simulated PCM-16 samples normalized to [-1, 1]
    sample_rate: int = 16000
    duration_ms: int = 3000
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriptResult:
    """Output from transcript processing with risk metadata."""
    text: str
    confidence: float
    language: str = "hi"
    is_final: bool = True


# ============================================================================
# MOCK CALL SCRIPTS (Synthetic training/inference data)
# ============================================================================

# High-risk scam call scripts for simulation
SCAM_SCRIPTS = [
    # Digital Arrest - CBI Investigation
    "Hello, this is speaking from the CBI Cyber Crime Investigation Unit. We have detected illegal transactions from your Aadhaar linked bank account. A digital arrest warrant has been issued against you under Section 66D of IT Act. You need to immediately transfer all funds to the RBI security escrow account for verification within 2 hours or face immediate arrest.",
    # ED Notice
    "This is the Enforcement Directorate calling. A money laundering case has been registered against your PAN card linked accounts under PMLA 2002. Your assets will be frozen immediately. To avoid attachment, you must pay the penalty amount of Rs 4,85,000 through the RTGS link we will send. Do not discuss with anyone or you will be arrested.",
    # Customs Case
    "Namaste, this is from Mumbai Customs Department. A parcel in your name containing 12 passports and 5 kg of drugs has been seized at the airport. An NCB case is being registered. To avoid legal action, you must pay the customs clearance fee of Rs 2,35,000. Here is your case number: CUS/2026/DRUGS/48201.",
    # Lottery Scam
    "Congratulations! You have won Rs 75,00,000 in the KBC Mega Lottery 2026. To release your winnings, you need to pay the processing fee of Rs 45,000 and GST of Rs 28,000. This is the final call for prize release. Your winning ticket number is KBC/25/LAKH/007.",
    # Fake Investment
    "Sir, this is regarding the SEBI approved high-return investment scheme. We have already processed Rs 12,50,000 profit in your trading account. To withdraw, you need to pay the TDS amount of Rs 2,15,000. This is a limited period government scheme.",
    # Friend/Family Emergency
    "Beta, I am in trouble. I lost my phone and wallet. Please send Rs 50,000 urgently to this UPI ID. I will explain everything later. Don't tell anyone in the family.",
    # Job Offer Scam
    "We have selected your profile for the work-from-home data entry position with a salary of Rs 85,000 per month. You need to pay Rs 5,000 as registration fee and Rs 12,000 for the laptop setup cost. This is refundable after probation period.",
    # Tech Support Scam
    "This is Microsoft Windows Security Center. Your computer has been infected with 15 viruses sending data to Chinese servers. Your internet banking is compromised. We need remote access to your computer immediately to install security patches.",
]

# Normal conversation scripts
NORMAL_SCRIPTS = [
    "Hello, I need to check my bank balance for the savings account ending 4820. Can you please help me with the latest transaction history?",
    "Yes, I would like to renew my insurance policy number 7Y8K9L for another year. What documents do I need to submit?",
    "My electricity bill for Mumbai office has not updated yet. The reference number is MH/ELEC/2026/88421. Can you check?",
    "I want to transfer Rs 2,500 to my daughter's college account for the semester fee. The account number is 9988776655 at SBI.",
    "Please help me with the new passbook update for my recurring deposit account number RD/4477/2024.",
    "Thank you for the assistance yesterday. The UPI transaction went through successfully. I received the payment confirmation.",
    "I need to book a train ticket from Delhi to Lucknow for the 15th of next month. Three tickets in AC 3-tier please.",
    "Can you please schedule a meeting with the branch manager for Friday at 3 PM regarding the home loan application?",
]


def generate_synthetic_pcm(duration_ms: int = 3000, sample_rate: int = 16000) -> List[float]:
    """
    Generate synthetic PCM audio samples simulating speech patterns.
    Returns normalized float samples in [-1, 1] range.
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    samples = []

    t = 0.0
    dt = 1.0 / sample_rate

    # Speech-like multi-tone synthesis with formant-like frequencies
    base_freq = random.uniform(120, 250)  # Fundamental frequency (Hz)
    formants = [
        random.uniform(300, 800),   # F1
        random.uniform(900, 2200),  # F2
        random.uniform(2400, 3400), # F3
    ]

    for i in range(num_samples):
        # Voiced signal with multiple formants
        sample = 0.0
        sample += 0.6 * math.sin(2 * math.pi * base_freq * t)
        sample += 0.3 * math.sin(2 * math.pi * formants[0] * t)
        sample += 0.15 * math.sin(2 * math.pi * formants[1] * t)
        sample += 0.05 * math.sin(2 * math.pi * formants[2] * t)

        # Add noise floor
        sample += random.gauss(0, 0.02)

        # Amplitude modulation to simulate syllable rhythm
        amplitude = 0.5 + 0.4 * math.sin(2 * math.pi * 4 * t)
        sample *= amplitude

        # Clamp and normalize
        sample = max(-1.0, min(1.0, sample))
        samples.append(sample)
        t += dt

    return samples


def encode_pcm_to_base64(pcm_samples: List[float]) -> str:
    """Convert PCM float samples to base64-encoded 16-bit PCM."""
    pcm_16 = [int(s * 32767) for s in pcm_samples]
    packed = struct.pack(f"<{len(pcm_16)}h", *pcm_16)
    return base64.b64encode(packed).decode("utf-8")


def decode_base64_to_pcm(b64_string: str) -> List[float]:
    """Convert base64-encoded 16-bit PCM back to float samples."""
    packed = base64.b64decode(b64_string)
    pcm_16 = struct.unpack(f"<{len(packed)//2}h", packed)
    return [s / 32767.0 for s in pcm_16]


# ============================================================================
# STREAM SIMULATOR
# ============================================================================

class AudioStreamSimulator:
    """
    Simulates a live audio interception stream.
    Generates synthetic call data with configurable scam probability.
    """

    def __init__(self, scam_probability: float = 0.35):
        self.scam_probability = scam_probability
        self.active_calls: Dict[str, Dict[str, Any]] = {}
        self._call_id_counter = 0

    def start_call(self) -> str:
        """Start a new simulated call interception session."""
        call_id = f"CALL_{uuid.uuid4().hex[:12].upper()}"
        is_scam = random.random() < self.scam_probability

        if is_scam:
            script = random.choice(SCAM_SCRIPTS)
        else:
            script = random.choice(NORMAL_SCRIPTS)

        # Split script into ~3 second chunks
        words = script.split()
        chunk_size = max(8, len(words) // (len(script) // 100 + 3))
        chunks_text = []
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i:i + chunk_size])
            if chunk_text:
                chunks_text.append(chunk_text)

        self.active_calls[call_id] = {
            "call_id": call_id,
            "is_scam": is_scam,
            "chunks": chunks_text,
            "total_chunks": len(chunks_text),
            "current_chunk": 0,
            "started_at": time.time(),
            "pitch_variance": random.uniform(0.3, 0.9) if is_scam else random.uniform(0.05, 0.2),
            "speech_rate": random.uniform(3.5, 5.5) if is_scam else random.uniform(2.0, 3.5),
        }

        return call_id

    async def get_next_chunk(self, call_id: str) -> Optional[AudioChunk]:
        """Get the next audio chunk for an active call."""
        call = self.active_calls.get(call_id)
        if not call:
            return None

        if call["current_chunk"] >= call["total_chunks"]:
            # Call ended
            del self.active_calls[call_id]
            return None

        idx = call["current_chunk"]
        text = call["chunks"][idx]
        call["current_chunk"] += 1

        # Generate synthetic PCM with pitch variance
        is_scam = call["is_scam"]
        pv = call["pitch_variance"]

        # Add extra artifacts for scam calls
        pcm = generate_synthetic_pcm(settings.AUDIO_CHUNK_MS)
        if is_scam:
            # Add stress artifacts: higher frequency modulation + tremors
            for i in range(len(pcm)):
                stress_mod = 1.0 + 0.3 * math.sin(2 * math.pi * 8 * i / len(pcm))
                pcm[i] *= stress_mod
                pcm[i] += random.gauss(0, 0.01) * (1 + pv * 2)

        chunk = AudioChunk(
            chunk_id=f"CHUNK_{uuid.uuid4().hex[:8].upper()}",
            call_id=call_id,
            chunk_index=idx,
            pcm_samples=pcm,
            duration_ms=settings.AUDIO_CHUNK_MS,
            metadata={
                "is_scam": is_scam,
                "pitch_variance": pv,
                "speech_rate": call["speech_rate"],
                "text_preview": text[:80],
            }
        )

        return chunk

    def end_call(self, call_id: str) -> bool:
        """Terminate an active call interception."""
        return bool(self.active_calls.pop(call_id, None))

    def get_active_calls(self) -> List[Dict[str, Any]]:
        """List all currently active intercepted calls."""
        return [
            {
                "call_id": cid,
                "progress": f"{c['current_chunk']}/{c['total_chunks']}",
                "is_scam": c["is_scam"],
                "active_seconds": int(time.time() - c["started_at"]),
            }
            for cid, c in self.active_calls.items()
        ]


# ============================================================================
# STREAM MANAGER (Singleton-backed)
# ============================================================================

class StreamManager:
    """
    Manages multiple concurrent interception streams.
    Provides async generator interface for real-time frontend streaming.
    """

    def __init__(self):
        self.simulator = AudioStreamSimulator(scam_probability=0.35)
        self._listeners: Dict[str, List[Callable[[AudioChunk], Awaitable[None]]]] = {}

    def register_listener(self, call_id: str, callback: Callable[[AudioChunk], Awaitable[None]]):
        """Register a callback for real-time chunk streaming."""
        if call_id not in self._listeners:
            self._listeners[call_id] = []
        self._listeners[call_id].append(callback)

    def unregister_listener(self, call_id: str, callback: Callable[[AudioChunk], Awaitable[None]]):
        """Remove a registered callback."""
        if call_id in self._listeners:
            self._listeners[call_id] = [cb for cb in self._listeners[call_id] if cb != callback]

    async def process_call_stream(self, call_id: str) -> List[AudioChunk]:
        """
        Process an entire call stream, returning all chunks.
        Calls registered listeners for each chunk in real-time.
        """
        chunks = []
        while True:
            chunk = await self.simulator.get_next_chunk(call_id)
            if chunk is None:
                break

            chunks.append(chunk)

            # Notify listeners
            listeners = self._listeners.get(call_id, [])
            for listener in listeners:
                try:
                    await listener(chunk)
                except Exception:
                    pass

            # Simulate real-time delay
            await asyncio.sleep(0.3)

        return chunks

    async def stream_chunks_generator(self, call_id: str):
        """
        Async generator yielding AudioChunks for WebSocket streaming.
        """
        while True:
            chunk = await self.simulator.get_next_chunk(call_id)
            if chunk is None:
                break
            yield chunk
            await asyncio.sleep(0.3)


# Global stream manager instance
stream_manager = StreamManager()