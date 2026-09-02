"""
evidence_fusion.py
-------------------
FasalSetu — AI Evidence Fusion Engine

Combines the 4 raw evidence sources described in the pitch deck's
"Flow of Solution" (Slide 4):

    📸 Farmer Photos          -> damage type + visual condition
    🛰️ Satellite (pre/post)   -> independent large-area change detection
    🌦️ Weather / Event Data   -> validates the reported disaster event
    📍 GPS / Field Boundary   -> confirms photos were taken on the claimed field

Output of this module is an `EvidenceInput` object — the exact shape
`claim_triage.py` expects — so the two files plug together directly:

    fusion = EvidenceFusionEngine()
    evidence = fusion.fuse(claim_id, farmer_id, field_meta, photos, satellite, weather, gps)
    result = ClaimTriage().triage(evidence)

This module does NOT decide claim priority — that's claim_triage.py's job.
It only fuses raw inputs into consistent, comparable evidence.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date

# Reuses the same EvidenceInput shape claim_triage.py expects.
# In this scaffold it's redefined locally so evidence_fusion.py can run
# standalone — once damage_detection.py is filled in, import EvidenceInput
# from claim_triage instead of duplicating it.
from claim_triage import EvidenceInput


# ---------------------------------------------------------------------
# Raw input containers — what each upstream source actually provides
# ---------------------------------------------------------------------

@dataclass
class FarmerPhoto:
    url: str
    latitude: float
    longitude: float
    timestamp: str


@dataclass
class FarmerSubmission:
    field_id: str
    farmer_id: str
    crop: str
    area_hectares: float
    damage_type: str          # e.g. "Flood submergence", "Drought", "Storm", "Pest attack"
    photos: List[FarmerPhoto] = field(default_factory=list)
    registered_field_polygon: Optional[list] = None  # [(lat, lon), ...] boundary


@dataclass
class SatelliteEvidence:
    pre_event_image_url: str
    post_event_image_url: str
    change_detection_score: float   # 0-1, from Sentinel-2 NDVI / change-detection model


@dataclass
class WeatherEvidence:
    event_date: date
    reported_event_type: str        # what the farmer claims happened
    recorded_event_type: Optional[str]   # what official weather data recorded, if any
    rainfall_mm: Optional[float] = None
    extreme_event_flag: bool = False


# ---------------------------------------------------------------------
# Fusion engine
# ---------------------------------------------------------------------

class EvidenceFusionEngine:
    """
    Fuses farmer photos, satellite imagery, weather data and GPS
    into one EvidenceInput ready for claim_triage.py.

    NOTE: damage_confidence and affected_area_pct below are placeholders.
    Once damage_detection.py has a real CV model, replace
    `self._estimate_damage_from_photos()` with a call into it.
    """

    def __init__(self, gps_tolerance_meters: float = 50.0):
        self.gps_tolerance_meters = gps_tolerance_meters

    # -- individual source scorers -------------------------------------

    def _estimate_damage_from_photos(self, submission: FarmerSubmission) -> tuple:
        """
        Placeholder for damage_detection.py's CV model.
        Returns (damage_confidence: 0-1, affected_area_pct: 0-100).
        Replace with: from damage_detection import classify_damage
        """
        if not submission.photos:
            return 0.0, 0.0
        # crude placeholder: more photos submitted -> slightly higher confidence
        confidence = min(0.6 + 0.1 * len(submission.photos), 0.95)
        affected_area_pct = 50.0  # until damage_detection.py provides a real estimate
        return confidence, affected_area_pct

    def _score_satellite_match(self, satellite: Optional[SatelliteEvidence]) -> float:
        """Returns 0-1: how strongly satellite change-detection corroborates the claim."""
        if satellite is None:
            return 0.0
        return max(0.0, min(satellite.change_detection_score, 1.0))

    def _verify_weather_event(self, weather: Optional[WeatherEvidence]) -> bool:
        """True if official weather/event records support the farmer's reported event."""
        if weather is None:
            return False
        if weather.recorded_event_type is None:
            return False
        return (
            weather.recorded_event_type.strip().lower()
            == weather.reported_event_type.strip().lower()
            or weather.extreme_event_flag
        )

    def _verify_gps_match(self, submission: FarmerSubmission) -> bool:
        """
        True if the farmer's photo GPS points fall within (or near) the
        registered field boundary. Placeholder uses a simple bounding check;
        swap in PostGIS ST_DWithin / point-in-polygon once backend is ready.
        """
        if not submission.registered_field_polygon or not submission.photos:
            return False

        lats = [p[0] for p in submission.registered_field_polygon]
        lons = [p[1] for p in submission.registered_field_polygon]
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)

        for photo in submission.photos:
            if not (min_lat <= photo.latitude <= max_lat and min_lon <= photo.longitude <= max_lon):
                return False
        return True

    # -- main entry point -------------------------------------------------

    def fuse(
        self,
        submission: FarmerSubmission,
        satellite: Optional[SatelliteEvidence] = None,
        weather: Optional[WeatherEvidence] = None,
    ) -> EvidenceInput:
        """
        Combines all sources for one claim into a single EvidenceInput,
        ready to hand to ClaimTriage().triage(...).
        """
        damage_confidence, affected_area_pct = self._estimate_damage_from_photos(submission)
        satellite_match_score = self._score_satellite_match(satellite)
        weather_verified = self._verify_weather_event(weather)
        gps_match = self._verify_gps_match(submission)

        return EvidenceInput(
            field_id=submission.field_id,
            farmer_id=submission.farmer_id,
            crop=submission.crop,
            area_hectares=submission.area_hectares,
            damage_type=submission.damage_type,
            affected_area_pct=affected_area_pct,
            damage_confidence=damage_confidence,
            satellite_match_score=satellite_match_score,
            weather_event_verified=weather_verified,
            gps_field_match=gps_match,
            photo_count=len(submission.photos),
        )


if __name__ == "__main__":
    # Demo matching the pitch deck's sample: Field FSL-1024, Wheat, flood submergence
    submission = FarmerSubmission(
        field_id="FSL-1024",
        farmer_id="F-2291",
        crop="Wheat",
        area_hectares=2.3,
        damage_type="Flood submergence",
        photos=[
            FarmerPhoto(url="photo1.jpg", latitude=28.6139, longitude=77.2090, timestamp="2026-08-20T09:00:00"),
            FarmerPhoto(url="photo2.jpg", latitude=28.6140, longitude=77.2091, timestamp="2026-08-20T09:01:00"),
            FarmerPhoto(url="photo3.jpg", latitude=28.6141, longitude=77.2089, timestamp="2026-08-20T09:02:00"),
            FarmerPhoto(url="photo4.jpg", latitude=28.6139, longitude=77.2092, timestamp="2026-08-20T09:03:00"),
        ],
        registered_field_polygon=[
            (28.6135, 77.2085),
            (28.6135, 77.2095),
            (28.6145, 77.2095),
            (28.6145, 77.2085),
        ],
    )

    satellite = SatelliteEvidence(
        pre_event_image_url="pre.jpg",
        post_event_image_url="post.jpg",
        change_detection_score=0.90,
    )

    weather = WeatherEvidence(
        event_date=date(2026, 8, 19),
        reported_event_type="Flood",
        recorded_event_type="Flood",
        rainfall_mm=210.5,
        extreme_event_flag=True,
    )

    engine = EvidenceFusionEngine()
    evidence = engine.fuse(submission, satellite, weather)

    print("Fused Evidence:")
    print(f"  Field: {evidence.field_id}  Farmer: {evidence.farmer_id}")
    print(f"  Damage Confidence: {evidence.damage_confidence}")
    print(f"  Satellite Match Score: {evidence.satellite_match_score}")
    print(f"  Weather Verified: {evidence.weather_event_verified}")
    print(f"  GPS Field Match: {evidence.gps_field_match}")

    # Feed straight into claim_triage.py
    from claim_triage import ClaimTriage
    result = ClaimTriage().triage(evidence)
    print(f"\nTriage Result: {result.priority.value}  ({result.evidence_confidence}%)")
    print(f"Action: {result.recommended_action}")
