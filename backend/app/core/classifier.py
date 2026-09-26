"""
ThreatPro - NLP Threat Classifier Engine
Multi-stage classifier for detecting digital arrest scams, financial fraud,
and social engineering attacks from transcribed speech.
"""

import re
import math
import random
import uuid
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime

from ..config import settings


# ============================================================================
# SCAM KEYWORD DATABASE
# ============================================================================

# High-severity keywords (direct scam indicators)
HIGH_RISK_KEYWORDS = {
    # Digital Arrest
    r"\bdigital\s*arrest\b": 95,
    r"\bcyber\s*crime\b": 80,
    r"\bcbi\s*(investigation|notice|case)\b": 90,
    r"\benforcement\s*directorate\b": 88,
    r"\bed\s*notice\b": 85,
    r"\bmla\s*2002\b": 82,
    r"\bPMLA\b": 82,
    r"\barrest\s*warrant\b": 92,
    r"\bimmediate\s*arrest\b": 88,
    r"\bfreeze\s*(account|asset|fund)\b": 85,
    r"\battachment\s*order\b": 80,
    r"\bit\s*act\b": 60,
    r"\bsection\s*66D\b": 85,
    r"\bseized\b": 75,
    r"\bncb\s*case\b": 80,

    # Customs & Drugs
    r"\bcustoms\s*department\b": 75,
    r"\bdrugs?\s*(seized|packet|parcel)\b": 85,
    r"\bpassport\s*(seized|cancel)\b": 70,
    r"\bcustoms\s*clearance\s*fee\b": 88,

    # Financial Fraud
    r"\bmoney\s*laundering\b": 85,
    r"\bAadhaar\s*linked\s*crime\b": 80,
    r"\bPAN\s*card\s*linked\b": 70,
    r"\bescrow\s*account\b": 78,
    r"\bsecurity\s*escrow\b": 85,
    r"\bprocessing\s*fee\b": 75,
    r"\bregistration\s*fee\b": 65,
    r"\btds\s*amount\b": 70,
    r"\bpenalty\s*amount\b": 75,
    r"\bwithin\s*\d+\s*hours?\b": 65,
    r"\btransfer\s*all\s*funds\b": 88,
    r"\bimmediately\s*transfer\b": 85,
}

# Medium-severity keywords (suspicious patterns)
MEDIUM_RISK_KEYWORDS = {
    r"\blottery\b": 55,
    r"\bprize\s*money\b": 60,
    r"\bwinning\b": 45,
    r"\bKBC\b": 50,
    r"\bgift\s*voucher\b": 55,
    r"\bclaim\s*(prize|reward|amount)\b": 60,
    r"\blimited\s*period\b": 45,
    r"\burgent\b": 50,
    r"\bdo\s*not\s*tell\s*anyone\b": 75,
    r"\bdon't\s*tell\b": 65,
    r"\bkeep\s*it\s*secret\b": 70,
    r"\bconfidential\b": 50,
    r"\bremote\s*access\b": 65,
    r"\banydesk|teamviewer|anydesk\b": 70,
    r"\bscreen\s*share\b": 65,
    r"\bwork\s*from\s*home\b": 40,
    r"\bdata\s*entry\b": 35,
    r"\bhigh\s*return\b": 55,
    r"\bguaranteed\s*profit\b": 60,
    r"\bSEBI\s*approved\b": 50,
    r"\binvestment\s*scheme\b": 55,
    r"\brefundable\b": 40,
    r"\blaptop\s*setup\b": 45,
}

# Low-severity keywords (contextual only)
LOW_RISK_KEYWORDS = {
    r"\bbank\s*account\b": 20,
    r"\baccount\s*number\b": 25,
    r"\bUPI\s*ID\b": 20,
    r"\bOTP\b": 30,
    r"\bverification\b": 20,
    r"\bKYC\b": 25,
    r"\bAadhaar\b": 20,
    r"\bPAN\s*card\b": 20,
    r"\bpassport\b": 15,
    r"\bnet\s*banking\b": 20,
    r"\binternet\s*banking\b": 20,
}


# ============================================================================
# CLASSIFIER ENGINE
# ============================================================================

class TranscriptClassifier:
    """
    Multi-stage NLP classifier for scam transcript analysis.
    Combines keyword matching, density analysis, pattern recognition,
    and synthesized voice stress analysis for risk scoring.
    """

    def __init__(self):
        self.high_keywords = HIGH_RISK_KEYWORDS
        self.medium_keywords = MEDIUM_RISK_KEYWORDS
        self.low_keywords = LOW_RISK_KEYWORDS

    def classify(self, text: str, pitch_variance: float = 0.0) -> Dict[str, Any]:
        """
        Full classification pipeline for a single transcript chunk.

        Returns:
            Dict with risk_score, risk_category, matched_keywords,
            analysis_details, and is_spoof flag.
        """
        if not text or not text.strip():
            return {
                "risk_score": 0.0,
                "risk_category": "Safe",
                "matched_keywords": [],
                "pitch_variance": pitch_variance,
                "is_spoof": False,
                "analysis_details": {"word_count": 0, "keyword_density": 0},
            }

        # Stage 1: Keyword matching with severity scoring
        matched = self._match_keywords(text)
        keyword_score = self._calculate_keyword_score(matched)

        # Stage 2: Keyword density analysis
        word_count = len(text.split())
        density_score = self._calculate_density_score(word_count, len(matched))

        # Stage 3: Pattern recognition (threat structures, urgency)
        pattern_score = self._analyze_patterns(text)

        # Stage 4: Voice stress / pitch analysis
        stress_score = self._analyze_voice_stress(pitch_variance)

        # Stage 5: Spoof signature detection
        spoof_score, is_spoof = self._detect_spoof_signatures(text, pitch_variance)

        # Aggregate risk score (weighted ensemble)
        risk_score = (
            keyword_score * 0.40 +
            density_score * 0.15 +
            pattern_score * 0.20 +
            stress_score * 0.15 +
            spoof_score * 0.10
        )

        # Clamp to [0, 100]
        risk_score = max(0.0, min(100.0, risk_score))

        # Categorize
        category = self._categorize_risk(risk_score)

        return {
            "risk_score": round(risk_score, 2),
            "risk_category": category,
            "matched_keywords": matched,
            "pitch_variance": pitch_variance,
            "is_spoof": is_spoof,
            "analysis_details": {
                "word_count": word_count,
                "keyword_matches": len(matched),
                "keyword_density": round(density_score, 2),
                "pattern_score": round(pattern_score, 2),
                "stress_score": round(stress_score, 2),
                "spoof_score": round(spoof_score, 2),
            }
        }

    def _match_keywords(self, text: str) -> List[Dict[str, Any]]:
        """Match all keywords in text and return with severity scores."""
        text_lower = text.lower()
        matched = []

        # Check high-risk keywords
        for pattern, score in self.high_keywords.items():
            matches = re.findall(pattern, text_lower)
            for m in matches:
                matched.append({
                    "keyword": m,
                    "score": score,
                    "severity": "High",
                })

        # Check medium-risk keywords
        for pattern, score in self.medium_keywords.items():
            matches = re.findall(pattern, text_lower)
            for m in matches:
                matched.append({
                    "keyword": m,
                    "score": score,
                    "severity": "Medium",
                })

        # Check low-risk keywords
        for pattern, score in self.low_keywords.items():
            matches = re.findall(pattern, text_lower)
            for m in matches:
                matched.append({
                    "keyword": m,
                    "score": score,
                    "severity": "Low",
                })

        return matched

    def _calculate_keyword_score(self, matched: List[Dict[str, Any]]) -> float:
        """Calculate aggregate keyword risk score."""
        if not matched:
            return 0.0

        # Weighted sum with diminishing returns
        total = 0.0
        high_count = sum(1 for m in matched if m["severity"] == "High")
        medium_count = sum(1 for m in matched if m["severity"] == "Medium")

        total = sum(m["score"] for m in matched)

        # Boost for multiple high-severity matches
        if high_count >= 3:
            total *= 1.3
        elif high_count >= 2:
            total *= 1.15

        # Normalize to 0-100 scale
        normalized = min(100.0, total * 0.6)
        return normalized

    def _calculate_density_score(self, word_count: int, match_count: int) -> float:
        """Calculate score based on keyword density in text."""
        if word_count == 0 or match_count == 0:
            return 0.0

        density = match_count / word_count

        # Higher density = higher risk
        if density > 0.5:
            return 90.0
        elif density > 0.3:
            return 70.0
        elif density > 0.15:
            return 50.0
        elif density > 0.08:
            return 30.0
        else:
            return 10.0

    def _analyze_patterns(self, text: str) -> float:
        """Analyze textual patterns indicating scam behavior."""
        text_lower = text.lower()
        score = 0.0

        # Threat + Demand pattern
        threat_demand = bool(
            re.search(r'(arrest|case|notice|freeze|seized|legal)', text_lower) and
            re.search(r'(pay|transfer|send|deposit|fee|amount|money)', text_lower)
        )
        if threat_demand:
            score += 30.0

        # Urgency escalation
        if re.search(r'immediate|urgent|within|hurry|asap|right now', text_lower):
            score += 15.0

        # Authority impersonation
        if re.search(r'(cbi|ed|nc|police|court|judge|commissioner|director)', text_lower):
            score += 20.0

        # Amount references
        amounts = re.findall(r'(?:Rs\.?\s*)?(\d{3,}(?:,\d{3})*(?:\.\d{1,2})?)', text_lower)
        if amounts:
            score += min(15.0, len(amounts) * 5.0)

        # Secrecy enforcement
        if re.search(r"(don't\s*tell|keep\s*secret|confidential|don't\s*disclose)", text_lower):
            score += 20.0

        return min(100.0, score)

    def _analyze_voice_stress(self, pitch_variance: float) -> float:
        """Analyze pitch variance as proxy for voice stress."""
        # Higher variance suggests stress/lying
        if pitch_variance > 0.7:
            return 80.0
        elif pitch_variance > 0.5:
            return 60.0
        elif pitch_variance > 0.3:
            return 40.0
        elif pitch_variance > 0.15:
            return 20.0
        else:
            return 5.0

    def _detect_spoof_signatures(self, text: str, pitch_variance: float) -> Tuple[float, bool]:
        """
        Detect potential spoof call signatures.
        Returns (spoof_score, is_spoof_classified).
        """
        text_lower = text.lower()
        indicators = 0
        total_checks = 5

        # 1. Text-to-speech artifacts (unusual phrasing)
        if re.search(r'(kindly\s*do\s*the\s*needful|the\s*same\s*is|hereby\s*informed)', text_lower):
            indicators += 1

        # 2. Overly structured/scripted feel
        if re.search(r'(this is | speaking from | on the line | here is your )', text_lower):
            indicators += 1

        # 3. Call-back numbers
        if re.search(r'\b(\+?91[-\s]?)?[6-9]\d{9}\b', text_lower):
            indicators += 1

        # 4. Reference numbers / case IDs
        if re.search(r'(case\s*(no|number|id)|reference|ticket|complaint\s*no)[\s:]*[A-Z0-9/]+', text_lower, re.IGNORECASE):
            indicators += 1

        # 5. High pitch variance (stress indicator)
        if pitch_variance > 0.5:
            indicators += 1

        spoof_score = (indicators / total_checks) * 100.0
        is_spoof = spoof_score >= 50.0

        return spoof_score, is_spoof

    def _categorize_risk(self, score: float) -> str:
        """Map risk score to category label."""
        if score >= settings.RISK_THRESHOLD_HIGH:
            return "Active Scam"
        elif score >= settings.RISK_THRESHOLD_MEDIUM:
            return "High Risk"
        elif score >= settings.RISK_THRESHOLD_LOW:
            return "Suspicious"
        else:
            return "Safe"


# ============================================================================
# BATCH / STREAM PROCESSOR
# ============================================================================

class StreamClassifier:
    """
    Processes streaming audio chunks through the classification pipeline.
    Accumulates context across chunks for improved accuracy.
    """

    def __init__(self):
        self.classifier = TranscriptClassifier()
        self._call_contexts: Dict[str, Dict[str, Any]] = {}

    def _get_context(self, call_id: str) -> Dict[str, Any]:
        """Get or create context for a call stream."""
        if call_id not in self._call_contexts:
            self._call_contexts[call_id] = {
                "call_id": call_id,
                "chunks": [],
                "all_text": "",
                "peak_risk": 0.0,
                "peak_category": "Safe",
                "alerts_generated": [],
                "keyword_accumulator": [],
                "spoof_probability": 0.0,
            }
        return self._call_contexts[call_id]

    def process_chunk(self, call_id: str, text: str, pitch_variance: float = 0.0) -> Dict[str, Any]:
        """
        Classify a single transcript chunk with call context.

        Returns:
            Full classification result plus cumulative call risk.
        """
        context = self._get_context(call_id)
        context["chunks"].append(text)
        context["all_text"] += " " + text

        # Classify current chunk
        result = self.classifier.classify(text, pitch_variance)

        # Update context
        context["keyword_accumulator"].extend(result["matched_keywords"])
        if result["risk_score"] > context["peak_risk"]:
            context["peak_risk"] = result["risk_score"]
            context["peak_category"] = result["risk_category"]

        if result["is_spoof"]:
            context["spoof_probability"] = min(
                1.0,
                context["spoof_probability"] + 0.15
            )

        # Add cumulative context
        result["call_context"] = {
            "chunk_count": len(context["chunks"]),
            "cumulative_risk": round(context["peak_risk"], 2),
            "cumulative_category": context["peak_category"],
            "total_keywords_matched": len(set(
                m["keyword"] for m in context["keyword_accumulator"]
            )),
            "spoof_probability": round(context["spoof_probability"] * 100, 1),
        }

        return result

    def get_call_summary(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get the complete analysis summary for a call."""
        context = self._call_contexts.get(call_id)
        if not context:
            return None

        return {
            "call_id": call_id,
            "total_chunks": len(context["chunks"]),
            "transcript": context["all_text"].strip(),
            "peak_risk_score": round(context["peak_risk"], 2),
            "peak_risk_category": context["peak_category"],
            "spoof_probability": round(context["spoof_probability"] * 100, 1),
            "alert_generated": context["peak_risk"] >= settings.RISK_THRESHOLD_MEDIUM,
            "total_unique_keywords": len(set(
                m["keyword"] for m in context["keyword_accumulator"]
            )),
        }

    def clear_context(self, call_id: str):
        """Clear context for a completed call."""
        self._call_contexts.pop(call_id, None)


# Global classifier instances
transcript_classifier = TranscriptClassifier()
stream_classifier = StreamClassifier()