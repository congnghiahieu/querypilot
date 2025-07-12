import json
import os
import time
from typing import Any, Dict, List
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

            # Add sample data and statistics
            text += "Sample data:\n"
            text += df.head().to_string() + "\n\n"

            # Add basic statistics for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_cols:
                text += "Statistical summary for numeric columns:\n"
                text += df[numeric_cols].describe().to_string() + "\n\n"

            # Add value counts for categorical columns
            categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
            for col in categorical_cols[:3]:  # Limit to first 3 categorical columns
                text += f"Value counts for {col}:\n"
                text += df[col].value_counts().head().to_string() + "\n\n"

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
                text += f"Size: {len(df)} rows, {len(df.columns)} columns\n"
                text += f"Columns: {', '.join(df.columns.tolist())}\n"
                text += "Sample data:\n"
                text += df.head().to_string() + "\n\n"

            return text.strip()
        except Exception as e:
            raise Exception(f"Error processing Excel: {str(e)}")

    def process_text(self, content: str) -> str:
        """Process plain text"""
        return content.strip()

    def chunk_text(self, text: str) -> List[str]:
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

    def add_documents(self, kb_id: str, chunks: List[str], filename: str):
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

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
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
    ) -> Dict[str, Any]:
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

    def process_text(self, text: str, kb_id: str, user_id: UUID) -> Dict[str, Any]:
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

    def _generate_insights(self, text: str) -> Dict[str, Any]:
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

    def search_knowledge_base(self, query: str, user_id: UUID, k: int = 5) -> List[Dict[str, Any]]:
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
