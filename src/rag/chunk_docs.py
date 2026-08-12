"""Split documentation pages into chunks for retrieval."""
import json
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

DOCS = Path("data/docs.json")
OUTPUT = Path("data/chunks.json")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def main():
    docs = json.loads(DOCS.read_text(encoding="utf-8"))
    print(f"Source pages: {len(docs)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks = []
    for doc in docs:
        pieces = splitter.split_text(doc["text"])
        for index, piece in enumerate(pieces):
            chunks.append(
                {
                    "id": f"{doc['url'].rstrip('/').split('/')[-1]}--{index}",
                    "text": piece,
                    "title": doc["title"],
                    "url": doc["url"],
                    "chunk_index": index,
                    "total_chunks": len(pieces),
                }
            )

    OUTPUT.write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    sizes = [len(c["text"]) for c in chunks]
    per_page = [c["total_chunks"] for c in chunks]

    print(f"Chunks:      {len(chunks)}")
    print(f"Avg size:    {sum(sizes) // len(sizes)} chars")
    print(f"Size range:  {min(sizes)} - {max(sizes)}")
    print(f"Max per page: {max(per_page)}")
    print(f"Saved:       {OUTPUT}")

    print("\nSample chunk:")
    sample = chunks[len(chunks) // 2]
    print(f"  id:    {sample['id']}")
    print(f"  title: {sample['title']}")
    print(f"  text:  {sample['text'][:150]}...")


if __name__ == "__main__":
    main()