from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.models import DocumentEntitiesResponse
from app.sources.document_entities import HKEXDocumentEntitiesSource
from app.storage.document_entities import DocumentEntityRepository
from app.storage.history import NormalizedSnapshotRepository


class DocumentEntitiesService:
    def __init__(self, source=None, repository=None):
        self.source = source or HKEXDocumentEntitiesSource()
        self.repository = repository

    async def get_entities(self, code: str | int) -> DocumentEntitiesResponse:
        response = await self.source.get_entities(code)
        if self.repository is not None and response.rows:
            self.repository.save(response)
        return response


@lru_cache
def get_document_entities_service() -> DocumentEntitiesService:
    settings = get_settings()
    return DocumentEntitiesService(HKEXDocumentEntitiesSource(), DocumentEntityRepository(NormalizedSnapshotRepository(settings.ccass_sqlite_path)))
