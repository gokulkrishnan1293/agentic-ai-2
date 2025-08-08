from langgraph.prebuilt import create_react_agent
from src.model import LLM_MODEL
from src.utils.prompt_loader import load_prompt_from_file
from src.state import AgentState
from src.tools.dummy import dummy

fixer_agent = create_react_agent(
model=LLM_MODEL,
tools=[dummy],
prompt=load_prompt_from_file("fixer"),
name="fixer_agent",
)