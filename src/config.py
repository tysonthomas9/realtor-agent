import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key with error handling
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please create a .env file with your API key.")

MODEL_ID = "openai/gpt-4" 