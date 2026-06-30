from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_vector_store_id: str
    openai_vector_store_name: str
    openai_model: str
    zendesk_base_url: str
    zendesk_locale: str
    article_limit: int
    target_chunk_size: int
    chunk_overlap: int
    data_dir: Path
    articles_dir: Path
    chunks_dir: Path
    manifests_dir: Path
    state_path: Path


def load_settings() -> Settings:
    data_dir = Path("data")
    articles_dir = data_dir / "articles"
    chunks_dir = data_dir / "chunks"
    manifests_dir = data_dir / "manifests"

    for path in (articles_dir, chunks_dir, manifests_dir):
        path.mkdir(parents=True, exist_ok=True)

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_vector_store_id=os.getenv("OPENAI_VECTOR_STORE_ID", "").strip(),
        openai_vector_store_name=os.getenv("OPENAI_VECTOR_STORE_NAME", "kb-raven").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        zendesk_base_url=os.getenv("ZENDESK_BASE_URL", "https://support.optisigns.com").rstrip("/"),
        zendesk_locale=os.getenv("ZENDESK_LOCALE", "en-us").strip(),
        article_limit=int(os.getenv("ARTICLE_LIMIT", "30")),
        target_chunk_size=int(os.getenv("TARGET_CHUNK_SIZE", "1800")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
        data_dir=data_dir,
        articles_dir=articles_dir,
        chunks_dir=chunks_dir,
        manifests_dir=manifests_dir,
        state_path=manifests_dir / "state.json",
    )
