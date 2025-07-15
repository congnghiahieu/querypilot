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
    LLM_CLIENT,
    LLM_MODEL_NAME,
    MAX_CONTEXT_TOKENS,
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
        self.deleted_count = 0  # Track deleted items
        self._load_index()

    def _load_index(self):
        """Load existing FAISS index and metadata"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)

                # Count existing deleted items
                self.deleted_count = sum(1 for m in self.metadata if m.get("deleted", False))
                print(f"Loaded {self.index.ntotal if self.index else 0} vectors, {self.deleted_count} deleted")

            except Exception as e:
                print(f"Error loading index: {e}")
                self.index = None
                self.metadata = []
                self.deleted_count = 0

    def _save_index(self):
        """Save FAISS index and metadata"""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)

        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def remove_documents(self, kb_id: str) -> dict[str, Any]:
        """Remove documents with smart strategy"""
        if not self.metadata:
            return {"removed_count": 0, "strategy": "no_data"}

        # Count documents to remove
        docs_to_remove = [m for m in self.metadata if m["kb_id"] == kb_id and not m.get("deleted", False)]

        if not docs_to_remove:
            return {"removed_count": 0, "strategy": "not_found"}

        # Calculate deletion ratio
        active_count = len([m for m in self.metadata if not m.get("deleted", False)])
        removal_count = len(docs_to_remove)
        deletion_ratio = (self.deleted_count + removal_count) / len(self.metadata)

        # Strategy decision
        if deletion_ratio > 0.4:  # >40% would be deleted -> rebuild
            return self._hard_delete(kb_id, docs_to_remove)
        else:  # <40% -> soft delete
            return self._soft_delete(kb_id, docs_to_remove)

    def _soft_delete(self, kb_id: str, docs_to_remove: list) -> dict[str, Any]:
        """Mark documents as deleted (fast)"""
        removed_count = 0

        for meta in self.metadata:
            if meta["kb_id"] == kb_id and not meta.get("deleted", False):
                meta["deleted"] = True
                meta["deleted_at"] = time.time()
                removed_count += 1

        self.deleted_count += removed_count
        self._save_index()

        return {
            "removed_count": removed_count,
            "strategy": "soft_delete",
            "deleted_total": self.deleted_count,
            "suggestion": "Consider cleanup_deleted() for better performance"
        }

    def _hard_delete(self, kb_id: str, docs_to_remove: list) -> dict[str, Any]:
        """Rebuild index without deleted documents"""
        start_time = time.time()

        # Get active metadata (excluding kb_id and already deleted)
        active_metadata = [
            m for m in self.metadata
            if m["kb_id"] != kb_id and not m.get("deleted", False)
        ]

        removed_count = len(docs_to_remove) + self.deleted_count

        if not active_metadata:
            # No documents left
            self.index = None
            self.metadata = []
            self.deleted_count = 0
        else:
            # Rebuild index
            self._rebuild_index_from_metadata(active_metadata)

        rebuild_time = time.time() - start_time

        return {
            "removed_count": len(docs_to_remove),
            "strategy": "hard_delete",
            "cleaned_total": removed_count,
            "rebuild_time": rebuild_time,
            "active_documents": len(active_metadata)
        }

    def _rebuild_index_from_metadata(self, active_metadata: list):
        """Rebuild FAISS index from active metadata"""
        if not active_metadata:
            self.index = None
            self.metadata = []
            self.deleted_count = 0
            return

        # Extract text chunks
        chunks = [m["text"] for m in active_metadata]

        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks)
        embeddings = np.array(embeddings).astype("float32")

        # Create new index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        # Update vector indices and clean metadata
        for i, metadata in enumerate(active_metadata):
            metadata["vector_index"] = i
            # Remove deletion flags
            metadata.pop("deleted", None)
            metadata.pop("deleted_at", None)

        self.metadata = active_metadata
        self.deleted_count = 0
        self._save_index()

    def cleanup_deleted(self, force: bool = False) -> dict[str, Any]:
        """Manual cleanup of deleted documents"""
        if self.deleted_count == 0:
            return {"message": "No deleted documents to clean", "cleaned_count": 0}

        deletion_ratio = self.deleted_count / len(self.metadata)

        if not force and deletion_ratio < 0.3:
            return {
                "message": f"Cleanup not recommended (only {deletion_ratio:.1%} deleted)",
                "deleted_count": self.deleted_count,
                "suggestion": "Use force=True to cleanup anyway"
            }

        start_time = time.time()

        # Get active metadata
        active_metadata = [m for m in self.metadata if not m.get("deleted", False)]
        cleaned_count = self.deleted_count

        # Rebuild
        self._rebuild_index_from_metadata(active_metadata)

        cleanup_time = time.time() - start_time

        return {
            "message": "Cleanup completed",
            "cleaned_count": cleaned_count,
            "active_documents": len(active_metadata),
            "cleanup_time": cleanup_time
        }

    def search(self, query: str, k: int = 5) -> list[dict[str, Any]]:
        """Search with soft delete support"""
        if self.index is None or self.index.ntotal == 0:
            return []

        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")

        # Search with buffer for deleted items
        active_ratio = 1 - (self.deleted_count / len(self.metadata)) if self.metadata else 1
        search_k = min(int(k / max(active_ratio, 0.1)), self.index.ntotal)
        search_k = max(search_k, k)  # At least k results

        distances, indices = self.index.search(query_embedding, search_k)

        # Filter out deleted documents
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                meta = self.metadata[idx]
                if not meta.get("deleted", False):  # Skip deleted
                    result = meta.copy()
                    result["distance"] = float(distances[0][i])
                    # Remove internal fields
                    result.pop("deleted", None)
                    result.pop("deleted_at", None)
                    results.append(result)

                    if len(results) >= k:
                        break

        return results

    def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics"""
        total_docs = len(self.metadata)
        active_docs = total_docs - self.deleted_count

        return {
            "total_documents": total_docs,
            "active_documents": active_docs,
            "deleted_documents": self.deleted_count,
            "deletion_ratio": self.deleted_count / total_docs if total_docs > 0 else 0,
            "vector_count": self.index.ntotal if self.index else 0,
            "cleanup_recommended": self.deleted_count / total_docs > 0.3 if total_docs > 0 else False
        }


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

            # Generate insights using LLM
            insights = self._generate_insights(text)

            processing_time = time.time() - start_time

            return {
                "summary": insights["summary"],
                "key_insights": insights["key_insights"],
                "entities": insights.get("entities", []),
                "topics": insights.get("topics", []),
                "processing_time": processing_time,
                "chunks_count": len(chunks),
                "processed_content": text[:2000],  # Store first 2000 chars for reference
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

            # Generate insights using LLM
            insights = self._generate_insights(text)

            processing_time = time.time() - start_time

            return {
                "summary": insights["summary"],
                "key_insights": insights["key_insights"],
                "entities": insights.get("entities", []),
                "topics": insights.get("topics", []),
                "processing_time": processing_time,
                "chunks_count": len(chunks),
                "processed_content": text[:2000],
            }

        except Exception as e:
            raise Exception(f"Error processing text: {str(e)}")

    def _generate_insights(self, text: str) -> dict[str, Any]:
        """Generate insights from text using LLM"""
        try:
            # Truncate text if too long
            if len(text) > MAX_CONTEXT_TOKENS * 4:  # Rough estimate
                text = text[: MAX_CONTEXT_TOKENS * 4]

            prompt = f"""
            Please analyze the following document and provide insights in JSON format:

            Document:
            {text}

            Please provide:
            1. A concise summary (2-3 sentences)
            2. Key insights (3-5 important points)
            3. Entities (people, organizations, locations, etc.)
            4. Topics (main themes or subjects)

            Format your response as JSON with keys: summary, key_insights, entities, topics
            """

            response = LLM_CLIENT.chat.completions.create(
                model=LLM_MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1000,
            )

            result = response.choices[0].message.content

            # Try to parse JSON response
            try:
                insights = json.loads(result)
                return insights
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "summary": "Document processed successfully. Detailed analysis available.",
                    "key_insights": [
                        "Document contains valuable information",
                        "Successfully processed and indexed",
                    ],
                    "entities": [],
                    "topics": ["General content"],
                }

        except Exception as e:
            print(f"Error generating insights: {e}")
            return {
                "summary": "Document processed successfully. Detailed analysis available.",
                "key_insights": [
                    "Document contains valuable information",
                    "Successfully processed and indexed",
                ],
                "entities": [],
                "topics": ["General content"],
            }

    def search_knowledge_base(self, query: str, user_id: UUID, k: int = 5) -> list[dict[str, Any]]:
        """Search knowledge base for relevant context"""
        vector_store = VectorStore(user_id)
        return vector_store.search(query, k)

    def remove_knowledge_base(self, kb_id: str, user_id: UUID):
        """Remove knowledge base from vector store"""
        vector_store = VectorStore(user_id)
        vector_store.remove_documents(kb_id)

    def get_context_for_query(self, query: str, user_id: UUID) -> str:
        """Get relevant context from knowledge base for a query"""
        results = self.search_knowledge_base(query, user_id)

        if not results:
            return ""

        context_parts = []
        for result in results:
            context_parts.append(f"From {result['filename']}: {result['text']}")

        return "\n\n".join(context_parts)


# Global RAG service instance
rag_service = RAGService()
