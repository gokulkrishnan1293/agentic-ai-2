import json
from src.state import AgentState
from src.model import LLM_MODEL
from src.utils.prompt_loader import load_prompt_from_file
from src.utils.logger import log_info,log_error
from src.utils.business_logger import log_simple_message
from langchain_core.messages import HumanMessage
from src.utils.helpers import *

def run_system_validator(state: AgentState) -> dict:
    """
    This is the node for the System Validator Agent.

    It accepts a handoff containing the initial raw claim data, uses an LLM
    to classify the intent and extract entities, and returns these findings
    to be added to the state.
    """
    request_id = state['request_id']
    log_info("System Validator agent invoked.", extra={"extra_info": {"request_id": request_id}})

    # 1. Accept the handoff from the Supervisor
    log_info(state)
    log_info(state.get("turn_history", [])[-1])
    handoff_payload = state.get("turn_history", [])[-1].get("output",{}).get("handoff", {}).get("payload")
    log_info(f"the data {handoff_payload}")


    # 3. Perform the agent's core logic (call the LLM)
    try:
        # Load the dedicated prompt for this agent
        prompt_template = load_prompt_from_file("analyzer")
        
        # Get a Bedrock LLM configured for JSON output
        # The model factory handles the specifics.
        llm = LLM_MODEL
        
        # Format the prompt with the input from the handoff
        prompt = prompt_template.format(input_data=json.dumps(handoff_payload))
        log_simple_message("--System Validator Agent --", request_id)
        log_info("Invoking LLM for analysis.", extra={"extra_info": {"request_id": request_id}})
        response = llm.invoke(prompt)
        llm_thought_process = clean_json_from_llm(response.content)
        log_info(f"LLM thught process {str(llm_thought_process)}")
        log_simple_message("Analyzing Intent....", request_id)
        log_simple_message(json.loads(llm_thought_process).get("thought",{}), request_id)
        # Safely parse the JSON response from the LLM
        #cleaned_json_string = clean_json_from_llm(llm_thought_process)
        
        # 3. Parse the CLEANED string.
        llm_response_json = json.loads(llm_thought_process)
        intent = llm_response_json.get("output",{}).get("intent", "unknown")
        entities = llm_response_json.get("output",{}).get("entities", {})
        log_simple_message(f"Identified Intent {intent}", request_id)
        log_info(
            f"Analysis complete. Intent classified as '{intent}'.",
            extra={"extra_info": {"request_id": request_id, "intent": intent, "entities": entities}}
        )

    except json.JSONDecodeError as e:
        error_message = f"Failed to parse LLM JSON response. Error: {e}"
        log_error(error_message, extra={"extra_info": {"request_id": request_id, "raw_response": response.content}})
        return {"status": "HALTED_LLM_ERROR"}
    except Exception as e:
        error_message = f"An unexpected error occurred during analysis. Error: {e}"
        log_error(error_message, extra={"extra_info": {"request_id": request_id}})
        return {"status": "HALTED_UNEXPECTED_ERROR"}

    # 4. Return the results as a dictionary.
    # The agent_node_wrapper will capture this dict in the TurnLog's "output".
    # The Supervisor's LLM will see this TurnLog and know what to do next.
    return {
        "status": "ANALYZED",
        "intent": intent,
        "extracted_entities": entities,
        "__agent_thought__":json.loads(llm_thought_process).get("thought",{})
    }