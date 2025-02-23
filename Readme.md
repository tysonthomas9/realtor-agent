# Realtor Agent

An intelligent real estate agent system powered by AI that helps analyze properties, documents, and assists with real estate transactions and creating purchase sale agreements.

## Features

- Property Analysis from realtor.com
- Real Estate Document Processing (TREC Forms)
- Multi-Agent System Architecture
- Interactive Human-in-the-Loop Tools
- Document Search and Retrieval
- Live Property Data Scraping

## Prerequisites

- Python 3.8+
- Conda package manager
- Required API keys:
  - OPEN_API_KEY
  - ARIZE_SPACE_ID
  - ARIZE_API_KEY

## Installation

1. Create and activate a conda environment:
```bash
conda create --name <env>
conda activate <env>
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export GROQ_API_KEY=<your_groq_api_key> 
```

## Usage

1. Run the demo:
```bash
python demo.py
```

2. Follow the prompts to interact with the real estate agent.

## Project Structure

- `demo.py`: Main script for the real estate agent system.
- `agents/`: Directory for agent components.
- `tools/`: Directory for tool components.
- `utils/`: Utility functions.
- `config.py`: Configuration settings.          

## Available Agents

1. **Realtor Agent**: Analyzes property data and generates detailed reports
2. **Comparable Agent**: Performs market research and property comparisons
3. **Document Agent**: Processes and analyzes real estate documents

## Supported Document Types

- Multi-Family Purchase Agreements
- Residential Contracts
- Financing Documents
- Inspection Reports
- Title Documents
- And more...

## Support

For support, please open an issue in the repository or contact the maintainers.
