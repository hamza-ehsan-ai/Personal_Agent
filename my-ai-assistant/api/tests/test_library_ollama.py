from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.library.engine import Answer, Delta, RagError, Turn
from app.library.ollama_engine import OllamaRagEngine, _extract_pages
from app.library.settings import LibrarySettings


class FakeOllama:
    def __init__(self, reply: str = "The warranty lasts two years [1].") -> None:
        self.reply = reply
        self.calls: list[dict] = []

    async def chat(self, **kwargs) -> AsyncIterator[SimpleNamespace]:
        self.calls.append(kwargs)

        async def chunks() -> AsyncIterator[SimpleNamespace]:
            for piece in self.reply.split(" "):
                yield SimpleNamespace(message=SimpleNamespace(content=piece + " "))

        return chunks()


@pytest.mark.asyncio
async def test_persistent_scoped_search_returns_cited_gemma_answer(tmp_path: Path) -> None:
    index_path = tmp_path / "ollama-index.sqlite3"
    model = FakeOllama()
    engine = OllamaRagEngine(
        host="http://localhost:11434", model="gemma4:e4b", index_path=index_path, client=model
    )
    store = await engine.ensure_store("assistant-library")

    handbook = tmp_path / "handbook.md"
    handbook.write_text("Warranty: all devices have a two year warranty.", encoding="utf-8")
    engine_doc = await engine.add_document(
        store,
        handbook,
        title="Handbook",
        mime_type="text/markdown",
        metadata={"scope": "c:policies", "doc": "doc-handbook"},
    )

    other = tmp_path / "other.md"
    other.write_text("The warranty is five years for enterprise devices.", encoding="utf-8")
    await engine.add_document(
        store,
        other,
        title="Private notes",
        mime_type="text/markdown",
        metadata={"scope": "c:private", "doc": "doc-private"},
    )

    restarted = OllamaRagEngine(
        host="http://localhost:11434", model="gemma4:e4b", index_path=index_path, client=model
    )
    assert await restarted.ensure_store("assistant-library") == store
    info = await restarted.store_info(store)
    assert info is not None
    assert info.active == 2

    events = [
        event
        async for event in restarted.stream(
            [Turn("user", "How long is the warranty?")],
            [store],
            'scope="c:policies"',
        )
    ]
    answer = events[-1]
    assert isinstance(answer, Answer)
    assert answer.grounded is True
    assert answer.model == "gemma4:e4b"
    assert answer.sources[0].title == "Handbook"
    assert answer.sources[0].doc_key == "doc-handbook"
    assert answer.sources[0].engine_document_id == engine_doc
    assert "[1]" in answer.cited_text
    assert all(isinstance(event, Delta) for event in events[:-1])
    assert "Private notes" not in str(model.calls[-1]["messages"])


@pytest.mark.asyncio
async def test_missing_or_invalid_scope_is_rejected(tmp_path: Path) -> None:
    engine = OllamaRagEngine(
        host="http://localhost:11434",
        model="gemma4:e4b",
        index_path=tmp_path / "index.sqlite3",
        client=FakeOllama(),
    )
    store = await engine.ensure_store("assistant-library")

    with pytest.raises(RagError, match="scope"):
        _ = [event async for event in engine.stream([Turn("user", "Anything?")], [store], None)]

    with pytest.raises(RagError, match="filter"):
        _ = [
            event
            async for event in engine.stream(
                [Turn("user", "Anything?")], [store], 'scope="x" OR 1=1'
            )
        ]


@pytest.mark.asyncio
async def test_uncited_model_output_is_not_returned_as_grounded(tmp_path: Path) -> None:
    model = FakeOllama("The warranty lasts two years.")
    engine = OllamaRagEngine(
        host="http://localhost:11434",
        model="gemma4:e4b",
        index_path=tmp_path / "index.sqlite3",
        client=model,
    )
    store = await engine.ensure_store("assistant-library")
    source = tmp_path / "source.txt"
    source.write_text("Warranty lasts two years.", encoding="utf-8")
    await engine.add_document(
        store,
        source,
        title="Policy",
        mime_type="text/plain",
        metadata={"scope": "chat:one", "doc": "doc-one"},
    )

    events = [
        event
        async for event in engine.stream(
            [Turn("user", "How long is the warranty?")], [store], 'doc="doc-one"'
        )
    ]
    answer = events[-1]
    assert isinstance(answer, Answer)
    assert answer.grounded is False
    assert answer.sources == []


@pytest.mark.asyncio
async def test_delete_and_purge_remove_indexed_document(tmp_path: Path) -> None:
    engine = OllamaRagEngine(
        host="http://localhost:11434",
        model="gemma4:e4b",
        index_path=tmp_path / "index.sqlite3",
        client=FakeOllama(),
    )
    store = await engine.ensure_store("assistant-library")
    source = tmp_path / "source.md"
    source.write_text("Warranty lasts two years.", encoding="utf-8")
    doc = await engine.add_document(
        store,
        source,
        title="Policy",
        mime_type="text/markdown",
        metadata={"scope": "c:one", "doc": "doc-one"},
    )

    await engine.delete_document(doc)
    assert (await engine.store_info(store)).active == 0

    doc = await engine.add_document(
        store,
        source,
        title="Policy",
        mime_type="text/markdown",
        metadata={"scope": "c:one", "doc": "doc-one"},
    )
    assert await engine.purge(store, "doc-one") == 1
    await engine.delete_document(doc)


def test_default_library_engine_is_local_ollama(tmp_path: Path) -> None:
    settings = LibrarySettings(_env_file=None, library_data_dir=tmp_path)
    assert settings.engine_name == "ollama"
    assert settings.rag_ollama_model == "gemma4:e4b"


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("Employee-Handbook-2026.pdf", "leave"),
        ("Travel-Expense-Policy.docx", "expense"),
        ("Product-FAQ.md", "requests per minute"),
    ],
)
def test_local_parser_extracts_supported_documents(filename: str, expected: str) -> None:
    fixture = Path(__file__).parent / "fixtures" / "library" / filename
    pages = _extract_pages(fixture)
    assert pages
    assert expected in " ".join(text for _, text in pages).lower()
