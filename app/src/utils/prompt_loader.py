import os
from src.config import PROMPTS_DIR

def load_prompt_from_file(prompt_name: str) -> str:
        """
        Loads a prompt template from a markdown file in the prompts directory.
        code
        Code
        Args:
            prompt_name: The name of the prompt file (without the .md extension).

        Returns:
            The content of the prompt file as a string.

        Raises:
            FileNotFoundError: If the prompt file does not exist.
        """
        prompt_path = os.path.join(PROMPTS_DIR, f"{prompt_name}.md")

        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            print(f"ERROR: Prompt file not found at {prompt_path}")
            raise