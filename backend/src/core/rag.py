import json
import os
import time
from typing import Any
from uuid import UUID

import faiss
import numpy as np
import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer

from src.core.settings import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    VECTOR_STORE_FOLDER,
)


class DocumentProcessor:
    """Handles different document types processing"""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            length_function=len,
        )

    def process_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")

    def process_csv(self, file_path: str) -> str:
        """Extract text from CSV"""
        try:
            df = pd.read_csv(file_path)
            # Convert DataFrame to descriptive text
            text = f"Dataset with {len(df)} rows and {len(df.columns)} columns.\n"
            text += f"Columns: {', '.join(df.columns.tolist())}\n\n"

            text += "Data:\n"
            text += df.to_string() + "\n\n"

            return text.strip()
        except Exception as e:
            raise Exception(f"Error processing CSV: {str(e)}")

    def process_excel(self, file_path: str) -> str:
        """Extract text from Excel"""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(file_path)
            text = f"Excel file with {len(excel_file.sheet_names)} sheet(s): {', '.join(excel_file.sheet_names)}\n\n"

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                text += f"Sheet: {sheet_name}\n"
                text += "Data:\n"
                text += df.to_string() + "\n\n"

            return text.strip()
        except Exception as e:
            raise Exception(f"Error processing Excel: {str(e)}")

    def process_text(self, content: str) -> str:
        """Process plain text"""
        return content.strip()

    def chunk_text(self, text: str) -> list[str]:
        """Split text into chunks"""
        return self.text_splitter.split_text(text)


class VectorStore:
    """Handles vector storage and retrieval using FAISS"""

    def __init__(self, user_id: UUID):
        self.user_id = user_id
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.vector_store_path = os.path.join(VECTOR_STORE_FOLDER, str(user_id))
        self.index_path = os.path.join(self.vector_store_path, "faiss_index")
        self.metadata_path = os.path.join(self.vector_store_path, "metadata.json")

        os.makedirs(self.vector_store_path, exist_ok=True)

        # Load existing index and metadata
        self.index = None
        self.metadata = []
        self._load_index()

    def _load_index(self):
        """Load existing FAISS index and metadata"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"Error loading index: {e}")
                self.index = None
                self.metadata = []

    def _save_index(self):
        """Save FAISS index and metadata"""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def add_documents(self, kb_id: str, chunks: list[str], filename: str):
        """Add document chunks to vector store"""
        if not chunks:
            return

        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks)
        embeddings = np.array(embeddings).astype("float32")

        # Create or update FAISS index
        if self.index is None:
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)

        # Add embeddings to index
        start_idx = self.index.ntotal
        self.index.add(embeddings)

        # Add metadata
        for i, chunk in enumerate(chunks):
            self.metadata.append(
                {
                    "kb_id": kb_id,
                    "filename": filename,
                    "chunk_index": i,
                    "text": chunk,
                    "vector_index": start_idx + i,
                }
            )

        # Save index
        self._save_index()

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Search for similar documents"""
        if self.index is None or self.index.ntotal == 0:
            return []

        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")

        # Search
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))

        # Return results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result["distance"] = float(distances[0][i])
                results.append(result)

        return results

    def remove_documents(self, kb_id: str):
        """Remove documents from vector store"""
        if not self.metadata:
            return

        # Filter out metadata for the kb_id
        new_metadata = [m for m in self.metadata if m["kb_id"] != kb_id]

        if len(new_metadata) == len(self.metadata):
            return  # No documents to remove

        # Rebuild index if documents were removed
        if new_metadata:
            chunks = [m["text"] for m in new_metadata]
            embeddings = self.embedding_model.encode(chunks)
            embeddings = np.array(embeddings).astype("float32")

            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)

            # Update vector indices
            for i, metadata in enumerate(new_metadata):
                metadata["vector_index"] = i

            self.metadata = new_metadata
        else:
            # No documents left
            self.index = None
            self.metadata = []

        self._save_index()


class RAGService:
    """Main RAG service for document processing and retrieval"""

    def __init__(self):
        self.document_processor = DocumentProcessor()

    def process_document(
        self, file_path: str, file_type: str, kb_id: str, filename: str, user_id: UUID
    ) -> dict[str, Any]:
        """Process document and add to vector store"""
        start_time = time.time()

        try:
            # Extract text based on file type
            if file_type == "pdf":
                text = self.document_processor.process_pdf(file_path)
            elif file_type == "csv":
                text = self.document_processor.process_csv(file_path)
            elif file_type in ["xlsx", "xls"]:
                text = self.document_processor.process_excel(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            # Chunk the text
            chunks = self.document_processor.chunk_text(text)

            # Add to vector store
            vector_store = VectorStore(user_id)
            vector_store.add_documents(kb_id, chunks, filename)

            processing_time = time.time() - start_time

            return {
                "status": "success",
                "message": f"Document '{filename}' processed successfully",
                "processing_time": processing_time,
                "chunks_count": len(chunks),
                "text_length": len(text),
                "processed_content": text[:500] + "..." if len(text) > 500 else text,
                "kb_id": kb_id,
                "filename": filename,
            }

        except Exception as e:
            raise Exception(f"Error processing document: {str(e)}")

    def process_text(self, text: str, kb_id: str, user_id: UUID) -> dict[str, Any]:
        """Process text input and add to vector store"""
        start_time = time.time()

        try:
            # Chunk the text
            chunks = self.document_processor.chunk_text(text)

            # Add to vector store
            vector_store = VectorStore(user_id)
            vector_store.add_documents(kb_id, chunks, "text_input")

            processing_time = time.time() - start_time

            return {
                "status": "success",
                "message": "Text processed successfully",
                "processing_time": processing_time,
                "chunks_count": len(chunks),
                "text_length": len(text),
                "processed_content": text[:500] + "..." if len(text) > 500 else text,
                "kb_id": kb_id,
                "filename": "text_input"
            }

        except Exception as e:
            raise Exception(f"Error processing text: {str(e)}")

    def search_knowledge_base(self, query: str, user_id: UUID, k: int = 5) -> list[dict[str, Any]]:
        """Search knowledge base for relevant context"""
        vector_store = VectorStore(user_id)
        return vector_store.search(query, k)

    def remove_knowledge_base(self, kb_id: str, user_id: UUID):
        """Remove knowledge base from vector store"""
        vector_store = VectorStore(user_id)
        vector_store.remove_documents(kb_id)

    def get_context_for_query(
        self, query: str, user_id: UUID, max_context_length: int = 4000
    ) -> str:
        """Get relevant context from knowledge base for a query"""
        return None

        results = self.search_knowledge_base(query, user_id)

        if not results:
            return ""

        context_parts = []
        current_length = 0

        for result in results:
            context_part = f"From {result['filename']}: {result['text']}"

            # Check if adding this context would exceed limit
            if current_length + len(context_part) > max_context_length:
                # Truncate the last part to fit
                remaining_length = max_context_length - current_length
                if remaining_length > 100:  # Only add if meaningful length
                    context_part = context_part[:remaining_length] + "..."
                    context_parts.append(context_part)
                break

            context_parts.append(context_part)
            current_length += len(context_part) + 2  # +2 for \n\n

        return "\n\n".join(context_parts)

    def get_document_stats(self, user_id: UUID) -> dict[str, Any]:
        """Get statistics about user's documents"""
        vector_store = VectorStore(user_id)

        if not vector_store.metadata:
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "knowledge_bases": {},
                "file_types": {},
            }

        # Count by knowledge base
        kb_stats = {}
        file_type_stats = {}

        for meta in vector_store.metadata:
            kb_id = meta["kb_id"]
            filename = meta["filename"]

            # KB stats
            if kb_id not in kb_stats:
                kb_stats[kb_id] = {"chunks": 0, "files": set()}
            kb_stats[kb_id]["chunks"] += 1
            kb_stats[kb_id]["files"].add(filename)

            # File type stats
            if filename != "text_input":
                file_ext = filename.split(".")[-1].lower() if "." in filename else "unknown"
                file_type_stats[file_ext] = file_type_stats.get(file_ext, 0) + 1

        # Convert sets to counts
        for kb_id in kb_stats:
            kb_stats[kb_id]["files"] = len(kb_stats[kb_id]["files"])

        return {
            "total_documents": len(set(meta["filename"] for meta in vector_store.metadata)),
            "total_chunks": len(vector_store.metadata),
            "knowledge_bases": kb_stats,
            "file_types": file_type_stats,
            "vector_count": vector_store.index.ntotal if vector_store.index else 0,
        }

# Global RAG service instance
rag_service = RAGService()

if __name__ == "__main__":
    # Example usage
    # Process document
    # result = rag_service.process_document("/home/phong/VScode/HackathonVPB/Kiến thức cơ bản.pdf", "pdf", "kb_123", "report.pdf", 200)
    # print(f"Processed {result['chunks_count']} chunks in {result['processing_time']:.2f}s")

    # Get context for query
    # context = rag_service.get_context_for_query("Cổ phiếu là gì", 100)
    # print(f"Context for query: {context[:500]}...")  # Print first 500 characters
    # # Get stats
    # stats = rag_service.get_document_stats(100)
    # print(f"Total documents: {stats['total_documents']}")

    # result = rag_service.process_document("/home/phong/Downloads/knowledgebase_upload_sample.xlsx", "xlsx", "vpbank_ex", "knowledgebase_upload_sample", 200)
    # print(f"Processed {result['chunks_count']} chunks in {result['processing_time']:.2f}s")

    # context = rag_service.get_context_for_query("Tài sản khách hàng", 200)
    # print(f"Context for query: {context}...")  # Print first 500 characters
    rag_service.remove_knowledge_base("kb_123", 200)
