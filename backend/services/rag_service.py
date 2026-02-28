import chromadb
import hashlib
import re
from chromadb.utils import embedding_functions

# Initialize clients — use ChromaDB's built-in sentence-transformer embeddings
# (all-MiniLM-L6-v2, runs locally, no API key needed)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

CHUNK_SIZE = 3000       # characters (~750 tokens)
CHUNK_OVERLAP = 300     # characters

class RAGService:

    def ingest_document(self, deal_id: int, document_id: int,
                        text: str, filename: str) -> int:
        """
        1. Chunk the text (financial-aware splitting)
        2. Embed each chunk via local sentence-transformer
        3. Store in ChromaDB collection "deal_{deal_id}"
        Returns number of chunks ingested.
        """
        chunks = self._chunk_text(text)
        if not chunks:
            return 0

        collection = chroma_client.get_or_create_collection(
            name=f"deal_{deal_id}",
            metadata={"hnsw:space": "cosine"},
            embedding_function=embedding_fn,
        )

        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{document_id}_{i}_{chunk[:50]}".encode()).hexdigest()
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                "document_id": document_id,
                "filename": filename,
                "chunk_index": i,
            })

        # Upsert — ChromaDB auto-embeds via the collection's embedding_function
        collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        return len(chunks)

    def retrieve(self, deal_id: int, query: str, top_k: int = 5) -> list:
        """
        1. Query ChromaDB (auto-embeds the query)
        2. Return [{chunk_text, filename, relevance_score, chunk_index}]
        """
        try:
            collection = chroma_client.get_collection(
                f"deal_{deal_id}",
                embedding_function=embedding_fn,
            )
        except Exception:
            return []

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        chunks = []
        if results and results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 1.0
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                # Convert to relevance: 1 - (distance / 2)
                relevance = round(1 - (distance / 2), 3)
                chunks.append({
                    "chunk_text": doc,
                    "filename": meta.get("filename", "unknown"),
                    "relevance_score": relevance,
                    "chunk_index": meta.get("chunk_index", 0),
                })

        return chunks

    def delete_deal_collection(self, deal_id: int):
        """Delete the ChromaDB collection for a deal."""
        try:
            chroma_client.delete_collection(f"deal_{deal_id}")
        except Exception:
            pass

    def _chunk_text(self, text: str) -> list:
        """
        Financial-aware chunking:
        1. Split on section headers (lines that look like headers)
        2. For large sections, split on paragraph breaks
        3. For still-large chunks, split on sentences
        4. Apply overlap between adjacent chunks
        """
        if not text or len(text.strip()) == 0:
            return []

        # Step 1: Split on section headers
        header_pattern = r'\n(?=(?:---\s*PAGE|\=\=\=\s*SHEET|[A-Z][A-Z\s]{5,}:?\s*$|#{1,3}\s+))'
        sections = re.split(header_pattern, text)

        # Step 2: Split large sections into chunks
        chunks = []
        for section in sections:
            if len(section) <= CHUNK_SIZE:
                if section.strip():
                    chunks.append(section.strip())
            else:
                # Split on paragraph breaks
                paragraphs = section.split("\n\n")
                current_chunk = ""
                for para in paragraphs:
                    if len(current_chunk) + len(para) <= CHUNK_SIZE:
                        current_chunk += "\n\n" + para if current_chunk else para
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = para
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())

        # Step 3: Add overlap
        overlapped = []
        for i, chunk in enumerate(chunks):
            if i > 0 and len(chunks[i-1]) > CHUNK_OVERLAP:
                overlap = chunks[i-1][-CHUNK_OVERLAP:]
                chunk = overlap + "\n" + chunk
            overlapped.append(chunk)

        return overlapped
