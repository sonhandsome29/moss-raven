from __future__ import annotations

from pathlib import Path

from openai import OpenAI


class OpenAIUploader:
    def __init__(self, api_key: str) -> None:
        self.client = OpenAI(api_key=api_key)

    def ensure_vector_store(self, vector_store_id: str, name: str) -> str:
        if vector_store_id:
            return vector_store_id

        vector_store = self.client.vector_stores.create(name=name)
        return vector_store.id

    def replace_article_chunks(
        self,
        vector_store_id: str,
        chunk_paths: list[Path],
        previous_file_ids: list[str],
    ) -> list[str]:
        before_ids = set(self.list_vector_store_file_ids(vector_store_id))

        for file_id in previous_file_ids:
            self._delete_vector_store_file(vector_store_id, file_id)

        handles = [path.open("rb") for path in chunk_paths]
        try:
            self.client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id,
                files=handles,
            )
        finally:
            for handle in handles:
                handle.close()

        after_ids = set(self.list_vector_store_file_ids(vector_store_id))
        return sorted(after_ids - before_ids)

    def list_vector_store_file_ids(self, vector_store_id: str) -> list[str]:
        ids: list[str] = []
        page = self.client.vector_stores.files.list(vector_store_id=vector_store_id, limit=100)
        ids.extend(item.id for item in page.data)

        while getattr(page, "has_more", False):
            page = self.client.vector_stores.files.list(
                vector_store_id=vector_store_id,
                limit=100,
                after=page.data[-1].id,
            )
            ids.extend(item.id for item in page.data)

        return ids

    def _delete_vector_store_file(self, vector_store_id: str, file_id: str) -> None:
        try:
            self.client.vector_stores.files.delete(vector_store_id=vector_store_id, file_id=file_id)
        finally:
            try:
                self.client.files.delete(file_id)
            except Exception:
                pass
