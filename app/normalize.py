from __future__ import annotations

import hashlib
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from markdownify import markdownify as to_markdown

from app.models import Article


def article_to_markdown(article: Article, url_to_filename: dict[str, str]) -> tuple[str, str]:
    soup = BeautifulSoup(article.body_html, "html.parser")

    for tag in soup(["script", "style", "nav", "aside"]):
        tag.decompose()

    code_blocks: dict[str, str] = {}
    for index, pre in enumerate(soup.find_all("pre")):
        placeholder = f"OPTIBOT_CODE_BLOCK_{index}"
        code_text = pre.get_text("\n", strip=False).rstrip("\n")
        code_blocks[placeholder] = f"\n```text\n{code_text}\n```\n"
        pre.replace_with(placeholder)

    for anchor in soup.find_all("a", href=True):
        anchor["href"] = _rewrite_href(anchor["href"], article.html_url, url_to_filename)

    markdown = to_markdown(str(soup), heading_style="ATX")
    for placeholder, code_block in code_blocks.items():
        markdown = markdown.replace(placeholder, code_block)

    markdown = _cleanup_markdown(markdown)
    body = markdown.strip()
    full_markdown = (
        f"# {article.title}\n\n"
        f"Article URL: {article.html_url}\n"
        f"Last Updated: {article.updated_at}\n\n"
        f"{body}\n"
    )
    content_hash = hashlib.sha256(full_markdown.encode("utf-8")).hexdigest()
    return full_markdown, content_hash


def _rewrite_href(href: str, current_article_url: str, url_to_filename: dict[str, str]) -> str:
    if href.startswith("#") or href.startswith("mailto:"):
        return href

    parsed = urlparse(href)
    if parsed.scheme and parsed.netloc:
        normalized = _canonicalize_url(href)
        if normalized in url_to_filename:
            return url_to_filename[normalized]
        return href

    if href.startswith("/"):
        normalized = _canonicalize_url(_join_domain(current_article_url, href))
        if normalized in url_to_filename:
            return url_to_filename[normalized]
        return href

    return href


def _join_domain(article_url: str, path: str) -> str:
    parsed = urlparse(article_url)
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def _canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    return base.lower()


def _cleanup_markdown(markdown: str) -> str:
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)
    markdown = re.sub(r"[ \t]+\n", "\n", markdown)
    return markdown.strip()
