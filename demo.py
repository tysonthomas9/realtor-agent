import os
import litellm
from dotenv import load_dotenv
from smolagents import Tool

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

class CalculatorTool(Tool):
    """
    A simple calculator for demonstration. 
    Supports 'add', 'subtract', 'multiply', or 'divide'.
    """
    name = "calculator"
    description = "Perform basic arithmetic. Provide 'operation' plus numeric 'a' and 'b'."
    inputs = {
        "operation": {
            "type": "string",
            "description": "Which operation to perform: add, subtract, multiply, or divide."
        },
        "a": {
            "type": "number",
            "description": "First operand."
        },
        "b": {
            "type": "number",
            "description": "Second operand."
        }
    }
    output_type = "string"

    def forward(self, operation: str, a: float, b: float) -> str:
        match operation:
            case "add":
                return f"Result: {a + b}"
            case "subtract":
                return f"Result: {a - b}"
            case "multiply":
                return f"Result: {a * b}"
            case "divide":
                if b == 0:
                    return "Error: Division by zero!"
                return f"Result: {a / b}"
            case _:
                return "Error: Invalid operation. Choose from add / subtract / multiply / divide."


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
calculator_tool = CalculatorTool()
human_tool = HumanInterventionTool()

model_id = "groq/qwen-2.5-coder-32b"
model = LiteLLMModel(model_id=model_id, api_key=api_key)

# Initialize the agent with the image generation tool
agent = CodeAgent(tools=[VisitWebpageTool(), calculator_tool, human_tool], model=model, add_base_tools=True)

GradioUI(agent).launch()