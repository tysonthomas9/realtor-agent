import os
from dotenv import load_dotenv
from smolagents import Tool

# Add import for scrape_properties
from LiveData import scrape_properties

# Load environment variables from .env file
load_dotenv()

# Get API key with error handling
api_key = os.environ.get('GROQ_API_KEY')
if not api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please create a .env file with your API key.")

arize_space_id = os.environ.get('ARIZE_SPACE_ID')
if not arize_space_id:
    raise ValueError("ARIZE_SPACE_ID environment variable is not set. Please create a .env file with your space ID.")

arize_api_key = os.environ.get('ARIZE_API_KEY')
if not arize_api_key:
    raise ValueError("ARIZE_API_KEY environment variable is not set. Please create a .env file with your API key.")

from arize.otel import register

tracer_provider = register(
    space_id = arize_space_id,
    api_key = arize_api_key,
    project_name = "Realtor Agent", 
)

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

SmolagentsInstrumentor().instrument(tracer_provider=tracer_provider)

import litellm

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


class LoadRealtorDataTool(Tool):
    """
    Loads realtor data from the URL provided.
    """
    name = "load_realtor_data"
    description = "Loads realtor data from website."
    inputs = {
        "url": {
            "type": "string",
            "description": "The URL of the realtor data to load."
        }
    }
    output_type = "string"

    def forward(self, url: str) -> str:
        return scrape_properties([url])

# Instantiate the tools
human_tool = HumanInterventionTool()
load_realtor_data_tool = LoadRealtorDataTool()

model_id = "groq/qwen-2.5-coder-32b"
model = LiteLLMModel(model_id=model_id, api_key=api_key)

realtor_agent = CodeAgent(
    tools=[load_realtor_data_tool],
    additional_authorized_imports=["time", "numpy", "bs4", "requests", "asyncio", "parsel", "httpx", "markdownify", "re"],
    model=model,
    add_base_tools=False,
    name="realtor_agent",
    description="""Analyzes property data in detail following these steps:
    1. Load the property data or find it on the web from realtor.com
    2. Analyze basic property features and price
    3. Calculate key metrics (price per sqft, estimated ROI)
    4. Compare with similar properties
    5. Assess investment potential
    6. Generate detailed property report
    Always explain calculations and reasoning.""",
)

comparable_agent = CodeAgent(
    tools=[VisitWebpageTool(), human_tool],
    model=model,
    add_base_tools=True,
    name="comparable_agent",
    description="""Performs detailed web research for real estate information. Follow these steps:
    1. Find similar properties in the area using the web tool or search the web for similar properties
    2. Gather information about the neighborhood and amenities
    3. Look for historical price trends in the area
    4. Research local schools and transportation
    5. Check for any recent news about the area
    6. Use the realtor_agent to analyze the properties
    Provide detailed summaries after each search with links to the sources. Never make up information or make assumptions. Alwayse search for realtor.com links.""",
)

manager_agent = CodeAgent(
    tools=[human_tool],
    model=model,
    managed_agents=[realtor_agent, comparable_agent],
)

GradioUI(manager_agent).launch()