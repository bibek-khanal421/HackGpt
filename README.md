# HackGPT - PDF-Based Chat System

HackGPT is an intelligent chat system that allows users to upload PDF documents and have context-aware conversations about their contents. The system uses advanced natural language processing and document understanding to provide accurate and relevant responses.

## Features

- 📄 **PDF Document Processing**
  - Automatic text extraction from PDFs
  - Smart chunking with overlap
  - Efficient embedding generation
  - FAISS-based similarity search

- 💬 **Intelligent Chat Interface**
  - Session-based conversations
  - Context-aware responses
  - Support for multiple PDFs
  - Real-time processing feedback

- 🚀 **Performance Optimizations**
  - Memory-efficient processing
  - Batch processing for large documents
  - Adaptive indexing strategies
  - Low-resource environment support

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/hackgpt.git
cd hackgpt
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the environment:
   - Copy `config-sample.py` to `config.py`
   - Update the configuration with your settings:
     - Database connection details
     - OpenAI API key
     - Azure OpenAI settings (if using)

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Create a new session:
   - Enter an optional session name
   - Click "Create New Session"

3. Upload PDF documents:
   - Use the PDF upload section in the sidebar
   - Wait for processing to complete
   - View uploaded files in the session

4. Start chatting:
   - Type your questions in the chat input
   - The system will use PDF context to provide relevant answers
   - View chat history in the main window

## Configuration

The system can be configured through `config.py`:

```python
# Database Configuration
DB_TYPE = "sqlite"  # or "postgres"
DATABASE_URL = "sqlite:///hackgpt_convo.db"  # or your PostgreSQL URL

# LLM Configuration
LLM_TYPE = "openai"  # or "azure"
OPENAI_API_KEY = "your-api-key"
AZURE_OPENAI_API_KEY = "your-azure-key"
AZURE_OPENAI_ENDPOINT = "your-azure-endpoint"
```

## Technical Details

### PDF Processing
- Uses PyPDF for text extraction
- Implements smart chunking with 500-token chunks and 50-token overlap
- Employs SentenceTransformer for embedding generation
- Utilizes FAISS for efficient similarity search

### Memory Management
- Lightweight models (96MB-118MB)
- Batch processing (32 chunks per batch)
- Efficient storage of embeddings
- Adaptive indexing strategies

### Database Structure
- Session management
- PDF document storage
- Embedding storage
- Chat history

## Example Queries

See [example_outputs.md](example_outputs.md) for sample interactions and responses.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the web interface
- [SentenceTransformers](https://www.sbert.net/) for embeddings
- [FAISS](https://github.com/facebookresearch/faiss) for similarity search
- [PyPDF](https://pypi.org/project/pypdf/) for PDF processing


