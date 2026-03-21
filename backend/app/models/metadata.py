# backend/app/models/metadata.py
# =============================================================================
# Metadata Forensics
# Purpose: Extract EXIF metadata + compute a "trust score" heuristic
# =============================================================================

from __future__ import annotations

import io
from typing import Any, Dict, Optional

from PIL import Image, ExifTags


# ---------------------------------------------------------------------------
# GPS parsing (best-effort, NEVER crashes)
# ---------------------------------------------------------------------------
def _parse_gps(gps_info: dict) -> Optional[dict]:
    if not gps_info:
        return None

    def to_float(x):
        try:
            return float(x)
        except Exception:
            try:
                return x[0] / x[1]
            except Exception:
                return None

    def to_degrees(values):
        if not isinstance(values, (list, tuple)) or len(values) < 3:
            return None

        d = to_float(values[0])
        m = to_float(values[1])
        s = to_float(values[2])

        if d is None or m is None or s is None:
            return None

        return d + (m / 60.0) + (s / 3600.0)

    gps_named = {}
    for k, v in gps_info.items():
        gps_named[ExifTags.GPSTAGS.get(k, k)] = v

    lat = None
    lon = None

    if "GPSLatitude" in gps_named and "GPSLatitudeRef" in gps_named:
        lat = to_degrees(gps_named.get("GPSLatitude"))
        if lat is not None and gps_named.get("GPSLatitudeRef") in ["S", b"S"]:
            lat = -lat

    if "GPSLongitude" in gps_named and "GPSLongitudeRef" in gps_named:
        lon = to_degrees(gps_named.get("GPSLongitude"))
        if lon is not None and gps_named.get("GPSLongitudeRef") in ["W", b"W"]:
            lon = -lon

    if lat is None and lon is None:
        return None

    return {"lat": lat, "lon": lon}


# ---------------------------------------------------------------------------
# EXIF extraction (JSON-SAFE, NEVER crashes)
# ---------------------------------------------------------------------------
def extract_exif(image_bytes: bytes) -> Dict[str, Any]:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        exif_data = img.getexif()

        if not exif_data:
            return {
                "has_exif": False,
                "camera_make": None,
                "camera_model": None,
                "datetime_original": None,
                "software": None,
                "gps": None,
                "raw_exif": {},
            }

        raw_exif: Dict[str, str] = {}

        # 🔥 ALWAYS stringify EXIF values (this is the key fix)
        for tag_id, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)
            raw_exif[str(tag_name)] = str(value)

        gps_info = exif_data.get(34853)  # GPSInfo tag

        return {
            "has_exif": True,
            "camera_make": raw_exif.get("Make"),
            "camera_model": raw_exif.get("Model"),
            "datetime_original": raw_exif.get("DateTimeOriginal")
            or raw_exif.get("DateTime"),
            "software": raw_exif.get("Software"),
            "gps": _parse_gps(gps_info) if gps_info else None,
            "raw_exif": raw_exif,
        }

    except Exception:
        # Any EXIF failure → treated as stripped metadata
        return {
            "has_exif": False,
            "camera_make": None,
            "camera_model": None,
            "datetime_original": None,
            "software": None,
            "gps": None,
            "raw_exif": {},
        }


# ---------------------------------------------------------------------------
# Metadata trust analysis (heuristic, explainable)
# ---------------------------------------------------------------------------
def metadata_trust_analysis(exif_data: Dict[str, Any], content_type: str) -> Dict[str, Any]:
    score = 70
    flags = []

    if not exif_data.get("has_exif"):
        return {
            "metadata_trust_score": 45,
            "verdict": "Inconclusive (metadata missing/stripped)",
            "flags": [
                "No EXIF metadata found. This commonly happens after messaging apps, "
                "screenshots, or editing/exporting and is not proof of AI by itself."
            ],
        }

    if not exif_data.get("camera_make") or not exif_data.get("camera_model"):
        score -= 15
        flags.append("Camera make/model missing (often stripped during export).")

    if not exif_data.get("datetime_original"):
        score -= 10
        flags.append("Original capture timestamp missing.")

    software = exif_data.get("software")
    if software:
        sw = software.lower()
        editors = ["photoshop", "lightroom", "snapseed", "picsart", "canva", "gimp", "capcut"]
        if any(e in sw for e in editors):
            score -= 20
            flags.append(f"Software tag suggests editing/export: {software}")

    if exif_data.get("gps") is None:
        score -= 5
        flags.append("No GPS data (common; many users disable location).")

    if "png" in content_type.lower():
        score -= 5
        flags.append("PNG format detected: metadata is often stripped on conversion.")

    score = max(0, min(100, score))

    verdict = "Likely authentic camera metadata"
    if score < 55:
        verdict = "Inconclusive (metadata may be edited/stripped)"
    if score < 35:
        verdict = "Suspicious metadata (missing/inconsistent)"

    return {
        "metadata_trust_score": score,
        "verdict": verdict,
        "flags": flags,
    }