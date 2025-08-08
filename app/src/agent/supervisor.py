import json
from src.utils.helpers import clean_json_from_llm
from src.state import AgentState
from src.utils.logger import log_info
from src.utils.business_logger import log_simple_message
from src.utils.prompt_loader import load_prompt_from_file
from src.model import LLM_MODEL

def run_supervisor(state: AgentState) -> dict: # <-- CRITICAL: Returns a dict
    """
    This is the SUPERVISOR NODE. Its job is to think and update the state
    with its decision and the next handoff package.
    """
    request_id = state['request_id']
    log_info("Agentic Supervisor Node invoked.", extra={"extra_info": {"request_id": request_id}})

    # 1. Use an LLM to decide the next agent to call
    prompt_template = load_prompt_from_file("supervisor")
    turn_history_json = json.dumps(state.get("turn_history", []), indent=2, default=str)
    prompt = prompt_template.format(turn_history_json=turn_history_json)
    
    llm = LLM_MODEL

    response = llm.invoke(prompt)
    llm_thought_process = clean_json_from_llm(response.content)
    log_info(f"response {str(llm_thought_process)}")
    though_process =  json.loads(llm_thought_process).get("thought")
    next_agent = json.loads(llm_thought_process).get("next_agent")
    log_info(f"Supervisor LLM decided next step is: '{next_agent}'", extra={"extra_info": {"request_id": request_id}})
    log_simple_message(though_process, request_id)

    # 2. Prepare the handoff payload for the chosen agent
    handoff_payload = {}
    last_turn = state["turn_history"][-1] if state["turn_history"] else None

    if not last_turn:
        log_simple_message(f"""Based on below Data {state.get("initial_input", {})}""", request_id)
        handoff_payload = state.get("initial_input", {})
    elif last_turn.get("output"):
        handoff_payload = last_turn.get("output", {})
    
    # --- THIS IS THE FIX ---
    # 3. Return a FLAT dictionary where keys match the AgentState.
    #    LangGraph will merge this dictionary into the main state.
    
    state_updates = {
        "status": f"ROUTING_TO_{next_agent.upper()}",
        "handoff": {
            "agent": next_agent,
            "payload": handoff_payload
        },
        "__agent_thought__":though_process
    }

    return state_updates
    

def route_from_supervisor(state: AgentState) -> str: # <-- CRITICAL: Returns a string
    """
    This is the CONDITIONAL EDGE. Its only job is to read the decision
    made by the supervisor node and return a string for routing.
    """
    next_agent = state.get("turn_history", [])[-1].get("output",{}).get("handoff", {}).get("agent", "END")
    log_info(f"Supervisor Edge routing to: '{next_agent}'", extra={"extra_info": {"request_id": state['request_id']}})
    return next_agent


