# backend/quick_check.py

print("🚀 Running prediction...")

try:
    from app.models.predictor import ImagePredictor

    predictor = ImagePredictor()

    image_path = "backend/test.jpg"

    result = predictor.predict(image_path)

    print(f"✅ Result: {result['label']} ({result['confidence']:.4f})")

except Exception as e:
    print("❌ Error:", e)