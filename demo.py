import os
import litellm
from dotenv import load_dotenv
from smolagents import Tool
from rag import retriever_tool

# Load environment variables from .env file
load_dotenv()

# Get API key with error handling
api_key = os.environ.get('GROQ_API_KEY')
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please create a .env file with your API key.")

from smolagents import (
    load_tool,
    CodeAgent,
    VisitWebpageTool,
    GradioUI, LiteLLMModel,
    Tool
)

class HumanInterventionTool(Tool):
    """
    A universal human-in-the-loop tool:
      - scenario="clarification": ask open-ended question.
      - scenario="approval": ask yes/no (type 'YES' or 'NO').
      - scenario="multiple_choice": present list of options.
    """
    name = "human_intervention"
    description = (
        "Single tool for clarifications, approvals, or multiple-choice from the user. "
        "Call with scenario='clarification', 'approval', or 'multiple_choice'."
    )
    inputs = {
        "scenario": {
            "type": "string",
            "description": "One of: 'clarification', 'approval', 'multiple_choice'."
        },
        "message_for_human": {
            "type": "string",
            "description": "Text or question to display to the user."
        },
        "choices": {
            "type": "array",
            "description": "List of options if scenario='multiple_choice'. Otherwise empty or null.",
            "nullable": True
        }
    }
    output_type = "string"

    def forward(self, scenario: str, message_for_human: str, choices: list = None) -> str:
        if scenario not in ("clarification", "approval", "multiple_choice"):
            return "Error: Invalid scenario."

        print("\n[HUMAN INTERVENTION]")
        print(f"Scenario: {scenario}")
        print(f"Agent says: {message_for_human}")

        if scenario == "clarification":
            user_response = input("(Type your clarification): ")
            return user_response

        elif scenario == "approval":
            print("Type 'YES' or 'NO' to proceed:")
            user_decision = input("Your decision: ").strip().upper()
            return user_decision

        elif scenario == "multiple_choice":
            if not choices:
                return "No choices provided."
            print("\nPossible options:")
            for i, option in enumerate(choices, start=1):
                print(f"{i}. {option}")
            user_input = input("\nPick an option number: ")
            return user_input


# Instantiate the tools
human_tool = HumanInterventionTool()

model_id = "openai/gpt-4o"
model = LiteLLMModel(model_id=model_id, api_key=api_key)

# Initialize the agent with the tools
agent = CodeAgent(
    tools=[retriever_tool], 
    model=model, 
    add_base_tools=False
)

GradioUI(agent).launch()

class RealEstateAgent:
    def __init__(self):
        self.document_types = {
            'contract': self.analyze_contract,
            'appraisal': self.analyze_appraisal,
            'inspection': self.analyze_inspection,
            'title': self.analyze_title,
            'mortgage': self.analyze_mortgage
        }
        
    def analyze_document(self, document, doc_type):
        """
        Main method to analyze real estate documents
        """
        if doc_type in self.document_types:
            return self.document_types[doc_type](document)
        else:
            return "Document type not supported"
    
    def analyze_contract(self, document):
        """
        Analyzes purchase agreements and contracts
        - Purchase price
        - Contingencies
        - Important dates
        - Terms and conditions
        """
        # Add contract analysis logic
        pass
    
    def analyze_appraisal(self, document):
        """
        Analyzes property appraisal reports
        - Property value
        - Comparable properties
        - Market analysis
        """
        # Add appraisal analysis logic
        pass
    
    def analyze_inspection(self, document):
        """
        Analyzes home inspection reports
        - Property condition
        - Required repairs
        - Safety issues
        """
        # Add inspection analysis logic
        pass
    
    def analyze_title(self, document):
        """
        Analyzes title documents
        - Ownership history
        - Liens
        - Encumbrances
        """
        # Add title analysis logic
        pass
    
    def analyze_mortgage(self, document):
        """
        Analyzes mortgage documents
        - Interest rates
        - Payment terms
        - Loan conditions
        """
        # Add mortgage analysis logic
        pass
    
    def generate_summary(self, analyses):
        """
        Generates a comprehensive summary of all analyzed documents
        """
        summary = {
            'key_findings': [],
            'risks': [],
            'recommendations': [],
            'important_dates': [],
            'financial_summary': {}
        }
        # Add summary generation logic
        return summary

class TRECDocumentAnalyzer:
    def __init__(self):
        self.document_types = {
            '20_MultiFamilyPSA': self.analyze_multifamily_contract,
            # ... other document types ...
        }
        # Initialize the retriever tool for document search
        self.retriever = retriever_tool
        
    def analyze_document(self, document_path, query=None):
        """
        Main method to analyze TREC documents with search capability
        """
        if query:
            # Use the retriever to search through documents
            search_results = self.retriever.forward(query)
            return search_results
            
        doc_type = self._get_document_type(document_path)
        if doc_type in self.document_types:
            return self.document_types[doc_type](document_path)
        return "Unsupported TREC document type"

class RealEstateExpertTool(Tool):
    name = "real_estate_expert"
    description = """
    Expert tool for analyzing real estate documents and TREC forms. Can:
    - Analyze different types of contracts (Multi-Family, Residential, etc.)
    - Review financing terms and contingencies
    - Examine inspection reports and addendums
    - Search through documents for specific information
    - Provide comprehensive summaries and recommendations
    """
    inputs = {
        "query": {
            "type": "string",
            "description": "The question or request about real estate documents"
        },
        "document_type": {
            "type": "string",
            "description": "Optional: Specific TREC form type to analyze",
            "nullable": True
        }
    }
    output_type = "string"

    def __init__(self):
        super().__init__()
        self.trec_analyzer = TRECDocumentAnalyzer()
        self.real_estate_agent = RealEstateAgent()
        
    def forward(self, query: str, document_type: str = None) -> str:
        # First, search through all documents for relevant information
        search_results = retriever_tool.forward(query)
        
        # If a specific document type is provided, perform detailed analysis
        if document_type:
            if document_type.startswith('20_') or document_type.startswith('21_'):
                analysis = self.real_estate_agent.analyze_document(
                    search_results, 
                    'contract'
                )
            elif document_type.startswith('22'):
                analysis = self.real_estate_agent.analyze_document(
                    search_results, 
                    'financing'
                )
            elif document_type.startswith('35'):
                analysis = self.real_estate_agent.analyze_document(
                    search_results, 
                    'inspection'
                )
            
            # Generate comprehensive response
            response = f"""
Document Analysis Results:

Search Results:
{search_results}

Detailed Analysis:
{analysis}

Summary and Recommendations:
{self.real_estate_agent.generate_summary({'search': search_results, 'analysis': analysis})}
"""
            return response
            
        return search_results

# Initialize the expert tool
real_estate_expert = RealEstateExpertTool()

# Initialize the model
model_id = "openai/gpt-4"
model = LiteLLMModel(model_id=model_id, api_key=api_key)

# Initialize the agent with both tools
agent = CodeAgent(
    tools=[retriever_tool, real_estate_expert], 
    model=model,
    add_base_tools=False
)

# Launch the Gradio interface
GradioUI(agent).launch()