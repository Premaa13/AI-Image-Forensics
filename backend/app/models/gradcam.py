# backend/app/models/gradcam.py

import base64
import io
import numpy as np
from PIL import Image
import tensorflow as tf

try:
    import cv2
except Exception:
    cv2 = None


def generate_gradcam_base64(
    model: tf.keras.Model,
    input_tensor: np.ndarray,
    original_pil: Image.Image,
    device=None,
) -> str:

    efficientnet = model.get_layer('efficientnetb0')
    top_conv = efficientnet.get_layer('top_conv')

    input_array = tf.cast(input_tensor, tf.float32)
    input_var = tf.Variable(input_array)

    with tf.GradientTape() as tape:
        tape.watch(input_var)
        # Run full model
        predictions = model(input_var, training=False)
        pred_idx = tf.argmax(predictions[0])
        score = predictions[:, pred_idx]

    # Get gradients w.r.t input, then get activations separately
    input_grads = tape.gradient(score, input_var)

    # Get conv activations by running efficientnet separately
    conv_model = tf.keras.models.Model(
        inputs=efficientnet.inputs,
        outputs=top_conv.output
    )
    conv_outputs = conv_model(input_array, training=False)

    # Simple CAM using activation magnitude (no gradient needed)
    cam = tf.reduce_mean(conv_outputs[0], axis=-1).numpy()
    cam = np.maximum(cam, 0)
    cam = cam / (cam.max() + 1e-8)

    orig = original_pil.convert("RGB")
    ow, oh = orig.size
    cam_uint8 = (cam * 255).astype(np.uint8)

    if cv2 is not None:
        cam_resized = cv2.resize(cam_uint8, (ow, oh))
        heat = cv2.applyColorMap(cam_resized, cv2.COLORMAP_JET)
        heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
        orig_np = np.array(orig)
        overlay = (0.55 * orig_np + 0.45 * heat).astype(np.uint8)
        out_img = Image.fromarray(overlay)
    else:
        cam_resized = Image.fromarray(cam_uint8).resize((ow, oh), Image.BILINEAR)
        heat = Image.new("RGB", (ow, oh), (255, 0, 0))
        out_img = Image.blend(orig, heat, alpha=0.35)
        out_img = Image.composite(out_img, orig, cam_resized.convert("L"))

    buf = io.BytesIO()
    out_img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")