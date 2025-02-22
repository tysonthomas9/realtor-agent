from smolagents import Tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.retrievers import BM25Retriever

class RetrieverTool(Tool):
    name = "retriever"
    description = "Retrieves and searches through real estate forms and documents to find relevant information."
    inputs = {
        "query": {
            "type": "string",
            "description": "The query to search for in the documents.",
        }
    }
    output_type = "string"

    def __init__(self, docs, **kwargs):
        super().__init__(**kwargs)
        self.docs = docs
        self.retriever = BM25Retriever.from_documents(docs, k=5)

    def forward(self, query: str) -> str:
        assert isinstance(query, str), "Query must be a string"
        docs = self.retriever.invoke(query)
        
        output = "\nRelevant Documents Found:\n"
        for i, doc in enumerate(docs, 1):
            filename = doc.metadata.get('source', '').split('/')[-1]
            output += f"\n=== Document {i}: {filename} ===\n"
            output += f"Page {doc.metadata.get('page', 'N/A')}\n"
            output += f"Content: {doc.page_content.strip()}\n"
        
        return output 