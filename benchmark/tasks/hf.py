"""HuggingFace dataset fetcher for the Engram benchmark."""

from __future__ import annotations

from pathlib import Path

HF_REPO_ID = "matthewschramm/engram-v3"
HF_FILENAME = "engram-v3.json"
HF_TEST_FILENAME = "engram-v3-test.json"


def _hf_download(filename: str) -> Path:
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as e:
        raise ImportError(
            "huggingface_hub is required to fetch the dataset. Run: pip install huggingface_hub"
        ) from e

    local_path = hf_hub_download(
        repo_id=HF_REPO_ID,
        filename=filename,
        repo_type="dataset",
    )
    return Path(local_path)


def fetch_engram_dataset() -> Path:
    """Download the full engram-v3.json dataset from HuggingFace.

    The dataset is public — no authentication required.
    """
    return _hf_download(HF_FILENAME)


def fetch_engram_test_dataset() -> Path:
    """Download the 50-question test split from HuggingFace.

    The dataset is public — no authentication required.
    """
    return _hf_download(HF_TEST_FILENAME)
