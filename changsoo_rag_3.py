import os
from PyPDF2 import PdfReader  # pip install PyPDF2
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.retrievers import BM25Retriever
from smolagents import Tool, CodeAgent, LiteLLMModel  # HfApiModel 대신 LiteLLMModel을 임포트합니다.
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read the Groq API key from an environment variable
groq_api_key = os.environ.get("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("Please set the GROQ_API_KEY environment variable.")

# -----------------------------
# 1. PDF 파일 읽어서 Documents 생성
# -----------------------------
pdf_path = os.path.join("pdf", "20_MultiFamilyPSA.pdf")

# PDF 열기
with open(pdf_path, "rb") as f:
    pdf_reader = PdfReader(f)
    pdf_texts = []
    for i, page in enumerate(pdf_reader.pages, start=1):
        text = page.extract_text()
        pdf_texts.append(text if text else "")

# 페이지 단위로 Document 객체 생성
source_docs = [
    Document(
        page_content=pdf_text,
        metadata={"source": f"20_MultiFamilyPSA_Page_{i}"}
    )
    for i, pdf_text in enumerate(pdf_texts, start=1)
]

# -----------------------------
# 2. 텍스트 분할
# -----------------------------
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    add_start_index=True,
    strip_whitespace=True,
    separators=["\n\n", "\n", ".", " ", ""],
)
docs_processed = text_splitter.split_documents(source_docs)

# -----------------------------
# 3. BM25 리트리버 Tool 정의
# -----------------------------
class RetrieverTool(Tool):
    name = "retriever"
    description = (
        "Uses BM25-based search to retrieve relevant chunks from the 20_MultiFamilyPSA.pdf file."
    )
    inputs = {
        "query": {
            "type": "string",
            "description": "The query to perform. Use the affirmative form rather than a question.",
        }
    }
    output_type = "string"

    def __init__(self, docs, **kwargs):
        super().__init__(**kwargs)
        self.retriever = BM25Retriever.from_documents(docs, k=10)

    def forward(self, query: str) -> str:
        assert isinstance(query, str), "Your search query must be a string"
        docs = self.retriever.invoke(query)
        return "\nRetrieved documents:\n" + "".join(
            [
                f"\n\n===== Document {str(i)} =====\n{doc.page_content}"
                for i, doc in enumerate(docs)
            ]
        )

# -----------------------------
# 4. 에이전트 구성 및 실행
# -----------------------------
retriever_tool = RetrieverTool(docs_processed)

# Define the model ID
model_id = "groq/qwen-2.5-coder-32b"

# Create the LiteLLMModel with model_id and API key
model = LiteLLMModel(model_id=model_id, api_key=groq_api_key)

agent = CodeAgent(
    tools=[retriever_tool],
    model=model,
    max_steps=4,
    verbosity_level=2,
)

# 간단한 테스트 질의
query = "What does this PDF say about the Purchase Price?"
agent_output = agent.run(query)

print("Final output:")
print(agent_output)
