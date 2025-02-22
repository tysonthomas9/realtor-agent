from smolagents import Tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever

class RetrieverTool(Tool):
    name = "retriever"
    description = "Uses semantic search to retrieve the parts of transformers documentation that could be most relevant to answer your query."
    inputs = {
        "query": {
            "type": "string",
            "description": "The query to perform. This should be semantically close to your target documents. Use the affirmative form rather than a question.",
        }
    }
    output_type = "string"

    def __init__(self, docs, **kwargs):
        super().__init__(**kwargs)
        self.retriever = BM25Retriever.from_documents(
            docs, k=10
        )

    def forward(self, query: str) -> str:
        assert isinstance(query, str), "Your search query must be a string"

        docs = self.retriever.invoke(
            query,
        )
        return "\nRetrieved documents:\n" + "".join(
            [
                f"\n\n===== Document {str(i)} =====\n" + doc.page_content
                for i, doc in enumerate(docs)
            ]
        )

# Add document loading and processing before creating the retriever_tool
loader = DirectoryLoader(
    '../../../Downloads/reator_agent_docs',
    glob="**/*.pdf",  # Specifically looking for PDF files
    loader_cls=PyPDFLoader,  # Use PyPDFLoader for PDFs
    recursive=True
)
documents = loader.load()

# Add debug print
print(f"Loaded {len(documents)} documents")

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
docs_processed = text_splitter.split_documents(documents)

# Add debug print
print(f"Created {len(docs_processed)} chunks")

# Check if we have documents before creating the retriever
if not docs_processed:
    raise ValueError("No documents were loaded. Please check the path and file pattern.")

retriever_tool = RetrieverTool(docs_processed)