"""Deterministic contract tests; actual multilingual retrieval is exercised in experiments/run.py."""
import numpy as np
import pytest
from qdrant_client import QdrantClient
from repair_mcp.retrieval import DenseStore


class Tokenizer:
    def encode(self, text, **kwargs):
        return list(text.encode())
    def decode(self, tokens, **kwargs):
        return bytes(tokens).decode(errors="replace")


class Encoder:
    tokenizer = Tokenizer()
    def encode(self, texts, **kwargs):
        return np.array([[1., 0.] if "motor" in t else [0., 1.] for t in texts])


def test_index_filter_source_and_no_duplicates():
    store = DenseStore(client=QdrantClient(":memory:"), encoder=Encoder())
    store.documents = {"repair_cases": [
        {"document_id": "case:1", "text": "motor " * 200, "source_repair_status": "Fixed",
         "source_url": "https://example.org/source/1"},
        {"document_id": "case:2", "text": "filter", "source_repair_status": "End of life"}]}
    with pytest.raises(RuntimeError, match="Index"):
        store.search("repair_cases", "motor")
    result = store.index()
    assert result["counts"]["repair_cases"]["chunks"] > 2
    found = store.search("repair_cases", "motor", repair_status="Fixed")
    assert len(found) == 1 and found[0]["document_id"] == "case:1"
    assert found[0]["source_url"] == "https://example.org/source/1"
    assert store.search("repair_cases", "motor", repair_status="End of life") == []
    store.close()
