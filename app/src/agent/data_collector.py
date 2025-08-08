import json
import os
from ..state import AgentState
from ..utils.logger import log
from ..config import BASE_DIR

# --- Data Loading Logic (remains the same) ---
_live_data = None
_history_data = None
_data_loaded = False

def _load_mock_data_if_needed():
    """Helper to load mock JSONs into memory once per Lambda invocation."""
    global _live_data, _history_data, _data_loaded
    if _data_loaded:
        return
    
    try:
        # Correctly navigate to the knowledge_base/data directory
        project_root = BASE_DIR
        db_path = os.path.join(project_root, "knowledge_base", "data")
        
        with open(os.path.join(db_path, "livedata.json"), 'r') as f:
            _live_data = json.load(f)
        with open(os.path.join(db_path, "history.json"), 'r') as f:
            _history_data = json.load(f)
        _data_loaded = True
        print(f"--- Data Collector: Mock JSON data loaded from {db_path}. ---")
    except Exception as e:
        print(f"--- Data Collector ERROR: Could not load mock data. {e} ---")
        _live_data = [] # Default to empty list
        _history_data = [] # Default to empty list

# --- The Main Agent Node ---
def run_claims_details_extractor(state: AgentState) -> dict:
    """
    A purely procedural agent that fetches all raw data for a given claim_id.
    It retrieves the live claim data and all associated historical claims.
    This agent does NOT use an LLM.
    """
    request_id = state['request_id']
    log.info("Data Collector agent invoked (Procedural).", extra={"extra_info": {"request_id": request_id}})
    
    # 1. Procedural Data Fetching
    _load_mock_data_if_needed()
    log.info(state.get("turn_history", [])[-1].get("output",{}).get("handoff", {}).get("payload"))
    # The Supervisor should hand off the claim_id. We also use the request_id as a fallback.
    handoff_payload = state.get("turn_history", [])[-1].get("output",{}).get("handoff", {}).get("payload")
    claim_id = state.get("initial_input").get("claim_id")
    
    # 2. Find the live claim by iterating through the list
    live_claim_data = next((claim for claim in _live_data if claim.get('Claim ID') == claim_id), {})
    
    #if not live_claim_data:
    #    log.error(f"FATAL: Could not find live claim data for claim_id '{claim_id}'.", extra={"extra_info": {"request_id": request_id}})
    #    return {"status": "HALTED_MISSING_DATA", "collected_data": {"error": f"Live claim data for {claim_id} not found."}}

    # 3. Get the member_id from the live claim
    member_id = live_claim_data.get("Member ID")
    
    # 4. Find all history claims for that member
    history_claims = []
    if member_id:
        history_claims = [
            claim for claim in _history_data 
            if claim.get('Member ID') == member_id
        ]
        log.info(f"Found {len(history_claims)} historical claims for member '{member_id}'.", extra={"extra_info": {"request_id": request_id}})
    else:
        log.warning(f"No member_id found on live claim '{claim_id}'; cannot fetch history.", extra={"extra_info": {"request_id": request_id}})

    # 5. Aggregate all raw data into a single package
    collected_data = {
        "live_claim": live_claim_data,
        "history_claims": history_claims
    }
    
    log.info("Data Collector procedural collection complete.", extra={"extra_info": {"request_id": request_id}})

    # 6. Return the aggregated data
    # The Supervisor will receive this and pass it to the next agent.
    return {
        "status": "DATA_COLLECTED",
        "collected_data": collected_data,
        "__agent_thought__": f"Procedurally fetched the live claim for '{claim_id}' and all {len(history_claims)} historical claims for its member ('{member_id}')."
    }