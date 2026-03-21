from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models" / "checkpoints"

MODEL1_PATH = MODELS_DIR / "final_real_vs_fake_detector.keras"
MODEL2_PATH = MODELS_DIR / "final_model2_general.keras"

IMAGE_SIZE = 224
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]

CLASS_NAMES = ["AI-generated", "Real"]
NUM_CLASSES = 2