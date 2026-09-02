"""
claim_triage.py
----------------
FasalSetu — AI-Powered Rapid Crop-Loss Assessment & Claim Triage

This module takes the fused, multi-source evidence for a farmer's claim
(farmer photos, satellite imagery, weather/event data, GPS/field boundary)
and converts it into a triage decision that tells a human surveyor where
to look first.

IMPORTANT: This module never approves or rejects a claim. It only
recommends a verification priority. A human surveyor always makes the
final decision (human-in-the-loop, per the project's USP).

Expected upstream inputs (produced by damage_detection.py / evidence_fusion.py):
    - damage_confidence: float (0-1)   -> from computer-vision damage classification
    - satellite_match_score: float (0-1) -> pre/post event change-detection agreement
    - weather_event_verified: bool      -> whether weather/event data supports the claim
    - gps_field_match: bool             -> whether photo GPS matches registered field boundary
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class TriagePriority(Enum):
    STRONG_EVIDENCE = "🟢 Strong Evidence"          # Routine / fast processing
    CONFLICTING = "🟡 Conflicting / Insufficient"    # Human verification
    SIGNIFICANT_INCONSISTENCY = "🔴 Significant Inconsistency"  # Priority investigation


@dataclass
class EvidenceInput:
    """Raw evidence signals coming from the fusion pipeline for one claim."""
    field_id: str
    farmer_id: str
    crop: str
    area_hectares: float
    damage_type: str
    affected_area_pct: float          # 0-100, from damage_detection.py
    damage_confidence: float          # 0-1, model confidence on damage classification
    satellite_match_score: float      # 0-1, pre/post imagery agreement with claim
    weather_event_verified: bool      # True if rainfall/extreme-weather records match
    gps_field_match: bool             # True if photo GPS falls inside registered field
    photo_count: int = 0


@dataclass
class TriageResult:
    field_id: str
    farmer_id: str
    evidence_confidence: float        # 0-100, the "Evidence Confidence" shown to user
    priority: TriagePriority
    reasons: list = field(default_factory=list)
    recommended_action: str = ""
    triaged_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class ClaimTriage:
    """
    Fuses multi-source evidence into a single Evidence Confidence Score
    and buckets the claim into a triage priority.

    Weights are tunable — start simple, calibrate against real claim data
    or surveyor feedback later.
    """

    def __init__(
        self,
        w_damage: float = 0.40,
        w_satellite: float = 0.30,
        w_weather: float = 0.15,
        w_gps: float = 0.15,
        strong_threshold: float = 80.0,
        conflicting_threshold: float = 50.0,
    ):
        self.w_damage = w_damage
        self.w_satellite = w_satellite
        self.w_weather = w_weather
        self.w_gps = w_gps
        self.strong_threshold = strong_threshold
        self.conflicting_threshold = conflicting_threshold

    def compute_confidence(self, ev: EvidenceInput) -> float:
        """
        Combines all evidence sources into one 0-100 Evidence Confidence score.
        """
        weather_score = 1.0 if ev.weather_event_verified else 0.0
        gps_score = 1.0 if ev.gps_field_match else 0.0

        raw_score = (
            self.w_damage * ev.damage_confidence
            + self.w_satellite * ev.satellite_match_score
            + self.w_weather * weather_score
            + self.w_gps * gps_score
        )
        return round(raw_score * 100, 2)

    def _build_reasons(self, ev: EvidenceInput, confidence: float) -> list:
        reasons = []
        if ev.damage_confidence < 0.5:
            reasons.append("Low confidence in AI damage classification from photos")
        if ev.satellite_match_score < 0.5:
            reasons.append("Satellite pre/post imagery does not strongly corroborate reported damage")
        if not ev.weather_event_verified:
            reasons.append("No matching weather/extreme-event record found for claim date")
        if not ev.gps_field_match:
            reasons.append("Submitted photo GPS does not match registered field boundary")
        if ev.photo_count < 3:
            reasons.append("Fewer than the recommended 3-5 guided photos submitted")
        if not reasons:
            reasons.append("All evidence sources are consistent and corroborate the claim")
        return reasons

    def triage(self, ev: EvidenceInput) -> TriageResult:
        confidence = self.compute_confidence(ev)
        reasons = self._build_reasons(ev, confidence)

        if confidence >= self.strong_threshold:
            priority = TriagePriority.STRONG_EVIDENCE
            action = "Route to routine / fast-track processing queue"
        elif confidence >= self.conflicting_threshold:
            priority = TriagePriority.CONFLICTING
            action = "Route to human verification queue for surveyor review"
        else:
            priority = TriagePriority.SIGNIFICANT_INCONSISTENCY
            action = "Flag for priority field investigation"

        return TriageResult(
            field_id=ev.field_id,
            farmer_id=ev.farmer_id,
            evidence_confidence=confidence,
            priority=priority,
            reasons=reasons,
            recommended_action=action,
        )


def triage_batch(claims: list) -> list:
    """
    Triage a batch of claims (e.g. after a disaster event causes a surge)
    and return them ranked — priority investigations first, so surveyors
    see the most inconsistent / highest-risk claims at the top of the queue.
    """
    engine = ClaimTriage()
    results = [engine.triage(c) for c in claims]

    priority_order = {
        TriagePriority.SIGNIFICANT_INCONSISTENCY: 0,
        TriagePriority.CONFLICTING: 1,
        TriagePriority.STRONG_EVIDENCE: 2,
    }
    results.sort(key=lambda r: priority_order[r.priority])
    return results


if __name__ == "__main__":
    # Example matching the sample assessment output from the pitch deck
    # (Field FSL-1024, Wheat, 2.3 ha, Flood submergence, 68% affected, 91% confidence)
    sample = EvidenceInput(
        field_id="FSL-1024",
        farmer_id="F-2291",
        crop="Wheat",
        area_hectares=2.3,
        damage_type="Flood submergence",
        affected_area_pct=68.0,
        damage_confidence=0.93,
        satellite_match_score=0.90,
        weather_event_verified=True,
        gps_field_match=True,
        photo_count=4,
    )

    engine = ClaimTriage()
    result = engine.triage(sample)

    print(f"Field: {result.field_id}  |  Farmer: {result.farmer_id}")
    print(f"Evidence Confidence: {result.evidence_confidence}%")
    print(f"Priority: {result.priority.value}")
    print(f"Action: {result.recommended_action}")
    print("Reasons:")
    for r in result.reasons:
        print(f"  - {r}")
