import os
import argparse
import urllib.request

# Dictionary mapping model keys to their Hugging Face URLs
MODEL_URLS = {
    # PyTorch checkpoints
    "clrnet_pytorch": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/pytorch/CLRNet_180_320_Pytorch.pth",
    "laneatt_pytorch": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/pytorch/LaneATT_180_320_Pytorch.pt",
    "polylanenet_pytorch": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/pytorch/PolyLaneNet_180_320_Pytorch.pt",
    "scnn_pytorch": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/pytorch/SCNN_180_320_Pytorch.pth",
    
    # ONNX checkpoints
    "clrnet_onnx_fp32": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/onnx/CLRNet_180_320_fp32.onnx",
    "clrnet_onnx_fp16": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/onnx/CLRNet_180_320_fp16.onnx",
    "laneatt_onnx_fp32": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/onnx/LaneATT_180_320_fp32.onnx",
    "laneatt_onnx_fp16": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/onnx/LaneATT_180_320_fp16.onnx",
    "polylanenet_onnx_fp32": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/onnx/PolyLaneNet_180_320_fp32.onnx",
    "polylanenet_onnx_fp16": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/onnx/PolyLaneNet_180_320_fp16.onnx",
    "scnn_onnx_fp32": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/onnx/SCNN_180_320_fp32.onnx",
    "scnn_onnx_fp16": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/models/onnx/SCNN_180_320_fp16.onnx",
}

def download_file(url, dest_path):
    print(f"Downloading {url} -> {dest_path}")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    def report_progress(block_num, block_size, total_size):
        read_so_far = block_num * block_size
        if total_size > 0:
            percent = read_so_far * 100 / total_size
            print(f"\rProgress: {percent:.1f}% ({read_so_far / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB)", end="")
        else:
            print(f"\rRead: {read_so_far / (1024*1024):.1f} MB", end="")
            
    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=report_progress)
        print("\nDownload completed successfully.")
    except Exception as e:
        print(f"\nError downloading file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Download pre-trained models for the AD Winter Driving Dataset.")
    parser.add_argument("--model", required=True, help="Name of the model to download (e.g. 'scnn_onnx_fp32', 'clrnet_pytorch', or 'all').")
    parser.add_argument("--dest_dir", default="./models", help="Local directory to save the downloaded model (default: './models').")
    
    args = parser.parse_args()
    
    if args.model == "all":
        print("Downloading all pre-trained models...")
        for name, url in MODEL_URLS.items():
            folder = "pytorch" if "pytorch" in name else "onnx"
            filename = url.split("/")[-1]
            dest_path = os.path.join(args.dest_dir, folder, filename)
            download_file(url, dest_path)
    else:
        if args.model in MODEL_URLS:
            url = MODEL_URLS[args.model]
            folder = "pytorch" if "pytorch" in args.model else "onnx"
            filename = url.split("/")[-1]
            dest_path = os.path.join(args.dest_dir, folder, filename)
            download_file(url, dest_path)
        else:
            print(f"Error: Model '{args.model}' not found in the download repository.")
            print("Available model keys:")
            for k in MODEL_URLS.keys():
                print(f"  - {k}")
            print("  - all")

if __name__ == '__main__':
    main()
