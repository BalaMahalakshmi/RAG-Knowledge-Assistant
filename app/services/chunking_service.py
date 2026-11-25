from typing import List, Dict

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def create_chunks(
    pages: List[Dict], chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP
):

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("Invalid chunk overlap.")

    chunks = []

    for page in pages:

        page_number = page["page_number"]
        text = page["text"].strip()

        if not text:
            continue

        start = 0
        chunk_index = 1

        while start < len(text):

            end = min(start + chunk_size, len(text))

            # Find a suitable word boundary
            if end < len(text):

                candidates = [
                    pos
                    for pos in (
                        text.rfind(" ", start, end),
                        text.rfind("\n", start, end),
                    )
                    if pos > start + int(chunk_size * 0.7)
                ]

                if candidates:
                    end = max(candidates)

            chunk_text = text[start:end].strip()

            if chunk_text:

                chunks.append(
                    {
                        "chunk_id": (f"page_{page_number}_chunk_{chunk_index}"),
                        "page_number": page_number,
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                        "character_count": len(chunk_text),
                    }
                )

                chunk_index += 1

            if end >= len(text):
                break

            # Calculate overlapping starting position
            next_start = max(start + 1, end - chunk_overlap)

            # Align next chunk to a word boundary
            if next_start > start:

                next_boundary = min(
                    (
                        pos
                        for pos in (
                            text.find(
                                " ", next_start, min(next_start + 100, len(text))
                            ),
                            text.find(
                                "\n", next_start, min(next_start + 100, len(text))
                            ),
                        )
                        if pos != -1
                    ),
                    default=-1,
                )

                if next_boundary != -1:
                    next_start = next_boundary + 1

            start = next_start

    return chunks
