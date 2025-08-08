import re # Import Python's regular expression module

def clean_json_from_llm(llm_output: str) -> str:
    """
    Strips leading/trailing markdown code blocks and whitespace
    from an LLM's string output to ensure it's valid JSON.
    """
    # 1. Use a regular expression to find the JSON block
    # This pattern looks for content between ```json and ```
    match = re.search(r"```json\s*(\{.*?\})\s*```", llm_output, re.DOTALL)
    
    if match:
        # If a markdown block is found, extract the JSON part
        return match.group(1)
    else:
        # If no markdown block is found, just strip whitespace and hope for the best
        # This handles cases where the LLM might just return the JSON directly.
        return llm_output.strip()