from smolagents import Tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.retrievers import BM25Retriever

class RetrieverTool(Tool):
    name = "retriever"
    description = "Retrieves and searches through real estate forms and documents to find relevant information, Go through the documents and find the most relevant information for the user's query. Provide the document header information and the document file name. Provide the page number of the document where the information is found. "
    inputs = {
        "query": {
            "type": "string",
            "description": "The query to search for in the documents. Be specific about the form or information you need.",
        }
    }
    output_type = "string"

    def __init__(self, docs, **kwargs):
        super().__init__(**kwargs)
        self.docs = docs  # Store original documents for metadata access
        self.retriever = BM25Retriever.from_documents(
            docs, k=5  # Reduced number of results for clearer output
        )

    def forward(self, query: str) -> str:
        assert isinstance(query, str), "Your search query must be a string"

        docs = self.retriever.invoke(query)
        
        # Enhanced output formatting
        output = "\nRelevant Documents Found:\n"
        for i, doc in enumerate(docs, 1):
            # Extract filename from source
            filename = doc.metadata.get('source', '').split('/')[-1]
            output += f"\n=== Document {i}: {filename} ===\n"
            output += f"Page {doc.metadata.get('page', 'N/A')}\n"
            output += f"Content: {doc.page_content.strip()}\n"
        
        return output

# Document loading and processing
loader = DirectoryLoader(
    './reator_agent_docs',
    glob="*.pdf",  # Focus on PDF files
    loader_cls=PyPDFLoader,
    recursive=True
)
documents = loader.load()

print(f"Found {len(documents)} PDF documents")

# Enhanced text splitting for better context
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=["\n\n", "\n", ". ", " ", ""],
    keep_separator=True
)
docs_processed = text_splitter.split_documents(documents)

print(f"Created {len(docs_processed)} searchable chunks")

if not docs_processed:
    raise ValueError("No documents were processed. Please check the path and file pattern.")

retriever_tool = RetrieverTool(docs_processed)