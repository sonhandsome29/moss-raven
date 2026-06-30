from __future__ import annotations

import json
import logging
from pathlib import Path

from app.chunk import write_chunk_files
from app.config import load_settings
from app.normalize import article_to_markdown
from app.scrape import fetch_articles
from app.state import load_state, save_state
from app.upload_openai import OpenAIUploader


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("optibot-sync")


def run() -> None:
    settings = load_settings()
    _validate_required_settings(settings.openai_api_key)

    state = load_state(settings.state_path)
    uploader = OpenAIUploader(settings.openai_api_key)
    vector_store_id = uploader.ensure_vector_store(
        state.get("openai_vector_store_id") or settings.openai_vector_store_id,
        settings.openai_vector_store_name,
    )
    state["openai_vector_store_id"] = vector_store_id
    save_state(settings.state_path, state)

    articles = fetch_articles(
        base_url=settings.zendesk_base_url,
        locale=settings.zendesk_locale,
        limit=settings.article_limit,
    )

    logger.info("Fetched %s articles from Zendesk.", len(articles))
    url_to_filename = {article.html_url.rstrip("/").lower(): f"{article.slug}.md" for article in articles}

    article_state = state.setdefault("articles", {})
    added = 0
    updated = 0
    skipped = 0
    embedded_chunks = 0

    for article in articles:
        markdown, content_hash = article_to_markdown(article, url_to_filename)
        article_path = settings.articles_dir / f"{article.slug}.md"
        article_path.write_text(markdown, encoding="utf-8")

        prior = article_state.get(str(article.article_id))
        if prior and prior.get("content_hash") == content_hash:
            skipped += 1
            logger.info("Skipped %s", article.slug)
            continue

        chunk_paths = write_chunk_files(
            article=article,
            markdown=markdown,
            output_dir=settings.chunks_dir,
            target_size=settings.target_chunk_size,
            overlap=settings.chunk_overlap,
        )
        file_ids = uploader.replace_article_chunks(
            vector_store_id=vector_store_id,
            chunk_paths=chunk_paths,
            previous_file_ids=prior.get("file_ids", []) if prior else [],
        )

        status = "added" if prior is None else "updated"
        if status == "added":
            added += 1
        else:
            updated += 1
        embedded_chunks += len(chunk_paths)

        article_state[str(article.article_id)] = {
            "slug": article.slug,
            "content_hash": content_hash,
            "updated_at": article.updated_at,
            "file_ids": file_ids,
            "chunk_count": len(chunk_paths),
            "article_path": _portable_path(article_path),
        }
        logger.info("%s %s (%s chunks)", status.title(), article.slug, len(chunk_paths))

    save_state(settings.state_path, state)

    summary = {
        "provider": "openai",
        "vector_store_id": vector_store_id,
        "model_for_testing": settings.openai_model,
        "articles_fetched": len(articles),
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "embedded_files": added + updated,
        "embedded_chunks": embedded_chunks,
    }
    logger.info(json.dumps(summary, indent=2))


def _portable_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def _validate_required_settings(openai_api_key: str) -> None:
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY is required. Copy .env.sample to .env and fill it in.")
