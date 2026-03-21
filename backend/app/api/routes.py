# backend/app/api/routes.py

from __future__ import annotations

from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.gradcam import generate_gradcam_base64
from app.models.metadata import extract_exif, metadata_trust_analysis
from app.models.predictor import ImagePredictor
from app.utils.image_processing import preprocess_image

router = APIRouter()

# -------------------------
# Health
# -------------------------
@router.get("/health")
def health():
    return {"status": "ok"}

# -------------------------
# Lazy predictor singleton
# -------------------------
_predictor: ImagePredictor | None = None


def get_predictor() -> ImagePredictor:
    global _predictor
    if _predictor is None:
        _predictor = ImagePredictor()
    return _predictor


# -------------------------
# Metadata endpoint
# -------------------------
@router.post("/metadata")
async def metadata(file: UploadFile = File(...)):
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(400, f"Unsupported format. Use: {', '.join(sorted(allowed))}")

    try:
        contents = await file.read()
        exif_data = extract_exif(contents)
        analysis = metadata_trust_analysis(exif_data, file.content_type)

        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "exif": exif_data,
            "analysis": analysis,
        }
    except Exception as e:
        raise HTTPException(400, f"Metadata extraction failed: {str(e)}")


# -------------------------
# Detect endpoint (optional heatmap)
# -------------------------
@router.post("/detect")
async def detect_ai_image(
    file: UploadFile = File(...),
    include_heatmap: bool = Form(False),
):
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(400, f"Unsupported format. Use: {', '.join(sorted(allowed))}")

    # Read + preprocess
    try:
        contents = await file.read()
        tensor, pil_image = preprocess_image(contents, return_pil=True)
    except Exception as e:
        raise HTTPException(400, f"Invalid image: {str(e)}")

    # Predict
    try:
        predictor = get_predictor()
        pred = predictor.predict(tensor)
    except FileNotFoundError:
        raise HTTPException(
            503,
            "Model checkpoint not found. Place trained weights in backend/models/checkpoints/",
        )
    except Exception as e:
        raise HTTPException(500, f"Inference error: {str(e)}")

    # Heatmap only if requested
    heatmap = None
    if include_heatmap:
       heatmap = generate_gradcam_base64(
            model=predictor.model1,
            input_tensor=tensor,
            original_pil=pil_image,
            device=None,
        )

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "heatmap": heatmap,
        **pred,
    }


# -------------------------
# Batch endpoint (+ split averages)
# -------------------------
@router.post("/batch")
async def batch_analyze(
    files: List[UploadFile] = File(...),
    include_heatmap: bool = Form(False),
):
    allowed = {"image/jpeg", "image/png", "image/webp"}

    results = []

    ai_count = 0
    real_count = 0

    total_conf = 0.0
    ai_conf_total = 0.0
    real_conf_total = 0.0

    total_meta = 0.0
    ai_meta_total = 0.0
    real_meta_total = 0.0

    exif_present = 0
    exif_missing = 0

    predictor = get_predictor()

    for f in files:
        item = {"filename": f.filename, "content_type": f.content_type}

        if f.content_type not in allowed:
            item["error"] = f"Unsupported format. Use: {', '.join(sorted(allowed))}"
            results.append(item)
            continue

        try:
            contents = await f.read()
            if not contents:
                item["error"] = "Empty file."
                results.append(item)
                continue

            tensor, pil_image = preprocess_image(contents, return_pil=True)

            pred = predictor.predict(tensor)
            label = str(pred["label"])
            conf_val = float(pred["confidence"])

            item.update(pred)

            is_ai = label.upper() == "FAKE"
            if is_ai:
                ai_count += 1
                ai_conf_total += conf_val
            else:
                real_count += 1
                real_conf_total += conf_val

            total_conf += conf_val

            exif_data = extract_exif(contents)
            analysis = metadata_trust_analysis(exif_data, f.content_type)
            item["exif"] = exif_data
            item["analysis"] = analysis

            meta_score = float(analysis.get("metadata_trust_score", 0))
            total_meta += meta_score

            if is_ai:
                ai_meta_total += meta_score
            else:
                real_meta_total += meta_score

            if exif_data.get("has_exif"):
                exif_present += 1
            else:
                exif_missing += 1

            if include_heatmap:
                item["heatmap"] = generate_gradcam_base64(
                    model=predictor.model,
                    input_tensor=tensor,
                    original_pil=pil_image,
                    device=None,
                )
            else:
                item["heatmap"] = None

            results.append(item)

        except Exception as e:
            item["error"] = f"Failed to process image: {str(e)}"
            results.append(item)

    processed = ai_count + real_count
    failed = len([r for r in results if "error" in r])

    avg_conf = round(total_conf / processed, 4) if processed > 0 else 0.0
    avg_conf_ai = round(ai_conf_total / ai_count, 4) if ai_count > 0 else None
    avg_conf_real = round(real_conf_total / real_count, 4) if real_count > 0 else None

    avg_meta = round(total_meta / processed, 2) if processed > 0 else 0.0
    avg_meta_ai = round(ai_meta_total / ai_count, 2) if ai_count > 0 else None
    avg_meta_real = round(real_meta_total / real_count, 2) if real_count > 0 else None

    return {
        "processed": processed,
        "failed": failed,
        "ai_count": ai_count,
        "real_count": real_count,
        "avg_confidence": avg_conf,
        "avg_confidence_ai": avg_conf_ai,
        "avg_confidence_real": avg_conf_real,
        "avg_metadata_trust_score": avg_meta,
        "avg_metadata_trust_score_ai": avg_meta_ai,
        "avg_metadata_trust_score_real": avg_meta_real,
        "exif_present_count": exif_present,
        "exif_missing_count": exif_missing,
        "results": results,
    }