"""
Cleanly synchronize backend to Hugging Face Space: parth1404/dermascan-api
Uses batch commit operations for fast atomic cleanup and upload.
"""

import argparse
import sys
from pathlib import Path

try:
    from huggingface_hub import HfApi, CommitOperationDelete
except ImportError:
    print("Error: huggingface_hub is required. Run: pip install huggingface_hub")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_ROOT / "backend"


def clean_sync_space(repo_id: str, token: str):
    print(f"[*] Connecting to Hugging Face Space: {repo_id}...")
    api = HfApi(token=token)

    # 1. Fetch existing files
    print("[*] Listing remote files...")
    existing_files = api.list_repo_files(repo_id=repo_id, repo_type="space")
    print(f"[*] Found {len(existing_files)} remote files.")

    junk_files = [
        f for f in existing_files
        if f.startswith(".quality-tools/")
        or f.startswith(".pytest_cache/")
        or f.startswith(".venv")
        or f.startswith(".verify-python/")
        or f.endswith(".pyc")
        or "/__pycache__/" in f
    ]

    if junk_files:
        print(f"[*] Deleting {len(junk_files)} unwanted temporary files in atomic batch commits...")
        chunk_size = 300
        for i in range(0, len(junk_files), chunk_size):
            chunk = junk_files[i:i+chunk_size]
            operations = [CommitOperationDelete(path_in_repo=f) for f in chunk]
            print(f"    - Committing deletion of files {i+1} to {min(i+chunk_size, len(junk_files))}...")
            try:
                api.create_commit(
                    repo_id=repo_id,
                    repo_type="space",
                    operations=operations,
                    commit_message=f"Clean up temporary files batch {i // chunk_size + 1}",
                )
            except Exception as e:
                print(f"    [!] Error during batch delete: {e}")

    # 2. Upload only production files
    print(f"[*] Uploading clean backend files from: {BACKEND_DIR}...")
    api.upload_folder(
        folder_path=str(BACKEND_DIR),
        repo_id=repo_id,
        repo_type="space",
        commit_message="Deploy production FastAPI backend with Python 3.10 compatibility",
        ignore_patterns=[
            "**/__pycache__/**",
            "**/.pytest_cache/**",
            "**/.venv*/**",
            "**/.quality-tools/**",
            "**/.verify-python/**",
            "**/.pytest-tmp*/**",
            "*.pyc",
            "*.log",
        ],
    )
    print(f"\n[+] SUCCESS! All backend files and trained AI models uploaded to:")
    print(f"    https://huggingface.co/spaces/{repo_id}")
    print(f"[+] Live Space URL:")
    print(f"    https://{repo_id.replace('/', '-')}.hf.space")


def main():
    parser = argparse.ArgumentParser(description="Upload backend to Hugging Face Space")
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
        help="Your Hugging Face write access token from https://huggingface.co/settings/tokens",
    )
    args = parser.parse_args()
    clean_sync_space(args.repo, args.token)


if __name__ == "__main__":
    main()