from typing import List, Optional
import os
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from sqlalchemy import Column, Integer, String, LargeBinary, ForeignKey
from sqlalchemy.orm import relationship
from source.chat_session import Base
import tiktoken

class PDFDocument(Base):
    __tablename__ = "hackgpt_pdf_documents"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("hackgpt_chat_sessions.session_name"))
    filename = Column(String)
    embeddings = Column(LargeBinary)  # Store FAISS index as binary
    chunks = Column(LargeBinary)  # Store text chunks as binary
    session = relationship("ChatSession", back_populates="pdf_documents")

class PDFProcessor:
    def __init__(self, model_name: str = "paraphrase-MiniLM-L3-v2"):
        """
        Initialize with a smaller model optimized for low-resource environments.
        Options:
        - paraphrase-MiniLM-L3-v2 (96MB, 384 dimensions)
        - all-MiniLM-L3-v2 (96MB, 384 dimensions)
        - paraphrase-MiniLM-L6-v2 (118MB, 384 dimensions)
        """
        self.model = SentenceTransformer(model_name)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4 tokenizer
        self.target_tokens = 500  # Target tokens per chunk
        self.chunk_overlap = 50  # Token overlap between chunks
        self.batch_size = 32  # Process chunks in batches to manage memory

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text."""
        return len(self.tokenizer.encode(text))

    def extract_text_from_pdf(self, pdf_file) -> str:
        """Extract text from PDF file."""
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def create_chunks(self, text: str) -> List[str]:
        """Split text into chunks based on token count."""
        chunks = []
        tokens = self.tokenizer.encode(text)
        start_idx = 0
        
        while start_idx < len(tokens):
            # Get chunk of target size
            end_idx = min(start_idx + self.target_tokens, len(tokens))
            chunk_tokens = tokens[start_idx:end_idx]
            
            # Decode tokens back to text
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
            
            # Move start index, accounting for overlap
            start_idx = end_idx - self.chunk_overlap
            
            # If we're at the end, break
            if end_idx == len(tokens):
                break
        
        return chunks

    def create_embeddings(self, chunks: List[str]) -> tuple:
        """Create embeddings for text chunks and build FAISS index."""
        # Process chunks in batches to manage memory
        all_embeddings = []
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            all_embeddings.extend(batch_embeddings)
        
        embeddings = np.array(all_embeddings)
        dimension = embeddings.shape[1]
        
        # Create FAISS index with L2 normalization for better performance
        quantizer = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIVFPQ(quantizer, dimension, 50, 8, 8) 
        if not index.is_trained:
            index.train(embeddings)
        # Normalize embeddings for better similarity search
        faiss.normalize_L2(embeddings)
        index.add(embeddings.astype('float32'))
        
        return index, chunks

    def process_pdf(self, pdf_file) -> tuple:
        """Process PDF file and return embeddings and chunks."""
        text = self.extract_text_from_pdf(pdf_file)
        chunks = self.create_chunks(text)
        index, chunks = self.create_embeddings(chunks)
        return index, chunks

    def search_similar_chunks(self, query: str, index: faiss.Index, chunks: List[str], k: int = 3) -> List[str]:
        """Search for similar chunks using FAISS index."""
        query_embedding = self.model.encode([query], show_progress_bar=False)
        # Normalize query embedding
        faiss.normalize_L2(query_embedding)
        distances, indices = index.search(query_embedding.astype('float32'), k)
        return [chunks[i] for i in indices[0]] 