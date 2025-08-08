import json
import os
from src.state import AgentState
from src.utils.logger import log_error,log_info
from src.config import BASE_DIR
from src.model import LLM_MODEL
from src.utils.prompt_loader import load_prompt_from_file
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from src.utils.business_logger import log_simple_message
from src.utils.helpers import clean_json_from_llm

# --- The native tool remains the same. Its job is to get the raw data. ---
@tool
def load_scenarios_from_json(intent: str) -> str:
    """
    Loads SOP scenarios from a local JSON file and filters them to find
    all scenarios that exactly match the given intent.
    """
    log_info(f"Tool 'load_scenarios_from_json' invoked for intent: '{intent}'")
    
    # Construct the full path to the JSON file
    sop_file_path = os.path.join(BASE_DIR, "knowledge_base", "sop", "sample.json")
    
    try:
        with open(sop_file_path, 'r', encoding='utf-8') as f:
            all_scenarios = json.load(f)
        
        
        return json.dumps(all_scenarios, indent=2)

    except FileNotFoundError:
        error_msg = f"SOP file not found at path: {sop_file_path}"
        log_error(error_msg)
        return json.dumps([{"error": error_msg}])
    except json.JSONDecodeError:
        error_msg = f"Failed to parse JSON from SOP file: {sop_file_path}"
        log_error(error_msg)
        return json.dumps([{"error": error_msg}])
    except Exception as e:
        error_msg = f"An unexpected error occurred while loading SOPs. Error: {e}"
        log_error(error_msg)
        return json.dumps([{"error": error_msg}])
    
# --- AGENT LOGIC (Now with an LLM step) ---
def run_claim_pend(state: AgentState) -> dict:
    """
    This agent retrieves all relevant SOP scenarios from a JSON file, then uses
    an LLM to format and summarize the results for the next agent.
    """
    request_id = state['request_id']
    log_info("SOP Retriever agent invoked (LLM-Enhanced).", extra={"extra_info": {"request_id": request_id}})

    # 1. Accept the handoff from the Supervisor
    #log_simple_message( state.get("turn_history", [])[-1].get("output",{}).get("handoff", {}).get("payload"),request_id)
    handoff_payload = state.get("turn_history", [])[-1].get("output",{}).get("handoff", {}).get("payload")
    intent = handoff_payload.get("intent")
    

    # 2. Execute the tool to get the raw list of all matching scenarios
    scenarios_json = load_scenarios_from_json.invoke({"intent": intent})
    scenarios = json.loads(scenarios_json)


    log_simple_message("--Claim Pend Agent --", request_id)     
    log_simple_message("--Analyzing Scenarios --", request_id) 
    # --- 3. Use an LLM to format and summarize the raw scenarios ---
    try:
        log_info(f"Invoking LLM to format {len(scenarios)} scenarios.", extra={"extra_info": {"request_id": request_id}})
        prompt_template = load_prompt_from_file("sop_retriever")
        llm = LLM_MODEL
        
        # Pass the raw scenarios from the tool into the prompt
        prompt = prompt_template.format(sop_candidates_json=scenarios_json,intent=intent)
        #log_error(f"prompt is {prompt}")
        response = llm.invoke(prompt)
        llm_thought_process = clean_json_from_llm(response.content)
        #log_error(f"thought is {llm_thought_process}")
        # Parse the new, formatted output from the LLM
        llm_response_json = json.loads(llm_thought_process)
        
        scenarios = llm_response_json.get("output", []).get("relevant_scenarios",[])
        process_summary = llm_response_json.get("thought", "No summary provided.")
        log_simple_message(process_summary, request_id) 
        log_simple_message(scenarios, request_id) 
        log_info("LLM formatting complete.", extra={"extra_info": {"request_id": request_id}})

    except Exception as e:
        log_error(f"SOP Retriever failed during LLM formatting. Error: {e}", extra={"extra_info": {"request_id": request_id}})
        return {"status": "HALTED_LLM_ERROR"}

    # 4. Return the results for the next agent
    return {
        "status": "SCENARIOS_RETRIEVED",
        # The key findings are now the LLM-processed data
        # We still include the raw scenarios for a complete audit trail
        "sop_scenarios": scenarios,
        "__agent_thought__": process_summary
    }