import os
import argparse
import urllib.request

# Dictionary mapping run names to their hosted URLs on Hugging Face
DATASET_URLS = {
    # Metadata synchronized CSV files
    "metadata_all": "https://raw.githubusercontent.com/AD-Assurance-Lab/winter-driving-dataset/main/metadata/",
    
    # Standardized MCity-WSPI image sequences (zip packages)
    "jan27-downtown-1_images": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/images/mcity_wspi/jan27-downtown-1_images.zip",
    "jan27-highway-1_images": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/images/mcity_wspi/jan27-highway-1_images.zip",
    "jan27-highway-2_images": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/images/mcity_wspi/jan27-highway-2_images.zip",
    
    # MCity raw ROS2 db3 bag (Example)
    "mcity_jan27_rosbag": "https://huggingface.co/datasets/AD-Assurance-Lab/winter-driving-dataset/resolve/main/bags/jan27-downtown-1.db3"
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
    parser = argparse.ArgumentParser(description="Download utility for the AD Winter Driving Dataset.")
    parser.add_argument("--run", required=True, help="Name of the run or file package to download (e.g. 'jan27-downtown-1_images', 'mcity_jan27_rosbag', or 'all_metadata').")
    parser.add_argument("--dest_dir", default="./data", help="Local directory to save the downloaded file (default: './data').")
    
    args = parser.parse_args()
    
    if args.run == "all_metadata":
        print("Downloading all synchronized CSV metadata files...")
        dest_metadata_dir = os.path.join(args.dest_dir, "metadata", "mcity_wspi")
        os.makedirs(dest_metadata_dir, exist_ok=True)
        # Download a sample sync CSV using standardized names and paths
        url = "https://raw.githubusercontent.com/AD-Assurance-Lab/winter-driving-dataset/main/metadata/mcity_wspi/jan27-downtown-1_sync.csv"
        dest_path = os.path.join(dest_metadata_dir, "jan27-downtown-1_sync.csv")
        download_file(url, dest_path)
    else:
        if args.run in DATASET_URLS:
            url = DATASET_URLS[args.run]
            file_ext = url.split(".")[-1]
            dest_path = os.path.join(args.dest_dir, f"{args.run}.{file_ext}")
            download_file(url, dest_path)
        else:
            print(f"Error: Package '{args.run}' not found in the download repository.")
            print("Available packages:")
            for k in DATASET_URLS.keys():
                print(f"  - {k}")

if __name__ == '__main__':
    main()
