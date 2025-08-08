import json
from src.state import AgentState
from src.model import LLM_MODEL
from src.utils.prompt_loader import load_prompt_from_file
from src.utils.logger import log
from src.utils.business_logger import log_simple_message
from src.utils.helpers import clean_json_from_llm

def run_duplicate_review_agent(state: AgentState) -> dict:
    """
    An LLM-powered agent that adjudicates a duplicate claim review by
    reasoning over a live claim and a list of historical claims.
    """
    request_id = state['request_id']
    agent_name = "DuplicateReviewAgent"
    log.info(f"{agent_name} agent invoked (LLM-powered).", extra={"extra_info": {"request_id": request_id}})
    
    # 1. Accept the handoff from the Supervisor
    handoff_payload = state.get("turn_history", [])[-1].get("output",{}).get("handoff", {}).get("payload")
    collected_data = handoff_payload.get("collected_data", {})
    live_claim = collected_data.get("live_claim")
    history_claims = collected_data.get("history_claims", [])


    # --- THIS IS THE FIX (PART 1) ---
    # Initialize all possible return variables with default error states BEFORE the try block.
    final_decision = "ERROR"
    decision_reasoning = "An unexpected error occurred during adjudication."
    llm_full_response = ""
    # --- END OF FIX (PART 1) ---

    log_simple_message("--Duplicate Review Agent","")

    log_simple_message("--Evaluating Results","")
    # 2. Call the LLM to perform the adjudication
    try:
        prompt_template = load_prompt_from_file("execution_sop")
        llm =LLM_MODEL
        
        prompt = prompt_template.format(
            live_claim_json=json.dumps(live_claim, indent=2),
            history_claims_json=json.dumps(history_claims, indent=2)
        )
        
        log.info("Invoking LLM for duplicate review adjudication.", extra={"extra_info": {"request_id": request_id}})
        response = llm.invoke(prompt)
        
        llm_full_response = clean_json_from_llm(response.content)
        llm_response_json = json.loads(llm_full_response)
        log_simple_message(llm_response_json,"")
        output = llm_response_json.get("output", {})
        # Re-assign the variables with the successful result
        final_decision = output.get("decision", "Error")
        decision_reasoning = output.get("reasoning", "LLM failed to provide reasoning.")
        
        log.info(f"LLM adjudication complete. Final decision: '{final_decision}'", extra={"extra_info": {"request_id": request_id}})

    except Exception as e:
        error_message = f"LLM adjudication failed. Error: {e}"
        log.error(error_message, extra={"extra_info": {"request_id": request_id, "raw_response": llm_full_response}})
        
        # --- THIS IS THE FIX (PART 2) ---
        # The except block should update the reasoning and then return immediately.
        decision_reasoning = f"Agent failed with error: {e}"
        return {
            "status": "HALTED_LLM_ERROR",
            "final_decision": "ERROR",
            "decision_reasoning": decision_reasoning,
            "final_output": {"decision": "ERROR", "reasoning": decision_reasoning},
            "__agent_thought__": llm_full_response
        }
        # --- END OF FIX (PART 2) ---

    # 3. Return the final decision from the successful "try" block execution
    return {
        "status": "DECISION_COMPLETE",
        "final_decision": final_decision,
        "decision_reasoning": decision_reasoning,
        "final_output": {"decision": final_decision, "reasoning": decision_reasoning},
        "__agent_thought__": llm_full_response
    }