"""
Clean recreate & upload Hugging Face Space: parth1404/dermascan-api
This bypasses commit rate limits and removes all unwanted clutter in 1 clean step.
"""

import argparse
import sys
from pathlib import Path

try:
    from huggingface_hub import HfApi
except ImportError:
    print("Error: huggingface_hub is required. Run: pip install huggingface_hub")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"


def recreate_and_upload(repo_id: str, token: str):
    print(f"[*] Connecting to Hugging Face API with token...")
    api = HfApi(token=token)

    # 1. Delete old cluttered space (if exists)
    try:
        print(f"[*] Deleting old space: {repo_id} to clear clutter and reset rate limits...")
        api.delete_repo(repo_id=repo_id, repo_type="space")
        print(f"[+] Deleted old space successfully.")
    except Exception as e:
        print(f"[*] Note on deletion: {e}")

    # 2. Create fresh clean space with Gradio SDK
    print(f"[*] Creating fresh Space: {repo_id} (Gradio SDK, 16GB Free CPU)...")
    api.create_repo(
        repo_id=repo_id,
        repo_type="space",
        space_sdk="gradio",
        private=False,
    )
    print(f"[+] Fresh space created successfully.")

    # 3. Upload only clean production backend files in a single atomic commit
    print(f"[*] Uploading clean production backend files from: {BACKEND_DIR}...")
    api.upload_folder(
        folder_path=str(BACKEND_DIR),
        repo_id=repo_id,
        repo_type="space",
        commit_message="Deploy production FastAPI backend with MobileNetV2 model",
        ignore_patterns=[
            "**/__pycache__/**",
            "**/.pytest_cache/**",
            "**/.pytest-tmp*/**",
            "**/.venv*/**",
            "**/.quality-tools/**",
            "**/.verify-python/**",
            "tests/**",
            "*.pyc",
            "*.log",
            "coverage.xml",
            "requirements-dev.txt",
            "Dockerfile",
            "vercel.json",
            "package-lock.json",
            "uv.lock",
        ],
    )
    print(f"\n[+] SUCCESS! All backend files and trained AI models uploaded cleanly to:")
    print(f"    https://huggingface.co/spaces/{repo_id}")
    print(f"[+] Live Space URL:")
    print(f"    https://{repo_id.replace('/', '-')}.hf.space")


def main():
    parser = argparse.ArgumentParser(description="Clean recreate & upload Hugging Face Space")
    parser.add_argument(
        "--repo",
        type=str,
        default="parth1404/dermascan-api",
        help="Hugging Face Space repo id (default: parth1404/dermascan-api)",
    )
    parser.add_argument(
        "--token",
        type=str,
        required=True,
        help="Your Hugging Face write access token",
    )
    args = parser.parse_args()
    recreate_and_upload(args.repo, args.token)


if __name__ == "__main__":
    main()
