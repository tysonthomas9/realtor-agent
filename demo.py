import os
import litellm

api_key = os.environ.get('GROQ_API_KEY')

from smolagents import (
    load_tool,
    CodeAgent,
    VisitWebpageTool,
    GradioUI, LiteLLMModel
)

model_id = "groq/llama3-8b-8192"
model = LiteLLMModel(model_id=model_id, api_key=api_key)

# Initialize the agent with the image generation tool
agent = CodeAgent(tools=[VisitWebpageTool()], model=model, add_base_tools=True)

GradioUI(agent).launch()