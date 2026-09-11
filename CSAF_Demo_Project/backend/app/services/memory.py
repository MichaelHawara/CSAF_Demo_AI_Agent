"""Student extension: persistent memory for RAG poisoning demos.

An in-memory map is enough for the foundation to import. Students replace
this with ownership, trust levels, expiration, and retrieval filtering.
"""

from __future__ import annotations

from typing import Protocol


class MemoryStore(Protocol):
    def store(
        self,
        agent_id: str,
        owner_customer_id: str,
        content: str,
        source: str,
        trust_level: str,
    ) -> str: ...

    def search(self, agent_id: str, query: str) -> list[dict]: ...


class InMemoryMemoryStore:
    """Empty-by-default store used until students implement persistence."""

    def __init__(self) -> None:
        self._rows: list[dict] = []

    def store(
        self,
        agent_id: str,
        owner_customer_id: str,
        content: str,
        source: str,
        trust_level: str,
    ) -> str:
        # TODO(STUDENT): Persist MemoryRecord rows, stamp trust/ownership, and
        # support expiration. Do not treat seller text as trusted memory.
        return "not_implemented"

    def search(self, agent_id: str, query: str) -> list[dict]:
        # TODO(STUDENT): Retrieve only in-scope, non-expired, policy-allowed
        # records. Filter untrusted seller content in patched mode.
        return []


memory_store = InMemoryMemoryStore()
