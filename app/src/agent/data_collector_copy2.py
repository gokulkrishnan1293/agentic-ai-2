import json
from src.state import AgentState
from src.model import LLM_MODEL
from src.utils.prompt_loader import load_prompt_from_file
from src.utils.logger import log
from langchain.agents import AgentExecutor
from src.tools.data_collector_tools import data_collector_tools
from langchain.prompts import PromptTemplate
from langgraph.prebuilt import create_react_agent
# --- 1. Create the ReAct Agent and Executor (loaded once) ---
data_collector_react_prompt_template = load_prompt_from_file("data_collector")


data_collector_agent_brain = create_react_agent(
model=LLM_MODEL,
tools=data_collector_tools,
prompt=data_collector_react_prompt_template,
name="Claim Detail Extractor Agent",
)

data_collector_executor = AgentExecutor(
    agent=data_collector_agent_brain,
    tools=data_collector_tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=15 # Allow for a longer loop for multiple scenarios
)

# --- 2. The LangGraph Node Function ---
def run_claims_details_extractor(state: AgentState) -> dict:
    """
    Runs the autonomous Data Collector agent. It iterates through scenarios
    and uses native tools to gather data from mock JSON files.
    """
    request_id = state['request_id']
    log.info("Data Collector agent invoked.", extra={"extra_info": {"request_id": request_id}})
    
    handoff_payload = state.get("turn_history", [])[-1].get("output",{}).get("handoff", {}).get("payload")
    scenarios = handoff_payload.get("sop_scenarios", [])
    # The agent needs the claim_id to use its tools correctly
    claim_id = state.get("request_id") # Assuming request_id is the claim_id
    
    if not scenarios:
        log.warning("Data Collector received no scenarios to process.", extra={"extra_info": {"request_id": request_id}})
        return {"status": "DATA_COLLECTION_SKIPPED"}

    log.info(f"Data Collector starting investigation for {len(scenarios)} scenarios.", extra={"extra_info": {"request_id": request_id}})
    
    try:
        # The input for the ReAct agent needs to be a single string. We format
        # all the context the agent needs into this input.
        input_str = (
            f"Your task is to collect data for the claim with claim_id '{claim_id}'.\n"
            f"You must process this list of scenarios:\n{json.dumps(scenarios, indent=2)}"
        )
        
        # Invoke the agent executor and let it run its full internal loop
        result = data_collector_executor.invoke({
            "input": input_str,
            "chat_history": []
        })
        
        # The final, aggregated data is structured by the agent's 'finish' tool
        final_output_data = result.get("output", {})
        collected_data = final_output_data.get("final_collected_data", {})

        log.info("Data Collector investigation complete.", extra={"extra_info": {"request_id": request_id}})

        # Return the final results for the Decision Agent
        return {
            "status": "DATA_COLLECTED",
            "collected_data": collected_data,
            "__agent_thought__": json.dumps(result.get("intermediate_steps"), default=str)
        }

    except Exception as e:
        error_message = f"Data Collector agent loop failed. Error: {e}"
        log.error(error_message, extra={"extra_info": {"request_id": request_id}})
        return {"status": "HALTED_AGENT_ERROR"}