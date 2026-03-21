# Training - Kaggle Notebooks

> Purpose: Train and export the EfficientNet model for AI vs Real image classification.

## Structure

```
training/
├── notebooks/     # Kaggle notebooks (.ipynb)
├── input/         # Kaggle datasets (ignored by git)
├── output/        # Saved checkpoints (ignored by git)
└── README.md
```

## Getting Started

1. Create a Kaggle dataset with AI-generated and Real images (balanced classes).
2. Add a notebook in `notebooks/` that:
   - Loads data from `/kaggle/input/...`
   - Uses `torchvision.models.efficientnet_b0` with a 2-class classifier
   - Saves the checkpoint to `/kaggle/working/` or `output/`
3. Download the `.pt` file and place it in `backend/models/checkpoints/efficientnet_ai_detector.pt`

## Suggested Preprocessing

- Resize: 224×224
- Normalize: ImageNet mean/std `[0.485,0.456,0.406]` / `[0.229,0.224,0.225]`
