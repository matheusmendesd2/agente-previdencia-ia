class TextChunker:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[dict]:
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            remaining = text_len - start
            if remaining <= self.chunk_size:
                chunk_text = text[start:].strip()
                if chunk_text:
                    chunks.append({
                        "text": chunk_text,
                        "start": start,
                        "end": text_len,
                    })
                break

            end = min(start + self.chunk_size, text_len)
            last_space = text.rfind(" ", start, end)
            if last_space > start:
                end = last_space

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "start": start,
                    "end": end,
                })

            start = end - self.chunk_overlap
            if start < 0:
                start = 0

        return chunks
