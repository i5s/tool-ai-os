from __future__ import annotations

import json
from typing import Optional

from .models import MemoryBlock, MemoryLink, MemoryBlockType, MemoryScope, MemoryLinkRelation
from .repository import SharedMemoryRepository


class SharedMemoryService:
    def __init__(self, cm):
        self.repo = SharedMemoryRepository(cm=cm)

    def create_memory(
        self,
        type: str,
        scope: str,
        title: str,
        content: Optional[str] = None,
        scope_id: Optional[str] = None,
        created_by: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> MemoryBlock:
        block = MemoryBlock(
            type=type,
            scope=scope,
            scope_id=scope_id,
            title=title,
            content=content,
            created_by=created_by,
            metadata=json.dumps(metadata) if metadata else None,
        )
        return self.repo.create_block(block)

    def get_memory(self, block_id: str) -> Optional[MemoryBlock]:
        return self.repo.get_block(block_id)

    def update_memory(self, block_id: str, **fields) -> Optional[MemoryBlock]:
        if "metadata" in fields and isinstance(fields["metadata"], dict):
            fields["metadata"] = json.dumps(fields["metadata"])
        return self.repo.update_block(block_id, **fields)

    def delete_memory(self, block_id: str) -> bool:
        return self.repo.delete_block(block_id)

    def list_memory(
        self,
        block_type: Optional[str] = None,
        scope: Optional[str] = None,
        scope_id: Optional[str] = None,
        created_by: Optional[str] = None,
        title_contains: Optional[str] = None,
        limit: int = 100,
    ) -> list[MemoryBlock]:
        return self.repo.list_blocks(
            block_type=block_type,
            scope=scope,
            scope_id=scope_id,
            created_by=created_by,
            title_contains=title_contains,
            limit=limit,
        )

    def search_memory(self, query: str, limit: int = 50) -> list[MemoryBlock]:
        return self.repo.search_blocks(query, limit=limit)

    def link_memory(
        self,
        source_id: str,
        target_id: str,
        relation: str = MemoryLinkRelation.RELATED_TO.value,
    ) -> MemoryLink:
        link = MemoryLink(
            source_id=source_id,
            target_id=target_id,
            relation=relation,
        )
        return self.repo.create_link(link)
