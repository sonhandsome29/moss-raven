from __future__ import annotations

from pathlib import Path

from app.models import Article


def write_chunk_files(
    article: Article,
    markdown: str,
    output_dir: Path,
    target_size: int,
    overlap: int,
) -> list[Path]:
    sections = _split_sections(markdown)
    chunks = _pack_sections(sections, target_size, overlap)
    paths: list[Path] = []

    for index, chunk in enumerate(chunks, start=1):
        chunk_path = output_dir / f"{article.slug}--{index:03d}.md"
        chunk_text = (
            f"# {article.title}\n\n"
            f"Article URL: {article.html_url}\n"
            f"Chunk: {index}/{len(chunks)}\n\n"
            f"{chunk.strip()}\n"
        )
        chunk_path.write_text(chunk_text, encoding="utf-8")
        paths.append(chunk_path)

    return paths


def _split_sections(markdown: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []

    for line in markdown.splitlines():
        if line.startswith("#") and current:
            sections.append("\n".join(current).strip())
            current = [line]
            continue
        current.append(line)

    if current:
        sections.append("\n".join(current).strip())

    return [section for section in sections if section]


def _pack_sections(sections: list[str], target_size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    current = ""

    for section in sections:
        if len(section) > target_size:
            if current:
                chunks.append(current.strip())
                current = ""
            chunks.extend(_split_large_section(section, target_size, overlap))
            continue

        candidate = f"{current}\n\n{section}".strip() if current else section
        if len(candidate) <= target_size:
            current = candidate
            continue

        chunks.append(current.strip())
        current = section

    if current:
        chunks.append(current.strip())

    return chunks


def _split_large_section(section: str, target_size: int, overlap: int) -> list[str]:
    paragraphs = section.split("\n\n")
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= target_size:
            current = candidate
            continue

        if current:
            chunks.append(current.strip())
            current = current[-overlap:].strip()

        if len(paragraph) <= target_size:
            current = f"{current}\n\n{paragraph}".strip() if current else paragraph
            continue

        start = 0
        while start < len(paragraph):
            end = start + target_size
            piece = paragraph[start:end].strip()
            if piece:
                chunks.append(piece)
            if overlap > 0:
                start = max(start + 1, end - overlap)
            else:
                start = end

    if current:
        chunks.append(current.strip())

    return chunks
