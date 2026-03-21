import numpy as np
import tensorflow as tf
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL1_PATH = str(BASE_DIR / "models" / "checkpoints" / "final_real_vs_fake_detector.keras")
MODEL2_PATH = str(BASE_DIR / "models" / "checkpoints" / "final_model2_general.keras")


class ImagePredictor:
    def __init__(self):
        if not Path(MODEL1_PATH).exists():
            raise FileNotFoundError(f"Model not found: {MODEL1_PATH}")
        if not Path(MODEL2_PATH).exists():
            raise FileNotFoundError(f"Model not found: {MODEL2_PATH}")

        self.model1 = tf.keras.models.load_model(MODEL1_PATH, compile=False)
        self.model2 = tf.keras.models.load_model(MODEL2_PATH, compile=False)
        print("✅ Both models loaded successfully")

    def predict(self, tensor: np.ndarray) -> Dict[str, Any]:
        pred1 = self.model1.predict(tensor)[0][0]
        pred2 = self.model2.predict(tensor)[0][0]
        final_pred = float(pred2)

        if final_pred >= 0.5:
            label = "REAL"
            confidence = float(final_pred)
        else:
            label = "FAKE"
            confidence = float(1 - final_pred)

        return {
            "label": label,
            "confidence": confidence,
            "model1_score": float(pred1),
            "model2_score": float(pred2)
        }