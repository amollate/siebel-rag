import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
INGESTED_DIR = os.path.join(DATA_DIR, "ingested")
VECTOR_STORE_DIR = os.path.join(PROJECT_ROOT, "vector_store_data")

CHROMA_PERSIST_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 512
CHUNK_OVERLAP = 64
TOP_K_RETRIEVAL = 5

SIMILARITY_THRESHOLD = 0.35

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_CHAT_MODEL = "gpt-4o-mini"

USE_OLLAMA = os.environ.get("USE_OLLAMA", "true").lower() == "true"

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

SIEBEL_SOURCES = [
    {
        "name": "Oracle Siebel Bookshelf",
        "url": "https://docs.oracle.com/en/applications/siebel/index.html",
        "description": "Official Oracle Siebel CRM documentation portal"
    },
    {
        "name": "Siebel CRM Architecture and Infrastructure",
        "url": "https://docs.oracle.com/cd/F14158_13/books/PerformTun/siebel-crm-architecture-and-infrastructure.html",
        "description": "Siebel architecture overview, components, and infrastructure"
    },
    {
        "name": "Siebel CRM Fundamentals Guide",
        "url": "https://www.cleverence.com/articles/oracle-documentation/siebel-crm-fundamentals-guide-4827",
        "description": "Architecture, configuration, and integration guide for Siebel CRM"
    },
    {
        "name": "Siebel CRM Training Tutorial",
        "url": "https://www.acte.in/what-is-siebel-crm-tutorial",
        "description": "Beginner tutorial covering Siebel CRM concepts, modules, and features"
    },
    {
        "name": "Siebel Tutorials Collection",
        "url": "http://www.aired.in/2013/06/siebel-tutorials.html",
        "description": "Collection of Siebel configuration articles and tutorials"
    },
    {
        "name": "Siebel Architecture Overview",
        "url": "https://docs.oracle.com/cd/F26413_09/books/DeplmtPlan/siebel-architecture-overview.html",
        "description": "Oracle Siebel deployment planning and architecture overview"
    },
    {
        "name": "Siebel CRM Online Training",
        "url": "https://www.slideshare.net/slideshow/siebel-crm-online-trainingpdf/251548905",
        "description": "SlideShare presentation covering Siebel CRM training material"
    },
    {
        "name": "Siebel CRM Deployment Guide",
        "url": "https://www.a10networks.com/wp-content/uploads/A10-DG-Oracle_Siebel_CRM.pdf",
        "description": "Oracle Siebel CRM deployment guide with topology and configuration"
    },
]