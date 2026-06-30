from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Article:
    article_id: int
    title: str
    slug: str
    html_url: str
    updated_at: str
    body_html: str
