from __future__ import annotations

from urllib.parse import urljoin

import requests

from app.models import Article


def fetch_articles(base_url: str, locale: str, limit: int) -> list[Article]:
    session = requests.Session()
    session.headers.update({"User-Agent": "optibot-kb-sync/1.0"})

    url = f"{base_url}/api/v2/help_center/{locale}/articles.json"
    articles: list[Article] = []

    while url and len(articles) < limit:
        response = session.get(url, params={"per_page": 100}, timeout=30)
        response.raise_for_status()
        payload = response.json()

        for item in payload.get("articles", []):
            body_html = item.get("body") or ""
            html_url = item.get("html_url") or ""
            slug = item.get("name") or item.get("title") or f"article-{item['id']}"
            articles.append(
                Article(
                    article_id=item["id"],
                    title=item.get("title") or slug,
                    slug=_slugify(item.get("title") or slug),
                    html_url=html_url,
                    updated_at=item.get("updated_at") or "",
                    body_html=body_html,
                )
            )
            if len(articles) >= limit:
                break

        next_page = payload.get("next_page")
        url = urljoin(base_url, next_page) if next_page else ""

    return articles[:limit]


def _slugify(value: str) -> str:
    normalized = []
    previous_dash = False

    for char in value.lower():
        if char.isalnum():
            normalized.append(char)
            previous_dash = False
            continue
        if not previous_dash:
            normalized.append("-")
            previous_dash = True

    slug = "".join(normalized).strip("-")
    return slug or "untitled-article"
