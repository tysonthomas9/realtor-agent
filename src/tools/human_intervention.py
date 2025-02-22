from smolagents import Tool

class HumanInterventionTool(Tool):
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
        # ... existing implementation ... 