"""HuggingFace dataset fetcher for the Engram benchmark."""

from __future__ import annotations

from pathlib import Path

HF_REPO_ID = "matthewschramm/engram-v3"
HF_FILENAME = "engram-v3.json"


def fetch_engram_dataset() -> Path:
    """Download engram-v3.json from HuggingFace and return the local cache path.

    Requires HF authentication for the private repo — either run `hf auth login`
    or set the HF_TOKEN environment variable.
    """
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as e:
        raise ImportError(
            "huggingface_hub is required to fetch the dataset. "
            "Run: pip install huggingface_hub"
        ) from e

    local_path = hf_hub_download(
        repo_id=HF_REPO_ID,
        filename=HF_FILENAME,
        repo_type="dataset",
    )
    return Path(local_path)
