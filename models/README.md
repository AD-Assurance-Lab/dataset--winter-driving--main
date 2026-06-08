# Pre-Trained Lane Detection Benchmarks

This directory tracks the documentation and hosting links for pre-trained deep learning checkpoints evaluated on the **REVA (MI-Snow1000)** perception module. 

To keep the git repository lightweight, the binary model weight files (such as `.pt`, `.pth`, and `.onnx` files) are listed in `.gitignore` and are not committed to GitHub. However, they are hosted publicly on Hugging Face for easy download.

---

## 1. Supported Model Architectures

The dataset benchmark evaluates four popular lane detection architectures, trained on the MI-Snow1000 dataset:

| Model | Frame Size | Format | PyTorch File | ONNX Float32 File | ONNX Float16 File |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **CLRNet** | 180x320 | PyTorch & ONNX | `pytorch/CLRNet_180_320_Pytorch.pth` | `onnx/CLRNet_180_320_fp32.onnx` | `onnx/CLRNet_180_320_fp16.onnx` |
| **LaneATT** | 180x320 | PyTorch & ONNX | `pytorch/LaneATT_180_320_Pytorch.pt` | `onnx/LaneATT_180_320_fp32.onnx` | `onnx/LaneATT_180_320_fp16.onnx` |
| **PolyLaneNet** | 180x320 | PyTorch & ONNX | `pytorch/PolyLaneNet_180_320_Pytorch.pt` | `onnx/PolyLaneNet_180_320_fp32.onnx` | `onnx/PolyLaneNet_180_320_fp16.onnx` |
| **SCNN** | 180x320 | PyTorch & ONNX | `pytorch/SCNN_180_320_Pytorch.pth` | `onnx/SCNN_180_320_fp32.onnx` | `onnx/SCNN_180_320_fp16.onnx` |

---

## 2. Model Descriptions

- **CLRNet (Cross Layer Refinement Network)**: Focuses on line segment refinement across multiple feature layers, achieving high accuracy on thin lane boundaries and low-contrast snowy edges.
- **LaneATT (Lane Attention)**: Utilizes an anchor-based attention mechanism to aggregate global spatial context, providing high processing speed (FPS) and robust lane line tracing.
- **PolyLaneNet**: Formulates lane detection as a polynomial regression problem, fitting third-order polynomials directly to the lanes for compact, fast predictions.
- **SCNN (Spatial CNN)**: Propagates spatial information slice-by-slice across rows and columns, allowing the model to capture continuous structures like dashed or partially covered lanes under snow buildup.

---

## 3. Downloader Tool

We provide a utility script to download the pre-trained weights from Hugging Face directly to your local `models/` directory:

```bash
# Download a specific model (e.g. SCNN ONNX model)
python3 tools/download_models.py --model scnn_onnx_fp32 --dest_dir ./models

# Download all models (PyTorch + ONNX)
python3 tools/download_models.py --model all --dest_dir ./models
```
