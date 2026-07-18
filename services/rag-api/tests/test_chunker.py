from app.chunker import TextChunker


def test_single_chunk():
    c = TextChunker(chunk_size=1000, chunk_overlap=50)
    text = "Hello world"
    chunks = c.chunk(text)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Hello world"


def test_multi_chunk():
    c = TextChunker(chunk_size=20, chunk_overlap=0)
    text = "a" * 100
    chunks = c.chunk(text)
    assert len(chunks) == 5


def test_empty_text():
    c = TextChunker()
    assert c.chunk("") == []


def test_overlap_smaller_than_chunk():
    c = TextChunker(chunk_size=10, chunk_overlap=5)
    text = "HelloWorldThisIsATest"
    chunks = c.chunk(text)
    assert len(chunks) >= 2
    for ch in chunks:
        assert len(ch["text"]) <= 10


def test_raises_on_bad_overlap():
    import pytest
    with pytest.raises(ValueError):
        TextChunker(chunk_size=10, chunk_overlap=10)


def test_word_boundary():
    c = TextChunker(chunk_size=15, chunk_overlap=0)
    text = "hello world foo bar"
    chunks = c.chunk(text)
    assert all(ch["text"] for ch in chunks)
