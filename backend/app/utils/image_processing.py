# backend/app/utils/image_processing.py

import numpy as np
from tensorflow.keras.applications.efficientnet import preprocess_input
from app.utils.safe_end import load_image_safe


def preprocess_image(image_bytes: bytes, return_pil=False):
    image = load_image_safe(image_bytes)
    image_resized = image.resize((224, 224))

    img_array = np.array(image_resized, dtype=np.float32)
    img_array = preprocess_input(img_array)       # EfficientNet-specific normalization
    tensor = np.expand_dims(img_array, axis=0)    # shape: (1, 224, 224, 3)

    if return_pil:
        return tensor, image
    return tensor